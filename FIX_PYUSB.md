# Fix: pyusb Not Found When Using sudo

## Problem

You're seeing this error:
```
sudo python3 capture_hid_descriptor.py
Error: pyusb not installed
Install with: pip3 install pyusb
```

## Why This Happens

- `pyusb` was installed for your user account only
- When you run `sudo python3`, it uses the **system Python** as root user
- The root user doesn't have access to your user-installed packages

## Solution

You need to install pyusb system-wide. Run **ONE** of these commands:

### Option 1: Using the Helper Script (Easiest)

```bash
./install_pyusb_for_sudo.sh
```

### Option 2: Manual Installation (Alternative)

```bash
sudo python3 -m pip install --break-system-packages pyusb
```

### Option 3: Using sudo -H (Alternative)

```bash
sudo -H pip3 install --break-system-packages pyusb
```

## After Installing

Once installed, verify it works:

```bash
# Test that sudo can now see pyusb
sudo python3 -c "import usb; print('pyusb is now accessible with sudo')"
```

Then run the capture tool:

```bash
sudo python3 capture_hid_descriptor.py
```

## Quick Fix Commands

Copy and paste these one by one:

```bash
# Install pyusb for system Python
sudo python3 -m pip install --break-system-packages pyusb

# Verify it worked
sudo python3 -c "import usb; print('Success!')"

# Run the capture tool
sudo python3 capture_hid_descriptor.py
```

## What the Capture Tool Will Do

1. Find your HORI Racing Wheel
2. Attempt to retrieve the HID descriptor
3. Capture raw input reports for 5 seconds
4. **During capture**: Move the wheel, press pedals, push all buttons!
5. Save data to `hid_descriptor.bin` and `hid_descriptor.c`

## Expected Output

```
============================================================
HORI Racing Wheel HID Descriptor Capture Tool
============================================================
Looking for device: VID=0x0F0D, PID=0x013E
✓ Device found: HORI Racing Wheel Switch
  Manufacturer: HORI CO.,LTD.
  Serial: 12340000

Interface: 0
  Class: 0xFF
  SubClass: 0xFF
  Protocol: 0xFF
  Endpoint: 0x81
    Direction: IN
    Type: Interrupt
    Max Packet Size: 64

============================================================
ATTEMPTING TO RETRIEVE HID DESCRIPTOR
============================================================
[Descriptor data or error message]

Would you like to capture raw input reports? (y/n): y

[Raw reports shown as you move the wheel and press buttons]
```

## Troubleshooting

### Still getting "pyusb not installed" error?

Try checking which Python sudo is using:

```bash
sudo which python3
sudo python3 --version
```

Then explicitly use that Python:

```bash
# If sudo python3 is at /usr/bin/python3
sudo /usr/bin/python3 -m pip install --break-system-packages pyusb
sudo /usr/bin/python3 capture_hid_descriptor.py
```

### Permission denied errors?

Make sure you're entering your password correctly when prompted by sudo.

### Device not found?

Check that the wheel is connected:

```bash
ioreg -p IOUSB -w0 -l | grep -i hori
```

Should show "HORI Racing Wheel Switch" in the output.

### libusb errors?

libusb should already be installed (version 1.0.29), but if you get errors:

```bash
brew install libusb
```

## Next Steps After Capture

1. Review the captured data in `hid_descriptor.c`
2. Look at the raw input reports to understand the protocol
3. Update `HORIRacingWheelDriver.cpp` with the actual descriptor
4. Implement proper parsing in `ParseWheelData()`
5. Build and test the driver!

---

**TL;DR:** Run this:
```bash
sudo python3 -m pip install --break-system-packages pyusb
sudo python3 capture_hid_descriptor.py
```
