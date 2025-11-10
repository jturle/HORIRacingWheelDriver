#!/usr/bin/env python3
"""
HORI Racing Wheel HID Descriptor Capture Tool

This script attempts to capture the HID report descriptor from the HORI Racing Wheel
device connected via USB. This information is crucial for properly parsing input reports.

Requirements:
    pip install pyusb

Usage:
    sudo python3 capture_hid_descriptor.py
"""

import sys
import struct

try:
    import usb.core
    import usb.util
except ImportError:
    print("Error: pyusb not installed")
    print("Install with: pip3 install pyusb")
    sys.exit(1)

# HORI Racing Wheel USB IDs
VENDOR_ID = 0x0F0D
PRODUCT_ID = 0x013E

def parse_hid_descriptor(data):
    """Parse and display HID descriptor in a readable format."""
    i = 0
    indent = 0

    print("\n" + "="*60)
    print("HID REPORT DESCRIPTOR")
    print("="*60)

    while i < len(data):
        item = data[i]
        i += 1

        # Parse item type, tag, and size
        item_type = (item >> 2) & 0x03
        item_tag = (item >> 4) & 0x0F
        item_size = item & 0x03

        if item_size == 3:
            item_size = 4

        # Get item data
        item_data = data[i:i+item_size]
        i += item_size

        # Convert data to integer
        value = 0
        if item_size > 0:
            value = int.from_bytes(item_data, byteorder='little', signed=False)

        # Format output
        hex_str = " ".join([f"{b:02X}" for b in [item] + list(item_data)])
        print(f"  {'  '*indent}{hex_str:20s}", end=" ")

        # Decode item
        if item_type == 0:  # Main
            if item_tag == 8:  # Input
                print(f"Input ({format_input_output_feature(value)})")
            elif item_tag == 9:  # Output
                print(f"Output ({format_input_output_feature(value)})")
            elif item_tag == 10:  # Collection
                print(f"Collection ({format_collection(value)})")
                indent += 1
            elif item_tag == 11:  # Feature
                print(f"Feature ({format_input_output_feature(value)})")
            elif item_tag == 12:  # End Collection
                indent = max(0, indent - 1)
                print("End Collection")
            else:
                print(f"Main Item {item_tag}: {value}")

        elif item_type == 1:  # Global
            if item_tag == 0:
                print(f"Usage Page (0x{value:04X})")
            elif item_tag == 1:
                print(f"Logical Minimum ({value if value < 0x8000 else value - 0x10000})")
            elif item_tag == 2:
                print(f"Logical Maximum ({value if value < 0x8000 else value - 0x10000})")
            elif item_tag == 3:
                print(f"Physical Minimum ({value})")
            elif item_tag == 4:
                print(f"Physical Maximum ({value})")
            elif item_tag == 5:
                print(f"Unit Exponent ({value})")
            elif item_tag == 6:
                print(f"Unit ({value})")
            elif item_tag == 7:
                print(f"Report Size ({value})")
            elif item_tag == 8:
                print(f"Report ID ({value})")
            elif item_tag == 9:
                print(f"Report Count ({value})")
            elif item_tag == 10:
                print(f"Push")
            elif item_tag == 11:
                print(f"Pop")
            else:
                print(f"Global Item {item_tag}: {value}")

        elif item_type == 2:  # Local
            if item_tag == 0:
                print(f"Usage (0x{value:02X})")
            elif item_tag == 1:
                print(f"Usage Minimum (0x{value:02X})")
            elif item_tag == 2:
                print(f"Usage Maximum (0x{value:02X})")
            elif item_tag == 3:
                print(f"Designator Index ({value})")
            elif item_tag == 4:
                print(f"Designator Minimum ({value})")
            elif item_tag == 5:
                print(f"Designator Maximum ({value})")
            elif item_tag == 7:
                print(f"String Index ({value})")
            elif item_tag == 8:
                print(f"String Minimum ({value})")
            elif item_tag == 9:
                print(f"String Maximum ({value})")
            elif item_tag == 10:
                print(f"Delimiter ({value})")
            else:
                print(f"Local Item {item_tag}: {value}")
        else:
            print(f"Reserved Item {item_tag}: {value}")

    print("="*60 + "\n")

def format_input_output_feature(value):
    """Format Input/Output/Feature item flags."""
    flags = []
    if value & 0x01:
        flags.append("Constant")
    else:
        flags.append("Data")

    if value & 0x02:
        flags.append("Variable")
    else:
        flags.append("Array")

    if value & 0x04:
        flags.append("Relative")
    else:
        flags.append("Absolute")

    if value & 0x08:
        flags.append("Wrap")
    if value & 0x10:
        flags.append("Non Linear")
    if value & 0x20:
        flags.append("No Preferred")
    if value & 0x40:
        flags.append("Null State")
    if value & 0x100:
        flags.append("Buffered Bytes")

    return ", ".join(flags)

def format_collection(value):
    """Format Collection type."""
    collections = {
        0x00: "Physical",
        0x01: "Application",
        0x02: "Logical",
        0x03: "Report",
        0x04: "Named Array",
        0x05: "Usage Switch",
        0x06: "Usage Modifier"
    }
    return collections.get(value, f"Reserved 0x{value:02X}")

