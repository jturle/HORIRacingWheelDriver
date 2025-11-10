#!/bin/bash

# HORI Racing Wheel Device Information Extractor
# This script uses macOS built-in tools to gather USB device information
# without requiring Python or special permissions

echo "=========================================="
echo "HORI Racing Wheel Device Information"
echo "=========================================="
echo ""

# Get detailed USB information
echo "=== USB Device Details ==="
ioreg -p IOUSB -w0 -l -r | grep -A 50 "HORI Racing Wheel" | head -60

echo ""
echo "=== Looking for HID Descriptors ==="

# Try to find HID-related information
ioreg -c IOHIDDevice -r -l | grep -A 30 "HORI" | head -40

echo ""
echo "=== Device Class Information ==="
system_profiler SPUSBDataType 2>/dev/null | grep -A 30 "HORI"

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. The device information above shows USB details"
echo "2. To capture HID reports, you'll need to run:"
echo "   sudo python3 capture_hid_descriptor.py"
echo "   (This requires sudo password for USB access)"
echo ""
echo "3. Alternatively, on Windows or Linux where the device"
echo "   works natively, you can use tools like:"
echo "   - Windows: USB Descriptor Dumper, Wireshark + USBPcap"
echo "   - Linux: lsusb -v, usbhid-dump"
echo ""
