#!/bin/bash

# System Readiness Checker for HORI Racing Wheel Driver Development

echo "=========================================="
echo "HORI Racing Wheel Driver - System Check"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0
warn_count=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((pass_count++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((fail_count++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((warn_count++))
}

# Check macOS version
echo "1. Checking macOS version..."
os_version=$(sw_vers -productVersion)
major_version=$(echo "$os_version" | cut -d. -f1)
if [ "$major_version" -ge 11 ]; then
    check_pass "macOS version: $os_version (DriverKit supported)"
else
    check_fail "macOS version: $os_version (DriverKit requires macOS 11.0+)"
fi
echo ""

# Check Xcode
echo "2. Checking Xcode installation..."
if command -v xcodebuild &> /dev/null; then
    xcode_version=$(xcodebuild -version | head -n 1)
    check_pass "Xcode installed: $xcode_version"

    # Check command line tools
    if xcode-select -p &> /dev/null; then
        check_pass "Command Line Tools: $(xcode-select -p)"
    else
        check_fail "Command Line Tools not found (run: xcode-select --install)"
    fi
else
    check_fail "Xcode not installed (download from Mac App Store)"
fi
echo ""

# Check Python
echo "3. Checking Python installation..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    check_pass "$python_version"

    # Check pip
    if command -v pip3 &> /dev/null; then
        check_pass "pip3 installed"

        # Check for pyusb
        if python3 -c "import usb" 2>/dev/null; then
            check_pass "pyusb library installed"
        else
            check_warn "pyusb not installed (run: pip3 install pyusb)"
        fi
    else
        check_warn "pip3 not found"
    fi
else
    check_fail "Python 3 not installed"
fi
echo ""

# Check SIP status
echo "4. Checking System Integrity Protection..."
sip_status=$(csrutil status 2>/dev/null)
if echo "$sip_status" | grep -q "disabled"; then
    check_pass "SIP is disabled (required for development)"
elif echo "$sip_status" | grep -q "enabled"; then
    check_warn "SIP is enabled (must be disabled for driver development)"
    echo "   To disable: Boot to Recovery Mode (Cmd+R) and run:"
    echo "   csrutil disable"
    echo "   csrutil authenticated-root disable"
else
    check_warn "Could not determine SIP status"
fi
echo ""

# Check for HORI device
echo "5. Checking for HORI Racing Wheel..."
if ioreg -p IOUSB -w0 -l | grep -q "HORI Racing Wheel"; then
    check_pass "HORI Racing Wheel detected"

    # Get device details
    vendor_id=$(ioreg -p IOUSB -w0 -l | grep -A 10 "HORI Racing Wheel" | grep "idVendor" | awk '{print $NF}')
    product_id=$(ioreg -p IOUSB -w0 -l | grep -A 10 "HORI Racing Wheel" | grep "idProduct" | awk '{print $NF}')
    echo "   Vendor ID: 0x$(printf '%04X' $vendor_id)"
    echo "   Product ID: 0x$(printf '%04X' $product_id)"
else
    check_warn "HORI Racing Wheel not detected (connect device and try again)"
fi
echo ""

# Check for existing driver
echo "6. Checking for existing driver installation..."
if [ -d "/Library/SystemExtensions/HORIRacingWheelDriver.dext" ]; then
    check_warn "Driver already installed at /Library/SystemExtensions/"

    # Check if loaded
    if sudo kmutil showloaded 2>/dev/null | grep -q "HORIRacingWheelDriver"; then
        check_warn "Driver is currently loaded"
    else
        echo "   Driver installed but not loaded"
    fi
else
    check_pass "No existing driver installation found"
fi
echo ""

# Check development mode
echo "7. Checking system extension development mode..."
if sudo systemextensionsctl developer 2>/dev/null | grep -q "enabled"; then
    check_pass "Development mode is enabled"
else
    check_warn "Development mode not enabled (run: sudo systemextensionsctl developer on)"
fi
echo ""

# Check disk space
echo "8. Checking disk space..."
available_space=$(df -h / | tail -1 | awk '{print $4}')
check_pass "Available disk space: $available_space"
echo ""

# Check permissions
echo "9. Checking user permissions..."
if groups | grep -q "admin"; then
    check_pass "User has admin privileges"
else
    check_warn "User is not an admin (required for driver installation)"
fi
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $pass_count"
echo -e "${YELLOW}Warnings:${NC} $warn_count"
echo -e "${RED}Failed:${NC} $fail_count"
echo ""

if [ $fail_count -eq 0 ] && [ $warn_count -eq 0 ]; then
    echo -e "${GREEN}✓ System is ready for driver development!${NC}"
    exit 0
elif [ $fail_count -eq 0 ]; then
    echo -e "${YELLOW}⚠ System is mostly ready, but some warnings need attention${NC}"
    exit 0
else
    echo -e "${RED}✗ System is not ready. Please fix the failed checks above${NC}"
    exit 1
fi