def capture_reports(dev, interface_num, endpoint_addr, duration=5):
    """Capture and display raw input reports."""
    print(f"\n{'='*60}")
    print(f"CAPTURING RAW INPUT REPORTS (for {duration} seconds)")
    print(f"{'='*60}")
    print("Please move the steering wheel, press pedals, and push buttons...")
    print()

    import time
    start_time = time.time()
    report_count = 0

    try:
        while time.time() - start_time < duration:
            try:
                data = dev.read(endpoint_addr, 64, timeout=100)
                if data:
                    report_count += 1
                    hex_str = " ".join([f"{b:02X}" for b in data])
                    print(f"Report {report_count:3d} [{len(data):2d} bytes]: {hex_str}")
            except usb.core.USBError as e:
                if e.errno != 110:  # Ignore timeout errors
                    print(f"USB Error: {e}")
    except KeyboardInterrupt:
        print("\nCapture interrupted by user")

    print(f"\n{'='*60}")
    print(f"Captured {report_count} reports")
    print(f"{'='*60}\n")

def main():
    print("="*60)
    print("HORI Racing Wheel HID Descriptor Capture Tool")
    print("="*60)
    print(f"Looking for device: VID=0x{VENDOR_ID:04X}, PID=0x{PRODUCT_ID:04X}")

    # Find the device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    if dev is None:
        print("\nError: HORI Racing Wheel not found!")
        print("Make sure the device is connected.")
        sys.exit(1)

    print(f"✓ Device found: {dev.product}")
    print(f"  Manufacturer: {dev.manufacturer}")
    print(f"  Serial: {dev.serial_number}")
    print()

    # Detach kernel driver if necessary (on macOS this may fail, which is OK)
    interface_num = 0
    try:
        if dev.is_kernel_driver_active(interface_num):
            print("Detaching kernel driver...")
            try:
                dev.detach_kernel_driver(interface_num)
                print("✓ Kernel driver detached")
            except usb.core.USBError as e:
                print(f"Could not detach kernel driver: {e}")
                print("This is often expected on macOS - continuing anyway...")
    except (usb.core.USBError, NotImplementedError) as e:
        # On macOS, is_kernel_driver_active may not be supported
        print(f"Note: Kernel driver check not available on this platform - continuing...")

    # Set configuration
    try:
        dev.set_configuration()
    except usb.core.USBError as e:
        print(f"Error setting configuration: {e}")

    # Get configuration
    cfg = dev.get_active_configuration()
    interface = cfg[(0, 0)]

    print(f"Interface: {interface.bInterfaceNumber}")
    print(f"  Class: 0x{interface.bInterfaceClass:02X}")
    print(f"  SubClass: 0x{interface.bInterfaceSubClass:02X}")
    print(f"  Protocol: 0x{interface.bInterfaceProtocol:02X}")

    # Find endpoints
    endpoint_in = None
    for ep in interface:
        print(f"  Endpoint: 0x{ep.bEndpointAddress:02X}")
        print(f"    Direction: {'IN' if ep.bEndpointAddress & 0x80 else 'OUT'}")
        print(f"    Type: {['Control', 'Isochronous', 'Bulk', 'Interrupt'][ep.bmAttributes & 0x03]}")
        print(f"    Max Packet Size: {ep.wMaxPacketSize}")

        if (ep.bEndpointAddress & 0x80) and ((ep.bmAttributes & 0x03) == 0x03):
            endpoint_in = ep.bEndpointAddress

    # Try to get HID descriptor
    print("\n" + "="*60)
    print("ATTEMPTING TO RETRIEVE HID DESCRIPTOR")
    print("="*60)

    # HID Class Descriptor Request: GET_DESCRIPTOR
    # bmRequestType = 0x81 (Device to Host, Class, Interface)
    # bRequest = 0x06 (GET_DESCRIPTOR)
    # wValue = 0x2200 (HID Report Descriptor)
    # wIndex = interface number
    # wLength = expected descriptor size

    try:
        # Try to get HID report descriptor
        hid_descriptor = dev.ctrl_transfer(
            bmRequestType=0x81,
            bRequest=0x06,  # GET_DESCRIPTOR
            wValue=0x2200,  # HID Report Descriptor
            wIndex=interface_num,
            data_or_wLength=1024
        )

        if hid_descriptor:
            print(f"✓ Retrieved HID descriptor ({len(hid_descriptor)} bytes)")

            # Display raw bytes
            print("\nRaw HID Descriptor (C array format):")
            print("static const uint8_t reportDescriptor[] = {")
            for i in range(0, len(hid_descriptor), 16):
                chunk = hid_descriptor[i:i+16]
                hex_str = ", ".join([f"0x{b:02X}" for b in chunk])
                print(f"    {hex_str},")
            print("};")

            # Parse and display
            parse_hid_descriptor(hid_descriptor)

            # Save to file
            with open("hid_descriptor.bin", "wb") as f:
                f.write(bytes(hid_descriptor))
            print(f"✓ Saved to hid_descriptor.bin")

            with open("hid_descriptor.c", "w") as f:
                f.write("// HORI Racing Wheel HID Report Descriptor\n")
                f.write("static const uint8_t reportDescriptor[] = {\n")
                for i in range(0, len(hid_descriptor), 16):
                    chunk = hid_descriptor[i:i+16]
                    hex_str = ", ".join([f"0x{b:02X}" for b in chunk])
                    f.write(f"    {hex_str},\n")
                f.write("};\n")
            print(f"✓ Saved to hid_descriptor.c")

        else:
            print("⚠ No HID descriptor retrieved")

    except usb.core.USBError as e:
        print(f"⚠ Could not retrieve HID descriptor: {e}")
        print("This is common for non-standard HID devices.")

    # Capture some reports
    if endpoint_in:
        print("\nWould you like to capture raw input reports? (y/n): ", end="")
        response = input().strip().lower()
        if response == 'y':
            capture_reports(dev, interface_num, endpoint_in)

    # Cleanup
    try:
        usb.util.release_interface(dev, interface_num)
    except:
        pass

    print("\nDone!")

if __name__ == "__main__":
    if sys.platform != "darwin":
        print("Warning: This script is designed for macOS but may work on other systems")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
