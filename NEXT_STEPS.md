# Next Steps - HORI Racing Wheel Driver

## Current Situation

✅ **What's Complete:**
- Driver framework fully implemented
- pyusb installed (version 1.3.1)
- libusb installed (version 1.0.29)
- Device detected and identified
- System mostly ready

⚠️ **Current Challenge:**
The HID descriptor capture script requires sudo access to communicate with the USB device. Since I can't provide passwords interactively, **you'll need to run it manually**.

## Device Information Discovered

From `ioreg`, we learned:
- **Vendor ID**: 0x0F0D (3853)
- **Product ID**: 0x013E (318)
- **Device Class**: 255 (Vendor-specific, not standard HID!)
- **Device SubClass**: 255
- **Device Protocol**: 255
- **Product Name**: "HORI Racing Wheel Switch"
- **Manufacturer**: "HORI CO.,LTD."
- **Serial**: "12340000"

🔴 **Important Discovery**: This device uses **vendor-specific class (255)** instead of standard HID class (3). This means it may use a custom protocol rather than standard HID reports.

## What This Means for the Driver

The driver implementation may need adjustments:

1. **Custom Protocol**: The device might not follow standard HID conventions
2. **Vendor Commands**: May require vendor-specific USB control transfers
3. **Different Report Structure**: Reports might not follow standard HID format

## Immediate Next Steps

### Step 1: Capture Device Data (Manual)

Run this command in your terminal:

```bash
sudo python3 capture_hid_descriptor.py
```

Enter your password when prompted. This will:
- Attempt to retrieve the HID descriptor
- Capture raw input reports
- Save data to `hid_descriptor.c` and `hid_descriptor.bin`

**During capture**: Move the steering wheel, press pedals, and push all buttons!

### Step 2: Analyze the Output

The script will show:
1. Whether a HID descriptor exists (it might not if it's truly vendor-specific)
2. Raw input reports in hex format
3. Pattern analysis of the data

Look for patterns in the raw reports like:
```
Report [8 bytes]: 00 7F FF 00 00 00 00 00
                  ^  ^^ ^^  -- Might be wheel position
                     ^^      -- Might be pedals
```

### Step 3: Alternative Approaches

If the HID descriptor capture doesn't work:

#### Option A: Use Windows/Linux Tools

If you have access to a Windows or Linux machine where the wheel works:

**Windows:**
```powershell
# Use USB Descriptor Dumper or USBTreeView
# Download from: https://www.uwe-sieber.de/usbtreeview_e.html
```

**Linux:**
```bash
# Show detailed USB info including HID descriptor
sudo lsusb -v -d 0f0d:013e

# Dump HID reports
sudo usbhid-dump -d 0f0d:013e
```

#### Option B: Analyze Nintendo Switch Protocol

Since this is a "HORI Racing Wheel Switch", it might use:
- Nintendo Switch Pro Controller protocol
- Custom Nintendo-licensed protocol
- Standard Switch input report format

Research existing Switch controller drivers:
- [dkms-hid-nintendo](https://github.com/nicman23/dkms-hid-nintendo)
- [joycond](https://github.com/DanielOgorchock/joycond)

#### Option C: USB Packet Capture

On your Mac, you can capture USB traffic:

1. Install Wireshark
2. Enable USB capture (requires reboot with reduced security)
3. Connect the wheel and capture packets while using it
4. Analyze the packet structure

## Driver Modifications Needed

Based on the vendor-specific class, you may need to:

### 1. Update Info.plist Matching

Change from HID-based matching to USB interface matching:

```xml
<key>IOProviderClass</key>
<string>IOUSBHostInterface</string>
<key>bInterfaceClass</key>
<integer>255</integer>
<key>idProduct</key>
<integer>318</integer>
<key>idVendor</key>
<integer>3853</integer>
```

### 2. Implement Custom Protocol Handling

Instead of relying on HID descriptors, you might need to:
- Send initialization commands
- Use vendor-specific control transfers
- Parse custom report formats

### 3. Reverse Engineer the Protocol

Monitor what data the device sends:
1. Wheel at center: `[?, ?, ?, ...]`
2. Wheel turned left: `[?, ?, ?, ...]`
3. Wheel turned right: `[?, ?, ?, ...]`
4. Accelerator pressed: `[?, ?, ?, ...]`
5. Brake pressed: `[?, ?, ?, ...]`
6. Buttons pressed: `[?, ?, ?, ...]`

Find which bytes change and how.

## Quick Test Commands

```bash
# Run the capture tool
sudo python3 capture_hid_descriptor.py

# Check device status
ioreg -p IOUSB -w0 -l | grep -i hori -A 30

# Monitor USB activity
log stream --predicate 'subsystem contains "usb"' --level debug

# Test device responsiveness
system_profiler SPUSBDataType | grep -A 30 HORI
```

## If Capture Script Fails

If the Python script can't access the device:

1. **Check USB permissions**: macOS may block access
2. **Try a different USB port**: Some ports have different security
3. **Reboot**: Sometimes USB stack needs refresh
4. **Check Activity Monitor**: Another process might be using the device

## Building Without HID Descriptor

You can still build and test the driver without the exact HID descriptor:

1. **Create Xcode project** as described in QUICKSTART.md
2. **Build the driver** with the generic descriptor
3. **Load it and monitor logs** to see what data comes through
4. **Adjust based on actual data** you observe

The logs will show raw reports in hex, which you can then analyze.

## Expected Timeline

- **Capture data**: 10-30 minutes (including testing inputs)
- **Analyze protocol**: 1-2 hours (depending on complexity)
- **Update driver**: 30-60 minutes
- **Build and test**: 1-2 hours
- **Refinement**: Ongoing

## Resources

### Switch Controller Research
- [Nintendo Switch Reverse Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)
- [Switch Controller Protocol](https://github.com/Dan-Nuclearpowered/Switch-Controller-Protocol)

### USB Analysis Tools
- [Wireshark](https://www.wireshark.org/)
- [USBPcap](https://desowin.org/usbpcap/) (Windows)
- [lsusb](https://github.com/jlhonora/lsusb) (macOS port)

### HID Resources
- [USB HID Usage Tables](https://usb.org/document-library/hid-usage-tables-13)
- [HID Report Descriptor Tool](https://eleccelerator.com/usbdescreqparser/)

## Getting Help

If you get stuck:

1. **Check the logs**: `make logs` or `log stream`
2. **Review device info**: `./get_device_info.sh`
3. **Test USB connection**: Unplug/replug and check ioreg
4. **Search for similar devices**: Look for other HORI wheel drivers

## Summary

**What You Need to Do:**

1. ✅ Install dependencies (DONE - pyusb and libusb installed)
2. 🔲 Run `sudo python3 capture_hid_descriptor.py` (enter password when prompted)
3. 🔲 Analyze the captured data
4. 🔲 Update driver code based on findings
5. 🔲 Create Xcode project
6. 🔲 Build, install, and test

**Current Blocker**: Need to manually run the capture script with sudo (requires password input)

**Workaround**: Run the script yourself in a terminal where you can enter your password.

Good luck! The driver framework is ready - it just needs the device-specific data to function properly. 🏁
