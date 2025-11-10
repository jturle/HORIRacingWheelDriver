#include <DriverKit/IOLib.h>
#include <DriverKit/IOBufferMemoryDescriptor.h>
#include <DriverKit/OSCollections.h>
#include <USBDriverKit/IOUSBHostDevice.h>
#include <USBDriverKit/IOUSBHostInterface.h>
#include <USBDriverKit/AppleUSBDefinitions.h>
#include <HIDDriverKit/HIDDriverKit.h>

#include "HORIRacingWheelDriver.h"

#define LOG_PREFIX "HORIRacingWheelDriver: "

// Helper macros for logging in DriverKit 25.1+
// Use IOLog instead of os_log which may not be available
#define LOG_ERROR(fmt, ...) IOLog(LOG_PREFIX fmt "\n", ##__VA_ARGS__)
#define LOG_INFO(fmt, ...) IOLog(LOG_PREFIX fmt "\n", ##__VA_ARGS__)

struct HORIRacingWheelDriver_IVars
{
    IOUSBHostInterface *interface;
    IOUSBHostPipe *inPipe;
    OSAction *completionAction;
    IOBufferMemoryDescriptor *reportBuffer;
};

bool HORIRacingWheelDriver::init()
{
    bool result = false;

    result = super::init();
    if (!result) {
        LOG_ERROR("super::init failed");
        return false;
    }

    ivars = IONewZero(HORIRacingWheelDriver_IVars, 1);
    if (!ivars) {
        LOG_ERROR("Failed to allocate ivars");
        return false;
    }

    LOG_INFO("init successful");
    return true;
}

