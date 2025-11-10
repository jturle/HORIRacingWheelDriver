.PHONY: help setup build install uninstall load unload logs capture test map clean

DRIVER_NAME = HORIRacingWheelDriver
BUNDLE_ID = com.hori.racingwheel.driver
BUILD_DIR = build
DEXT_PATH = $(BUILD_DIR)/$(DRIVER_NAME).dext

help:
	@echo "HORI Racing Wheel Driver - Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  setup       - Install build dependencies"
	@echo "  map         - Interactive control mapper (find byte positions)"
	@echo "  test        - Run real-time input tester (verify buttons/axes)"
	@echo "  capture     - Capture HID descriptor from device"
	@echo "  build       - Build the driver (requires Xcode project)"
	@echo "  install     - Install driver to system"
	@echo "  uninstall   - Remove driver from system"
	@echo "  load        - Load the driver"
	@echo "  unload      - Unload the driver"
	@echo "  logs        - Stream driver logs"
	@echo "  clean       - Clean build artifacts"
	@echo ""
	@echo "Note: Most operations require sudo/admin privileges"

setup:
	@echo "Installing dependencies..."
	@command -v pip3 >/dev/null 2>&1 || { echo "pip3 not found. Install Python 3 first."; exit 1; }
	pip3 install --user pyusb
	@echo "✓ Dependencies installed"

map:
	@echo "Starting interactive control mapper..."
	@echo "This will help you find which bytes correspond to each control."
	@echo ""
	sudo python3 map_controls.py

test:
	@echo "Starting real-time input tester..."
	@echo "Move the wheel, press pedals, and push buttons to test!"
	@echo "Press Ctrl+C to exit."
	@echo ""
	sudo python3 test_wheel.py

capture:
	@echo "Capturing HID descriptor from device..."
	@echo "Note: This requires the device to be connected"
	sudo python3 capture_hid_descriptor.py

build:
	@echo "Building driver..."
	@echo "⚠ This requires an Xcode project to be set up"
	@echo "Please create an Xcode project and build from there, or use:"
	@echo "  xcodebuild -project $(DRIVER_NAME).xcodeproj -scheme $(DRIVER_NAME)"

install: build
	@echo "Installing driver..."
	sudo mkdir -p /Library/SystemExtensions
	sudo cp -r $(DEXT_PATH) /Library/SystemExtensions/
	@echo "✓ Driver installed to /Library/SystemExtensions/"

uninstall:
	@echo "Uninstalling driver..."
	sudo rm -rf /Library/SystemExtensions/$(DRIVER_NAME).dext
	@echo "✓ Driver removed"

load:
	@echo "Loading driver..."
	sudo systemextensionsctl developer on
	systemextensionsctl submit $(BUNDLE_ID)
	sudo kmutil load -p /Library/SystemExtensions/$(DRIVER_NAME).dext
	@echo "✓ Driver loaded"

unload:
	@echo "Unloading driver..."
	sudo kmutil unload -p /Library/SystemExtensions/$(DRIVER_NAME).dext
	@echo "✓ Driver unloaded"

logs:
	@echo "Streaming driver logs (Ctrl+C to stop)..."
	log stream --predicate 'eventMessage contains "$(DRIVER_NAME)"' --level debug

status:
	@echo "Checking driver status..."
	@echo ""
	@echo "=== Loaded Extensions ==="
	@sudo kmutil showloaded | grep -i hori || echo "Driver not loaded"
	@echo ""
	@echo "=== USB Device Status ==="
	@ioreg -p IOUSB -w0 -l | grep -i hori -A 10 || echo "Device not connected"
	@echo ""

clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR)
	rm -f hid_descriptor.bin hid_descriptor.c
	@echo "✓ Clean complete"

# Development helpers
dev-enable:
	@echo "Enabling development mode for system extensions..."
	sudo systemextensionsctl developer on
	@echo "✓ Development mode enabled"

dev-disable:
	@echo "Disabling development mode for system extensions..."
	sudo systemextensionsctl developer off
	@echo "✓ Development mode disabled"

check-sip:
	@echo "Checking System Integrity Protection status..."
	@csrutil status

info:
	@echo "HORI Racing Wheel Driver Information"
	@echo "====================================="
	@echo "Driver Name: $(DRIVER_NAME)"
	@echo "Bundle ID: $(BUNDLE_ID)"
	@echo "Vendor ID: 0x0F0D"
	@echo "Product ID: 0x013E"
	@echo ""
	@echo "System Information:"
	@sw_vers
	@echo ""
	@echo "Xcode Version:"
	@xcodebuild -version 2>/dev/null || echo "Xcode not found"
