# HORI Racing Wheel macOS Driver

Using AI/Claude to write a macOS driver for the Mario Kart Racing Wheel Pro Mini for Nintendo Switch™

A complete DriverKit-based driver for the HORI Racing Wheel Switch (USB ID: 0x0F0D:0x013E) with full button and axis mapping discovered through interactive testing.

## Device Information

- **Vendor ID**: 0x0F0D (HORI CO.,LTD.)
- **Product ID**: 0x013E
- **Product Name**: HORI Racing Wheel Switch
- **Serial Number**: 12340000

## Features

- ✅ Complete DriverKit driver implementation
- ✅ 16-bit steering wheel support (65,536 positions!)
- ✅ All 20 physical controls mapped (3 analog axes, 17 digital buttons)
- ✅ Interactive mapping tool to discover button/axis positions
- ✅ Real-time testing dashboard
- ✅ Comprehensive documentation

## Mapped Controls

**All physical controls have been successfully mapped:**

- **Byte 2 (8 controls)**: D-pad (4 directions) + L/R shoulder buttons + Plus/Minus buttons
- **Byte 3 (7 controls)**: Paddle shifters (2) + Face buttons (A/B/X/Y/Home)
- **Bytes 4-5 (5 controls)**: Brake/Accelerator pedals + ZL/ZR button overlays
- **Bytes 6-7 (1 control)**: 16-bit steering wheel (signed-style encoding, 0x0000 = center)

See `DISCOVERED_MAPPING.md` for complete protocol documentation.

## Architecture

This driver uses Apple's DriverKit framework (modern replacement for kernel extensions) and implements:

- **IOUSBHostDevice**: USB device communication
- **IOUserHIDEventService**: HID event generation for game compatibility
- Asynchronous interrupt endpoint reading
- HID report descriptor translation

## Quick Start

### 1. Test the Wheel (No Driver Needed!)

Before building the driver, test all inputs work:

```bash
sudo python3 test_wheel.py
```

This displays a live dashboard showing all controls in real-time.

### 2. Build the Driver

See `BUILD_INSTRUCTIONS.md` for complete build instructions.

```bash
# Quick build with Xcode
xcodebuild -project HORIRacingWheelDriver.xcodeproj -scheme HORIRacingWheelDriver
```

### 3. Install and Load

```bash
sudo cp -r HORIRacingWheelDriver.dext /Library/SystemExtensions/
sudo systemextensionsctl developer on
systemextensionsctl submit com.yourname.HORIRacingWheelDriver
```

## Files

### Driver Code
- `HORIRacingWheelDriver.iig` - Driver interface definition
- `HORIRacingWheelDriver.cpp` - Driver implementation
- `Info.plist` - Driver bundle configuration and USB device matching
- `HORIRacingWheelDriver.entitlements` - Required DriverKit entitlements

### Testing Tools
- `test_wheel.py` - Real-time input testing dashboard
- `map_controls.py` - Interactive control mapping tool
- `capture_hid_descriptor.py` - USB HID descriptor capture tool

### Documentation
- `START_HERE.txt` - Quick orientation guide
- `BUILD_INSTRUCTIONS.md` - How to build and install
- `DISCOVERED_MAPPING.md` - Complete protocol documentation (all 20 controls!)
- `TESTING_GUIDE.md` - How to test the wheel
- `MAPPING_GUIDE.md` - How to use the mapping tool
- `QUICK_REFERENCE.md` - Command reference

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

See `BUILD_INSTRUCTIONS.md` for detailed instructions.

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
- Steering wheel position with visual indicator (16-bit precision!)
- Accelerator and brake pedal bars
- All 17 buttons (lights up when pressed)
- Paddle shifters
- D-pad direction with arrow
- Raw hex values for debugging

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

If you get this error when running test tools:

```bash
# Install pyusb for system Python
sudo python3 -m pip install --break-system-packages pyusb
```

See `FIX_PYUSB.md` for detailed troubleshooting.

## Debugging

### View Console Logs

```bash
# Real-time logging
log stream --predicate 'eventMessage contains "HORIRacingWheelDriver"' --level debug

# View system log
log show --last 10m | grep HORIRacingWheelDriver
```

### Capture HID Descriptor

```bash
sudo python3 capture_hid_descriptor.py
```

### Map Unknown Controls

```bash
sudo python3 map_controls.py
```

## Technical Highlights

### 16-bit Steering Precision

Unlike typical 8-bit wheels (256 positions), this wheel uses 16-bit steering:
- **65,536 unique positions**
- Signed-style encoding: 0x0000 = center, 0x0001-0x7FFF = right, 0x8000-0xFFFF = left
- Professional racing simulator grade precision

### Efficient Button Encoding

The protocol uses highly efficient bit-packing:
- **Byte 2**: All 8 bits used (D-pad + shoulders + system buttons)
- **Byte 3**: 7 buttons (paddles + face buttons)
- **Overlays**: ZL/ZR buttons overlay on analog pedal axes

### Complete Mapping Achieved

All 20 physical controls have been mapped through interactive testing:
- 3 analog axes (steering, brake, accelerator)
- 17 digital buttons (including D-pad as 4 buttons)

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

Contributions welcome, especially:
- Force feedback implementation
- Better error handling
- Multi-device support
- Testing on different macOS versions

## Acknowledgments

Generated with [Claude Code](https://claude.com/claude-code)
