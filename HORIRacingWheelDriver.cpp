#include <os/log.h>
#include <DriverKit/IOLib.h>
#include <DriverKit/IOBufferMemoryDescriptor.h>
#include <USBDriverKit/IOUSBHostDevice.h>
#include <USBDriverKit/IOUSBHostInterface.h>
#include <HIDDriverKit/HIDDriverKit.h>

#include "HORIRacingWheelDriver.h"

#define LOG_PREFIX "HORIRacingWheelDriver: "

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
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "super::init failed");
        return false;
    }

    ivars = IONewZero(HORIRacingWheelDriver_IVars, 1);
    if (!ivars) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to allocate ivars");
        return false;
    }

    os_log(OS_LOG_DEFAULT, LOG_PREFIX "init successful");
    return true;
}

kern_return_t HORIRacingWheelDriver::Start(IOService *provider)
{
    kern_return_t ret;
    IOUSBHostDevice *device;
    const IOUSBConfigurationDescriptor *configDesc;
    const IOUSBInterfaceDescriptor *interfaceDesc;

    os_log(OS_LOG_DEFAULT, LOG_PREFIX "Start called");

    ret = super::Start(provider);
    if (ret != kIOReturnSuccess) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "super::Start failed: 0x%x", ret);
        return ret;
    }

    // Cast provider to USB device
    device = OSDynamicCast(IOUSBHostDevice, provider);
    if (!device) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Provider is not an IOUSBHostDevice");
        Stop(provider);
        return kIOReturnError;
    }

    // Open the device
    ret = device->Open(this, 0, nullptr);
    if (ret != kIOReturnSuccess) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to open device: 0x%x", ret);
        Stop(provider);
        return ret;
    }

    // Get configuration descriptor
    configDesc = device->CopyConfigurationDescriptor(0);
    if (!configDesc) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to get configuration descriptor");
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Find the first interface (usually the HID interface)
    ivars->interface = device->CopyInterface(0);
    if (!ivars->interface) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to copy interface");
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Open the interface
    ret = ivars->interface->Open(this, 0, nullptr);
    if (ret != kIOReturnSuccess) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to open interface: 0x%x", ret);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return ret;
    }

    // Get interface descriptor
    interfaceDesc = ivars->interface->CopyInterfaceDescriptor();
    if (!interfaceDesc) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to get interface descriptor");
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Find interrupt IN endpoint (typically endpoint 1 for HID)
    for (uint8_t i = 0; i < interfaceDesc->bNumEndpoints; i++) {
        const IOUSBEndpointDescriptor *endpointDesc = nullptr;

        ret = ivars->interface->CopyEndpointDescriptor(i, &endpointDesc);
        if (ret == kIOReturnSuccess && endpointDesc) {
            uint8_t epAddress = endpointDesc->bEndpointAddress;
            uint8_t epType = endpointDesc->bmAttributes & kIOUSBEndpointDescriptorTransferTypeMask;

            // Check if it's an interrupt IN endpoint
            if ((epAddress & kIOUSBEndpointDescriptorDirectionMask) == kIOUSBEndpointDescriptorDirectionIn &&
                epType == kIOUSBEndpointDescriptorTransferTypeInterrupt) {

                ivars->inPipe = ivars->interface->CopyPipe(epAddress);
                if (ivars->inPipe) {
                    os_log(OS_LOG_DEFAULT, LOG_PREFIX "Found interrupt IN pipe at address 0x%02x", epAddress);
                    break;
                }
            }
        }
    }

    if (!ivars->inPipe) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to find interrupt IN endpoint");
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    // Allocate report buffer (typical racing wheel reports are 8-64 bytes)
    ret = IOBufferMemoryDescriptor::Create(kIOMemoryDirectionIn, 64, 0, &ivars->reportBuffer);
    if (ret != kIOReturnSuccess || !ivars->reportBuffer) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to allocate report buffer: 0x%x", ret);
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
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to create completion action: 0x%x", ret);
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
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to start async IO: 0x%x", ret);
        OSSafeReleaseNULL(ivars->completionAction);
        OSSafeReleaseNULL(ivars->reportBuffer);
        OSSafeReleaseNULL(ivars->inPipe);
        ivars->interface->Close(this, 0);
        OSSafeReleaseNULL(ivars->interface);
        device->Close(this, 0);
        Stop(provider);
        return kIOReturnError;
    }

    os_log(OS_LOG_DEFAULT, LOG_PREFIX "Successfully started");

    ret = RegisterService();

    return ret;
}

