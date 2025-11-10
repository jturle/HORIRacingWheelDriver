# HORI Racing Wheel macOS Driver

A DriverKit-based driver for the HORI Racing Wheel Switch (USB ID: 0x0F0D:0x013E) on macOS.

## Device Information

- **Vendor ID**: 0x0F0D (HORI CO.,LTD.)
- **Product ID**: 0x013E
- **Product Name**: HORI Racing Wheel Switch
- **Serial Number**: 12340000

## Architecture

This driver uses Apple's DriverKit framework (modern replacement for kernel extensions) and implements:

- **IOUSBHostDevice**: USB device communication
- **IOUserHIDEventService**: HID event generation for game compatibility
- Asynchronous interrupt endpoint reading
- HID report descriptor translation

## Files

- `HORIRacingWheelDriver.iig` - Driver interface definition
- `HORIRacingWheelDriver.cpp` - Driver implementation
- `Info.plist` - Driver bundle configuration and USB device matching
- `HORIRacingWheelDriver.entitlements` - Required DriverKit entitlements

## Building

### Prerequisites

1. **Xcode 12 or later** with Command Line Tools
2. **macOS 11.0 SDK or later**
3. **Apple Developer Account** (for code signing)
4. **System Integrity Protection (SIP)** must be disabled for testing:
   ```bash
   # Reboot into Recovery Mode (Command+R during boot)
   csrutil disable
   csrutil authenticated-root disable
   # Reboot normally
   ```

### Build Steps

1. Create an Xcode project:
   - File → New → Project
   - Choose "System Extension" template
   - Set Product Name to "HORIRacingWheelDriver"
   - Set Bundle Identifier (e.g., `com.yourname.HORIRacingWheelDriver`)

2. Add the files to your project:
   - Add all `.iig`, `.cpp`, `.plist`, and `.entitlements` files

3. Configure build settings:
   - Set deployment target to macOS 11.0+
   - Enable "Hardened Runtime"
   - Set code signing identity
   - Add the entitlements file to the target

4. Build the driver:
   ```bash
   xcodebuild -project HORIRacingWheelDriver.xcodeproj -scheme HORIRacingWheelDriver
   ```

### Alternative: Manual Build (Advanced)

```bash
# Compile the IIG file
iig HORIRacingWheelDriver.iig

# Compile the implementation
clang++ -std=c++17 -arch arm64 -arch x86_64 \
    -framework DriverKit \
    -framework USBDriverKit \
    -framework HIDDriverKit \
    -c HORIRacingWheelDriver.cpp -o HORIRacingWheelDriver.o

# Link (requires proper DriverKit setup)
# Note: Full manual linking is complex; Xcode is recommended
```

## Installation

1. **Build the driver extension** (.dext bundle)

2. **Copy to system extensions directory**:
   ```bash
   sudo cp -r HORIRacingWheelDriver.dext /Library/SystemExtensions/
   ```

3. **Activate the extension**:
   ```bash
   sudo systemextensionsctl developer on
   systemextensionsctl submit com.yourname.HORIRacingWheelDriver
   ```

4. **Load the driver**:
   ```bash
   sudo kmutil load -p /Library/SystemExtensions/HORIRacingWheelDriver.dext
   ```

5. **Verify driver is loaded**:
   ```bash
   sudo kmutil showloaded | grep HORI
   ```

## Testing

### Real-time Input Testing (Before Building Driver)

Test all wheel inputs without installing the driver:

```bash
sudo python3 test_wheel.py
```

This displays a live dashboard showing:
- Steering wheel position with visual indicator
- Accelerator, brake, and clutch pedal bars
- All 13 buttons (lights up when pressed)
- D-pad direction with arrow
- Raw hex values

See `TESTING_GUIDE.md` for complete testing instructions.

### Driver Testing (After Installation)

1. **Check driver attachment**:
   ```bash
   ioreg -p IOUSB -w0 -l | grep -i hori -A 20
   ```

2. **Monitor driver logs**:
   ```bash
   log stream --predicate 'eventMessage contains "HORIRacingWheelDriver"' --level debug
   ```

3. **Test with a game**: The wheel should appear as a standard HID game controller

## Common Issues

### "pyusb not installed" when using sudo

If you get this error when running `sudo python3 capture_hid_descriptor.py`:

```bash
# Install pyusb for system Python
sudo python3 -m pip install --break-system-packages pyusb
```

See `FIX_PYUSB.md` for detailed troubleshooting.

## Debugging

### Capture USB Traffic

Use a USB analyzer or Wireshark with USBPcap to capture the HID report structure from a Windows machine where the wheel works natively.

### Get HID Descriptor from Device

Run the included helper script:
```bash
sudo python3 capture_hid_descriptor.py
```

This will help you understand the actual report format the device uses.

### View Console Logs

```bash
# Real-time logging
log stream --predicate 'eventMessage contains "HORIRacingWheelDriver"' --level debug

# View system log
log show --last 10m | grep HORIRacingWheelDriver
```

## Known Limitations

1. **Generic HID Report Descriptor**: The current implementation uses a generic racing wheel descriptor. You need to:
   - Capture the actual HID report descriptor from the device
   - Update `newReportDescriptor()` method with the real descriptor
   - Update `ParseWheelData()` to correctly parse the device's report format

2. **Report Parsing**: The `ParseWheelData()` function needs to be customized based on the actual report structure

3. **Force Feedback**: This driver does not currently implement force feedback (FFB) output reports

## Customization Needed

To make this driver fully functional, you need to:

1. **Capture the HID Report Descriptor**:
   - Use `capture_hid_descriptor.py` script
   - Or extract from Windows/Linux where the device works
   - Update `newReportDescriptor()` in the driver

2. **Analyze Report Format**:
   - Monitor raw reports in `HandleInputReport()`
   - Determine bit positions for:
     - Steering wheel axis
     - Accelerator pedal
     - Brake pedal
     - Clutch pedal (if present)
     - Buttons
     - D-pad

3. **Update ParseWheelData()**:
   - Extract values from correct byte positions
   - Scale values appropriately

## Security Notes

- DriverKit extensions run in user space (safer than kernel extensions)
- Code must be signed with a Developer ID
- Requires entitlements for USB and HID access
- SIP must be disabled for development/testing

## Resources

- [Apple DriverKit Documentation](https://developer.apple.com/documentation/driverkit)
- [USB HID Usage Tables](https://usb.org/document-library/hid-usage-tables-13)
- [IOKit Fundamentals](https://developer.apple.com/library/archive/documentation/DeviceDrivers/Conceptual/IOKitFundamentals/)

## License

MIT License - Modify and use as needed

## Contributing

This is a starting point. Contributions welcome, especially:
- Actual HID report descriptor for this device
- Force feedback implementation
- Better error handling
- Multi-device support
