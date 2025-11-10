# Quick Start Guide

## Overview

This driver enables macOS to recognize your HORI Racing Wheel Switch as a standard HID game controller. The driver uses Apple's modern DriverKit framework (user-space drivers) instead of kernel extensions.

## Prerequisites

Before building and installing the driver, you need:

1. **macOS 11.0 (Big Sur) or later**
2. **Xcode 12 or later** - Download from Mac App Store
3. **Apple Developer Account** - Free account is sufficient for local testing
4. **Disable SIP** (for development/testing only):
   ```bash
   # Reboot into Recovery Mode (hold Command+R during startup)
   # In Terminal:
   csrutil disable
   csrutil authenticated-root disable
   # Reboot
   ```

## Step 1: Capture HID Descriptor

First, we need to understand how your racing wheel communicates:

```bash
# Install Python USB library
pip3 install pyusb

# Run the capture tool (device must be connected)
sudo python3 capture_hid_descriptor.py
```

This will:
- Show you the HID report descriptor
- Capture sample input reports
- Save the descriptor to `hid_descriptor.c`

**Move the wheel, press pedals, and push buttons during capture!**

## Step 2: Update the Driver

Take the captured HID descriptor from `hid_descriptor.c` and replace the `reportDescriptor` array in `HORIRacingWheelDriver.cpp` (in the `newReportDescriptor()` method).

Also analyze the captured reports to understand the data format, then update the `ParseWheelData()` function accordingly.

## Step 3: Create Xcode Project

1. Open Xcode
2. File → New → Project
3. Select **"System Extension"** under macOS
4. Set Product Name: **HORIRacingWheelDriver**
5. Set Bundle Identifier: **com.yourname.HORIRacingWheelDriver** (replace "yourname")
6. Choose save location: this directory

## Step 4: Configure Project

1. **Add source files to the project**:
   - `HORIRacingWheelDriver.iig`
   - `HORIRacingWheelDriver.cpp`
   - `Info.plist`
   - `HORIRacingWheelDriver.entitlements`

2. **Update Info.plist**:
   - Replace `$(PRODUCT_BUNDLE_IDENTIFIER)` with your actual bundle ID

3. **Configure Build Settings**:
   - Target: macOS 11.0+
   - Signing & Capabilities:
     - Enable "Automatically manage signing"
     - Select your Team
     - Add `HORIRacingWheelDriver.entitlements`
   - Build Settings:
     - Set "Code Signing Entitlements" to `HORIRacingWheelDriver.entitlements`

## Step 5: Build

In Xcode:
- Product → Build (⌘B)
- Product → Archive (for distribution)

Or from terminal:
```bash
xcodebuild -project HORIRacingWheelDriver.xcodeproj -scheme HORIRacingWheelDriver
```

## Step 6: Install and Load

```bash
# Enable development mode
sudo systemextensionsctl developer on

# Copy the built .dext to system extensions directory
sudo cp -r build/Debug/HORIRacingWheelDriver.dext /Library/SystemExtensions/

# Load the driver
sudo kmutil load -p /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Or use systemextensionsctl (may require approval)
systemextensionsctl submit com.yourname.HORIRacingWheelDriver
```

## Step 7: Verify

```bash
# Check if driver is loaded
sudo kmutil showloaded | grep HORI

# Check device in USB tree
ioreg -p IOUSB -w0 -l | grep -i hori -A 20

# Monitor driver logs
log stream --predicate 'eventMessage contains "HORIRacingWheelDriver"' --level debug
```

You should see log messages like:
```
HORIRacingWheelDriver: init successful
HORIRacingWheelDriver: Start called
HORIRacingWheelDriver: Found interrupt IN pipe at address 0x81
HORIRacingWheelDriver: Successfully started
```

## Step 8: Test

1. Open **System Settings → Game Controllers** (if available)
2. Or use a game that supports controllers
3. Or test with a tool like [Enjoyable](https://github.com/nuibb/Enjoyable) or [Joystick Show](https://apps.apple.com/app/joystick-show/id515886877)

The racing wheel should appear as a standard HID device with:
- Steering axis
- Accelerator and brake pedals
- Buttons
- D-pad

## Troubleshooting

### Driver won't load
```bash
# Check system extension status
systemextensionsctl list

# Check for errors
log show --last 10m | grep HORIRacingWheelDriver
```

### Device not recognized
```bash
# Verify USB connection
ioreg -p IOUSB -w0 -l | grep -i hori

# Check if device is being claimed by another driver
ioreg -c IOService -r -n "HORI Racing Wheel Switch"
```

### Build errors
- Make sure Xcode Command Line Tools are installed: `xcode-select --install`
- Check that your bundle identifier matches everywhere
- Verify entitlements are properly set
- Ensure you have a valid signing certificate

### SIP Issues
If you get permission errors, verify SIP is disabled:
```bash
csrutil status
# Should show: "System Integrity Protection status: disabled."
```

## Uninstalling

```bash
# Unload the driver
sudo kmutil unload -p /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Remove the extension
sudo rm -rf /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Re-enable SIP (optional, recommended for normal use)
# Reboot into Recovery Mode, then:
csrutil enable
```

## Using the Makefile

A Makefile is provided for common tasks:

```bash
make setup      # Install dependencies (pyusb)
make capture    # Capture HID descriptor
make status     # Check driver status
make logs       # Stream driver logs
make info       # Show system info
```

## Next Steps

1. **Customize the HID descriptor** based on captured data
2. **Implement proper report parsing** in `ParseWheelData()`
3. **Add force feedback support** (if your wheel supports it)
4. **Test with various games**
5. **Create a proper installer** using `pkgbuild`

## Important Notes

⚠️ **Security**: This driver runs in user space (DriverKit), which is safer than kernel extensions, but:
- Only install if you understand the risks
- Review the code before building
- Use a dedicated testing Mac if possible

⚠️ **SIP**: Disabling System Integrity Protection reduces system security. Only do this on a development machine, and re-enable SIP when done testing.

⚠️ **Code Signing**: For distribution, you need a paid Apple Developer account and proper code signing certificates.

## Resources

- [DriverKit Documentation](https://developer.apple.com/documentation/driverkit)
- [USB HID Specification](https://www.usb.org/hid)
- [IOKit Fundamentals](https://developer.apple.com/library/archive/documentation/DeviceDrivers/Conceptual/IOKitFundamentals/)

## Support

For issues or questions:
1. Check the logs: `make logs`
2. Verify device connection: `make status`
3. Review the README.md for detailed information
4. Check Apple's DriverKit documentation

Good luck! 🏎️💨
