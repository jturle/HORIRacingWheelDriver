# HORI Racing Wheel Driver - Quick Reference

## 🚨 You're Here Because...

You just got: `Error: pyusb not installed` when running the capture script.

## ✅ Quick Fix (Copy/Paste This)

```bash
# Install pyusb for sudo
sudo python3 -m pip install --break-system-packages pyusb

# Run the capture tool
sudo python3 capture_hid_descriptor.py

# When prompted, type 'y' to capture reports
# Then MOVE THE WHEEL and PRESS ALL BUTTONS for 5 seconds!
```

## 📋 Complete Setup Checklist

- [x] pyusb installed for user (already done)
- [x] libusb installed (already done)
- [ ] **pyusb installed for sudo** ← You need this now
- [ ] Run capture script
- [ ] Analyze captured data
- [ ] Update driver code
- [ ] Create Xcode project
- [ ] Build driver
- [ ] Test driver

## 🎯 Your Current Step

**Step 3 of 8:** Install pyusb for system-wide access

Run this command:
```bash
sudo python3 -m pip install --break-system-packages pyusb
```

Then proceed to run the capture tool.

## 📚 File Guide

| File | Purpose |
|------|---------|
| `FIX_PYUSB.md` | Detailed fix for pyusb sudo issue |
| `NEXT_STEPS.md` | What to do after fixing pyusb |
| `QUICKSTART.md` | Complete getting started guide |
| `README.md` | Full technical documentation |
| `capture_hid_descriptor.py` | USB analysis tool (needs sudo) |
| `check_system.sh` | Verify system is ready |

## 🔧 Useful Commands

```bash
# Check system readiness
./check_system.sh

# Fix pyusb for sudo
sudo python3 -m pip install --break-system-packages pyusb

# Capture device data (main task)
sudo python3 capture_hid_descriptor.py

# Check if device is connected
ioreg -p IOUSB -w0 -l | grep -i hori

# Get basic device info
./get_device_info.sh
```

## 🎮 When Capturing Data

The script will ask if you want to capture reports. Say **yes** and then:

1. ✅ Turn wheel fully left
2. ✅ Turn wheel fully right
3. ✅ Center the wheel
4. ✅ Press accelerator pedal fully
5. ✅ Press brake pedal fully
6. ✅ Press each button
7. ✅ Move through all D-pad positions

This helps identify which bytes represent which inputs!

## ⏭️ After Capturing

1. Look at `hid_descriptor.c` - this is the device's descriptor
2. Review the captured reports to see patterns
3. Update `HORIRacingWheelDriver.cpp`:
   - Replace `reportDescriptor` in `newReportDescriptor()`
   - Implement byte parsing in `ParseWheelData()`
4. Build in Xcode
5. Install and test!

## 🆘 Getting Stuck?

### Can't install pyusb?
See `FIX_PYUSB.md`

### Script fails to find device?
```bash
ioreg -p IOUSB -w0 -l | grep -i hori
```
Make sure you see the device listed.

### No HID descriptor found?
This is expected - the device uses vendor-specific protocol.
Focus on analyzing the raw input reports instead.

### Need to understand the driver code?
Read `README.md` sections on:
- Architecture
- Known Limitations
- Customization Needed

## 📞 Support Files

- **Setup Issues**: `FIX_PYUSB.md`
- **Next Actions**: `NEXT_STEPS.md`
- **Step-by-Step**: `QUICKSTART.md`
- **Technical Details**: `README.md`
- **Project Overview**: `PROJECT_STATUS.md`

---

## Right Now, Do This:

```bash
sudo python3 -m pip install --break-system-packages pyusb
sudo python3 capture_hid_descriptor.py
```

That's it! 🚀