kern_return_t HORIRacingWheelDriver::Start_Impl(IOService *provider)
{
    kern_return_t ret;
    IOUSBHostDevice *device = nullptr;

    LOG_INFO("Start called");

    ret = super::Start(provider);
    if (ret != kIOReturnSuccess) {
        LOG_ERROR("super::Start failed: 0x%x", ret);
        return ret;
    }

    // Cast provider to USB device
    device = OSDynamicCast(IOUSBHostDevice, provider);
    if (!device) {
        LOG_ERROR("Provider is not an IOUSBHostDevice");
        Stop(provider);
        return kIOReturnError;
    }

    // Open the device (DriverKit 25.1 API: third parameter is uintptr_t, use 0)
    ret = device->Open(this, 0, 0);
    if (ret != kIOReturnSuccess) {
        LOG_ERROR("Failed to open device: 0x%x", ret);
        Stop(provider);
        return ret;
    }

    // Copy interface (DriverKit 25.1 API: now requires output parameter)
    ret = device->CopyInterface(0, &ivars->interface);
    if (ret != kIOReturnSuccess || !ivars->interface) {
        LOG_ERROR("Failed to copy interface: 0x%x", ret);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Open the interface (third parameter is uintptr_t)
    ret = ivars->interface->Open(this, 0, 0);
    if (ret != kIOReturnSuccess) {
        LOG_ERROR("Failed to open interface: 0x%x", ret);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return ret;
    }

    // In DriverKit 25.1, we try standard HID interrupt IN endpoint address
    // HID devices typically use endpoint 0x81 (IN, endpoint 1)
    // Let's try to open it directly
    uint8_t hidEndpointAddress = 0x81;  // Interrupt IN, endpoint 1

    ret = ivars->interface->CopyPipe(hidEndpointAddress, &ivars->inPipe);
    if (ret != kIOReturnSuccess || !ivars->inPipe) {
        // If that doesn't work, try endpoint 2
        hidEndpointAddress = 0x82;
        ret = ivars->interface->CopyPipe(hidEndpointAddress, &ivars->inPipe);
    }

    if (ret == kIOReturnSuccess && ivars->inPipe) {
        LOG_INFO("Found interrupt IN pipe at address 0x%02x", hidEndpointAddress);
    }

    if (!ivars->inPipe) {
        LOG_ERROR("Failed to find interrupt IN endpoint");
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Allocate report buffer
    ret = IOBufferMemoryDescriptor::Create(kIOMemoryDirectionIn, 64, 0, &ivars->reportBuffer);
    if (ret != kIOReturnSuccess || !ivars->reportBuffer) {
        LOG_ERROR("Failed to allocate report buffer: 0x%x", ret);
        OSSafeReleaseNULL(ivars->inPipe);
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Create completion action for async reads
    ret = CreateActionReadComplete(sizeof(void*), &ivars->completionAction);
    if (ret != kIOReturnSuccess) {
        LOG_ERROR("Failed to create completion action: 0x%x", ret);
        OSSafeReleaseNULL(ivars->reportBuffer);
        OSSafeReleaseNULL(ivars->inPipe);
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Start reading from the device
    ret = ivars->inPipe->AsyncIO(ivars->reportBuffer, 64, ivars->completionAction, 0);
    if (ret != kIOReturnSuccess) {
        LOG_ERROR("Failed to start async IO: 0x%x", ret);
        OSSafeReleaseNULL(ivars->completionAction);
        OSSafeReleaseNULL(ivars->reportBuffer);
        OSSafeReleaseNULL(ivars->inPipe);
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    LOG_INFO("Successfully started");

    ret = RegisterService();

    return ret;
}

kern_return_t HORIRacingWheelDriver::Stop_Impl(IOService *provider)
{
    LOG_INFO("Stop called");

    if (ivars->inPipe) {
        ivars->inPipe->Abort(0, kIOReturnAborted, this);
        OSSafeReleaseNULL(ivars->inPipe);
    }

    if (ivars->completionAction) {
        ivars->completionAction->release();
        ivars->completionAction = nullptr;
    }

    if (ivars->reportBuffer) {
        OSSafeReleaseNULL(ivars->reportBuffer);
    }

    if (ivars->interface) {
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
    }

    IOUSBHostDevice *device = OSDynamicCast(IOUSBHostDevice, provider);
    if (device) {
        device->Close(this, 0);
    }

    return super::Stop(provider);
}

void HORIRacingWheelDriver::free()
{
    LOG_INFO("free called");

    if (ivars) {
        IOSafeDeleteNULL(ivars, HORIRacingWheelDriver_IVars, 1);
    }

    super::free();
}

void HORIRacingWheelDriver::ReadComplete_Impl(OSAction *action, IOReturn status, uint32_t actualByteCount, uint64_t completionTimestamp)
{
    kern_return_t ret;

    if (status != kIOReturnSuccess) {
        LOG_ERROR("Read completed with error: 0x%x", status);
        return;
    }

    if (actualByteCount > 0) {
        uint8_t *reportData = nullptr;
        uint64_t reportLength = 0;

        ret = ivars->reportBuffer->Map(0, 0, 0, 0, (uint64_t*)&reportData, &reportLength);
        if (ret == kIOReturnSuccess && reportData) {
            // Handle the report
            HandleInputReport(completionTimestamp, reportData, actualByteCount);

            // Dispatch the report to the HID system
            handleReport(completionTimestamp, reportData, actualByteCount, kIOHIDReportTypeInput, 0);
        }
    }

    // Queue next read
    ret = ivars->inPipe->AsyncIO(ivars->reportBuffer, 64, ivars->completionAction, 0);
    if (ret != kIOReturnSuccess) {
        LOG_ERROR("Failed to queue next read: 0x%x", ret);
    }
}

void HORIRacingWheelDriver::HandleInputReport(uint64_t timestamp, uint8_t *report, uint32_t reportLength)
{
    // Log raw report for debugging
    if (reportLength >= 8) {
        LOG_INFO("Report [%d bytes]: %02x %02x %02x %02x %02x %02x %02x %02x",
               reportLength,
               report[0], report[1], report[2], report[3],
               report[4], report[5], report[6], report[7]);
    }

    ParseWheelData(report, reportLength);
}

void HORIRacingWheelDriver::ParseWheelData(uint8_t *report, uint32_t reportLength)
{
    // HORI Racing Wheel ACTUAL Report Structure (discovered via interactive mapping):
    //
    // Byte 0-1: Buttons (location TBD - not yet mapped)
    // Byte 2:   D-pad + Shoulder Buttons + Plus/Minus (ALL 8 BITS!)
    //           Bit 0 (0x01): D-pad Up
    //           Bit 1 (0x02): D-pad Down
    //           Bit 2 (0x04): D-pad Left
    //           Bit 3 (0x08): D-pad Right
    //           Bit 4 (0x10): Plus/+ button
    //           Bit 5 (0x20): Minus/- button
    //           Bit 6 (0x40): LSB (Left Shoulder Button)
    //           Bit 7 (0x80): RSB (Right Shoulder Button)
    // Byte 3:   Paddle Shifters + Face Buttons (bits)
    //           Bit 0 (0x01): Gear Down (left paddle)
    //           Bit 1 (0x02): Gear Up (right paddle)
    //           Bit 2 (0x04): Home button
    //           Bit 3 (0x08): (unknown)
    //           Bit 4 (0x10): A button
    //           Bit 5 (0x20): B button
    //           Bit 6 (0x40): X button
    //           Bit 7 (0x80): Y button
    // Byte 4:   Brake (Z axis: 0x00=not pressed, 0xFF=full brake)
    //           ALSO: ZL button (digital, 0xFF when pressed)
    // Byte 5:   Accelerator (Y axis: 0x00=not pressed, 0xFF=full throttle)
    //           ALSO: ZR button (digital, 0xFF when pressed)
    //           Note: Also changes 0-86 when brake is pressed (cross-talk)
    // Byte 6-7: Steering wheel (X axis: 16-BIT! Little-endian, signed-style)
    //           0x0000 = CENTER/NEUTRAL (straight ahead)
    //           0x0001 to 0x7FFF = Turn RIGHT (1 to 32767)
    //           0x8000 to 0xFFFF = Turn LEFT (32768 to 65535, or -32768 to -1 if interpreted as signed)
    // Byte 8+:  Vendor-specific data

    if (reportLength < 8) {
        LOG_ERROR("Report too short: %d bytes", reportLength);
        return;
    }

    // Extract button state (TODO: map buttons to find actual positions)
    uint16_t buttons = report[0] | ((report[1] & 0xFF) << 8);  // Guess: bytes 0-1

    // Extract D-pad (individual bits, not hat switch encoding)
    uint8_t dpad_bits = report[2] & 0x0F;
    // Convert individual bits to hat switch encoding for compatibility
    // 0x01=Up, 0x02=Down, 0x04=Left, 0x08=Right
    uint8_t dpad = 8;  // Default: centered
    if (dpad_bits == 0x01) dpad = 0;      // Up
    else if (dpad_bits == 0x09) dpad = 1; // NE (Up+Right)
    else if (dpad_bits == 0x08) dpad = 2; // Right
    else if (dpad_bits == 0x0A) dpad = 3; // SE (Down+Right)
    else if (dpad_bits == 0x02) dpad = 4; // Down
    else if (dpad_bits == 0x06) dpad = 5; // SW (Down+Left)
    else if (dpad_bits == 0x04) dpad = 6; // Left
    else if (dpad_bits == 0x05) dpad = 7; // NW (Up+Left)

    // Extract shoulder buttons and plus/minus from byte 2 (upper 4 bits)
    bool btn_plus = (report[2] & 0x10) != 0;   // Bit 4: + button
    bool btn_minus = (report[2] & 0x20) != 0;  // Bit 5: - button
    bool btn_lsb = (report[2] & 0x40) != 0;    // Bit 6: LSB (Left Shoulder Button)
    bool btn_rsb = (report[2] & 0x80) != 0;    // Bit 7: RSB (Right Shoulder Button)

    // Extract axes (CORRECTED POSITIONS!)
    uint8_t brake = report[4];     // Byte 4: Brake
    uint8_t accel = report[5];     // Byte 5: Accelerator

    // Extract 16-bit steering (bytes 6-7, little-endian)
    // 0x0000 = center, 0x0001-0x7FFF = right, 0x8000-0xFFFF = left
    uint16_t steering16 = report[6] | ((uint16_t)report[7] << 8);
    int16_t steering_signed = (int16_t)steering16;  // Can also interpret as signed: -32768 to +32767

    // Extract paddle shifters and face buttons (byte 3)
    bool paddle_gear_down = (report[3] & 0x01) != 0;  // Bit 0: left paddle
    bool paddle_gear_up = (report[3] & 0x02) != 0;    // Bit 1: right paddle
    bool btn_home = (report[3] & 0x04) != 0;          // Bit 2: home button
    // Bit 3 (0x08): unknown
    bool btn_a = (report[3] & 0x10) != 0;             // Bit 4: A button
    bool btn_b = (report[3] & 0x20) != 0;             // Bit 5: B button
    bool btn_x = (report[3] & 0x40) != 0;             // Bit 6: X button
    bool btn_y = (report[3] & 0x80) != 0;             // Bit 7: Y button

    // Detect ZL and ZR buttons (they overlay on the analog pedal axes)
    // ZL: Brake jumps to 0xFF when pressed
    // ZR: Accelerator jumps to 0xFF when pressed
    // Note: This means we can't detect these buttons when pedals are fully pressed
    bool btn_zl = (brake == 0xFF);
    bool btn_zr = (accel == 0xFF);

    // Log parsed values (can be disabled in production)
    static uint32_t logCounter = 0;
    if ((logCounter++ % 100) == 0) {  // Log every 100th report to reduce spam
        os_log(OS_LOG_DEFAULT, LOG_PREFIX
               "Wheel: 0x%04x (%d), Accel: %02x, Brake: %02x | "
               "Byte2: [%c%c|%c%c] Byte3: [%c%c|%c%c%c%c%c] ZL/ZR: [%c%c] | D-pad: %d",
               steering16, steering_signed, accel, brake,
               btn_lsb ? 'L' : '-', btn_rsb ? 'R' : '-', btn_plus ? '+' : '-', btn_minus ? '-' : '.',
               paddle_gear_down ? 'D' : '-', paddle_gear_up ? 'U' : '-',
               btn_home ? 'H' : '-', btn_a ? 'A' : '-', btn_b ? 'B' : '-',
               btn_x ? 'X' : '-', btn_y ? 'Y' : '-',
               btn_zl ? 'L' : '-', btn_zr ? 'R' : '-',
               dpad);
    }

    // The HID system will automatically parse these values based on the HID descriptor
    // However, the HID descriptor may need updating to match this actual format
    // No need to manually dispatch events - the parent class handles it via handleReport()
}

void HORIRacingWheelDriver::handleReport(uint64_t timestamp, uint8_t *report, uint32_t reportLength, IOHIDReportType type, uint32_t reportID)
{
    // Forward to parent class for HID event processing
    super::handleReport(timestamp, report, reportLength, type, reportID);
}
