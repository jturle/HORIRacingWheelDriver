#!/bin/bash

# Script to install pyusb for system-wide use (required for sudo python3)
# This is needed because pyusb was installed in user space, but the capture
# script needs sudo to access USB devices

echo "=========================================="
echo "Installing pyusb for system Python"
echo "=========================================="
echo ""
echo "The capture script needs sudo to access USB devices,"
echo "but pyusb is currently only installed for your user."
echo ""
echo "Running: sudo python3 -m pip install --break-system-packages pyusb"
echo ""

sudo python3 -m pip install --break-system-packages pyusb

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Success! pyusb installed system-wide"
    echo "=========================================="
    echo ""
    echo "Now you can run:"
    echo "  sudo python3 capture_hid_descriptor.py"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "✗ Installation failed"
    echo "=========================================="
    echo ""
    echo "Alternative solution:"
    echo "  sudo -H pip3 install --break-system-packages pyusb"
    echo ""
fi