kern_return_t HORIRacingWheelDriver::Stop(IOService *provider)
{
    os_log(OS_LOG_DEFAULT, LOG_PREFIX "Stop called");

    if (ivars->inPipe) {
        ivars->inPipe->Abort();
        OSSafeReleaseNULL(ivars->inPipe);
    }

    if (ivars->completionAction) {
        ivars->completionAction->Release();
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
    os_log(OS_LOG_DEFAULT, LOG_PREFIX "free called");

    if (ivars) {
        IOSafeDeleteNULL(ivars, HORIRacingWheelDriver_IVars, 1);
    }

    super::free();
}

void HORIRacingWheelDriver::ReadComplete(OSAction *action, IOReturn status, uint32_t actualByteCount, uint64_t completionTimestamp)
{
    kern_return_t ret;

    if (status != kIOReturnSuccess) {
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Read completed with error: 0x%x", status);
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
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Failed to queue next read: 0x%x", ret);
    }
}

void HORIRacingWheelDriver::HandleInputReport(uint64_t timestamp, uint8_t *report, uint32_t reportLength)
{
    // Log raw report for debugging
    if (reportLength >= 8) {
        os_log(OS_LOG_DEFAULT, LOG_PREFIX "Report [%d bytes]: %02x %02x %02x %02x %02x %02x %02x %02x",
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
        os_log_error(OS_LOG_DEFAULT, LOG_PREFIX "Report too short: %d bytes", reportLength);
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

kern_return_t HORIRacingWheelDriver::handleReport(uint64_t timestamp, uint8_t *report, uint32_t reportLength, IOHIDReportType type, uint32_t reportID)
{
    // Forward to parent class for HID event processing
    return super::handleReport(timestamp, report, reportLength, type, reportID);
}

OSDictionary * HORIRacingWheelDriver::newDeviceDescription()
{
    OSDictionary *dict = OSDictionary::withCapacity(10);
    if (!dict) {
        return nullptr;
    }

    // Set device properties
    OSNumber *vendorID = OSNumber::withNumber(0x0F0D, 16);
    OSNumber *productID = OSNumber::withNumber(0x013E, 16);
    OSNumber *version = OSNumber::withNumber(0x0116, 16);
    OSString *product = OSString::withCString("HORI Racing Wheel Switch");
    OSString *manufacturer = OSString::withCString("HORI CO.,LTD.");
    OSString *serial = OSString::withCString("12340000");

    // Usage page: Generic Desktop (0x01), Usage: Joystick/Game Pad (0x04 or 0x05)
    OSNumber *usagePage = OSNumber::withNumber(0x01, 16);
    OSNumber *usage = OSNumber::withNumber(0x04, 16);

    if (vendorID) dict->setObject("VendorID", vendorID);
    if (productID) dict->setObject("ProductID", productID);
    if (version) dict->setObject("VersionNumber", version);
    if (product) dict->setObject("Product", product);
    if (manufacturer) dict->setObject("Manufacturer", manufacturer);
    if (serial) dict->setObject("SerialNumber", serial);
    if (usagePage) dict->setObject("PrimaryUsagePage", usagePage);
    if (usage) dict->setObject("PrimaryUsage", usage);

    OSSafeReleaseNULL(vendorID);
    OSSafeReleaseNULL(productID);
    OSSafeReleaseNULL(version);
    OSSafeReleaseNULL(product);
    OSSafeReleaseNULL(manufacturer);
    OSSafeReleaseNULL(serial);
    OSSafeReleaseNULL(usagePage);
    OSSafeReleaseNULL(usage);

    return dict;
}

OSData * HORIRacingWheelDriver::newReportDescriptor()
{
    // HORI Racing Wheel HID Report Descriptor
    // Captured from actual device via USB
    static const uint8_t reportDescriptor[] = {
        0x05, 0x01, 0x09, 0x05, 0xA1, 0x01, 0x15, 0x00, 0x25, 0x01, 0x35, 0x00, 0x45, 0x01, 0x75, 0x01,
        0x95, 0x0D, 0x05, 0x09, 0x19, 0x01, 0x29, 0x0D, 0x81, 0x02, 0x95, 0x03, 0x81, 0x01, 0x05, 0x01,
        0x25, 0x07, 0x46, 0x3B, 0x01, 0x75, 0x04, 0x95, 0x01, 0x65, 0x14, 0x09, 0x39, 0x81, 0x42, 0x65,
        0x00, 0x95, 0x01, 0x81, 0x01, 0x26, 0xFF, 0x00, 0x46, 0xFF, 0x00, 0x09, 0x30, 0x09, 0x31, 0x09,
        0x32, 0x09, 0x35, 0x75, 0x08, 0x95, 0x04, 0x81, 0x02, 0x06, 0x00, 0xFF, 0x09, 0x20, 0x09, 0x21,
        0x09, 0x22, 0x09, 0x23, 0x09, 0x24, 0x09, 0x25, 0x09, 0x26, 0x09, 0x27, 0x09, 0x28, 0x09, 0x29,
        0x09, 0x2A, 0x09, 0x2B, 0x95, 0x0C, 0x81, 0x02, 0x0A, 0x21, 0x26, 0x95, 0x08, 0xB1, 0x02, 0xC0,
    };

    return OSData::withBytes(reportDescriptor, sizeof(reportDescriptor));
}
