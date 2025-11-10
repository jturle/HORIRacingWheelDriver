# HORI Racing Wheel - Testing Guide

## 🧪 Real-time Input Tester

The `test_wheel.py` tool lets you verify all wheel inputs before building the full driver.

## 🚀 Quick Start

```bash
sudo python3 test_wheel.py
```

That's it! The tool will:
1. Connect to your HORI Racing Wheel
2. Display a live dashboard of all inputs
3. Update in real-time as you use the controls

## 📺 What You'll See

```
================================================================================
  HORI Racing Wheel - Real-time Input Tester
================================================================================

  STEERING WHEEL
  =====●=====
  Position        [████████████████████            ] 128/255 ( 50%)

  PEDALS
  Accelerator     [                                ]   0/255 (  0%)
  Brake           [                                ]   0/255 (  0%)
  Clutch          [                                ]   0/255 (  0%)

  D-PAD
  Direction:   ●   (Neutral)

  BUTTONS
   B 1    B 2    B 3    B 4    B 5
   B 6    B 7    B 8    B 9    B10
   B11   B12   B13

  RAW VALUES
  Steering: 0x80 (128)
  Accel:    0x00 (  0)
  Brake:    0x00 (  0)
  Clutch:   0x00 (  0)
  Buttons:  0x0000 (binary: 0000000000000)
  D-pad:    8

────────────────────────────────────────────────────────────────────────────────
  Press Ctrl+C to exit
```

## 🎮 Testing Checklist

### Steering Wheel
- [ ] Turn **full left** → Position should show ~0/255 (0%)
  - Visual: `<<<<<=========`
  - Raw: 0x00
- [ ] Turn to **center** → Position should show ~128/255 (50%)
  - Visual: `=====●=====`
  - Raw: 0x80
- [ ] Turn **full right** → Position should show ~255/255 (100%)
  - Visual: `=========>>>>>`
  - Raw: 0xFF

### Pedals
Test each pedal separately:

**Accelerator (Y axis)**
- [ ] Not pressed → 0/255 (0%)
- [ ] Half pressed → ~128/255 (50%)
- [ ] Fully pressed → ~255/255 (100%)

**Brake (Z axis)**
- [ ] Not pressed → 0/255 (0%)
- [ ] Half pressed → ~128/255 (50%)
- [ ] Fully pressed → ~255/255 (100%)

**Clutch (Rz axis)** - if your wheel has one
- [ ] Not pressed → 0/255 (0%)
- [ ] Half pressed → ~128/255 (50%)
- [ ] Fully pressed → ~255/255 (100%)

### D-Pad
Test all 8 directions plus neutral:

- [ ] **Up (North)** → Arrow: ↑, Value: 0
- [ ] **Up-Right (NE)** → Arrow: ↗, Value: 1
- [ ] **Right (East)** → Arrow: →, Value: 2
- [ ] **Down-Right (SE)** → Arrow: ↘, Value: 3
- [ ] **Down (South)** → Arrow: ↓, Value: 4
- [ ] **Down-Left (SW)** → Arrow: ↙, Value: 5
- [ ] **Left (West)** → Arrow: ←, Value: 6
- [ ] **Up-Left (NW)** → Arrow: ↖, Value: 7
- [ ] **Neutral (Center)** → Arrow: ●, Value: 8

### Buttons (13 total)
Press each button and verify it lights up **green**:

- [ ] Button 1 → B 1 lights up
- [ ] Button 2 → B 2 lights up
- [ ] Button 3 → B 3 lights up
- [ ] Button 4 → B 4 lights up
- [ ] Button 5 → B 5 lights up
- [ ] Button 6 → B 6 lights up
- [ ] Button 7 → B 7 lights up
- [ ] Button 8 → B 8 lights up
- [ ] Button 9 → B 9 lights up
- [ ] Button 10 → B10 lights up
- [ ] Button 11 → B11 lights up
- [ ] Button 12 → B12 lights up
- [ ] Button 13 → B13 lights up

### Combination Tests
- [ ] Press multiple buttons simultaneously → All light up
- [ ] Turn wheel while pressing accelerator → Both update
- [ ] Press brake while pressing buttons → All update

## 🎨 Visual Indicators

### Steering Wheel
```
Full Left:   <<<<<=========   (Red arrows pointing left)
Center:      =====●=====       (Green center dot)
Full Right:  =========>>>>>   (Red arrows pointing right)
```

### Progress Bars
- **Blue**: 0-50%
- **Yellow**: 50-80%
- **Green**: 80-100%

### Buttons
- **Black background**: Not pressed
- **Green background**: Pressed

### D-Pad
- **Green arrow**: Active direction
- **Cyan dot**: Neutral/centered

## 🐛 Troubleshooting

### "Must be run with sudo"
```bash
sudo python3 test_wheel.py
```

### "pyusb not installed"
```bash
sudo python3 -m pip install --break-system-packages pyusb
```

### "Device not found"
```bash
# Check if device is connected
ioreg -p IOUSB -w0 -l | grep -i hori

# Unplug and replug the wheel
```

### Display is flickering
This is normal - the tool updates rapidly to show real-time changes.

### Values seem wrong

**Steering centered but showing wrong value?**
- Some wheels may center at a slightly different value (127-129)
- As long as it's consistent, this is fine

**Pedals not reaching 255?**
- Some pedals may max out at 250-254
- This is normal mechanical variation

**Buttons numbered differently?**
- The button numbers (1-13) are the HID button IDs
- They may not match the physical labels on your wheel
- Note which physical button maps to which number

## 📝 Recording Your Findings

Create a button mapping reference:

```
Physical Button    →  HID Button ID
─────────────────────────────────────
X                  →  B 1
A                  →  B 2
B                  →  B 3
Y                  →  B 4
LB                 →  B 5
RB                 →  B 6
...etc
```

## 🔧 Advanced Testing

### Test Rapid Inputs
1. Rapidly press buttons → All should register
2. Quickly move wheel left/right → Smooth transitions
3. Pump pedals quickly → Values should update

### Test Edge Cases
1. Press all buttons simultaneously → All light up
2. Max out all pedals at once → All show 100%
3. Hold button while moving wheel → Both update

### Test Consistency
1. Move wheel to same position multiple times → Same value
2. Press pedal to same depth → Consistent readings
3. Leave controls idle → Values stay at neutral

## ✅ Success Criteria

Your wheel is working correctly if:
- ✅ All 13 buttons register when pressed
- ✅ Steering moves smoothly from 0 to 255
- ✅ Accelerator goes from 0 to ~255
- ✅ Brake goes from 0 to ~255
- ✅ Clutch responds (if equipped)
- ✅ D-pad works in all 8 directions
- ✅ No unexpected values or jumps
- ✅ Values are stable when controls are idle

## 🎯 Next Steps

Once you've verified all inputs work correctly:

1. **Note any button mapping differences**
   - Document which physical button = which HID ID

2. **Check for any calibration issues**
   - Is steering centered at 0x80?
   - Do pedals reach full range?

3. **Proceed to build the driver**
   - Follow `BUILD_INSTRUCTIONS.md`
   - The driver will use the same mapping

## 💡 Tips

- **Test methodically**: Check one control at a time
- **Look at raw values**: These show exact byte values the driver will see
- **Leave it running**: Monitor for any drift or instability
- **Test combinations**: Make sure multiple inputs work together

## 🚪 Exiting

Press **Ctrl+C** to exit the tool cleanly.

---

## Quick Command Reference

```bash
# Run the tester
sudo python3 test_wheel.py

# If you get errors, first verify device is connected
ioreg -p IOUSB -w0 -l | grep -i hori

# Install pyusb if needed
sudo python3 -m pip install --break-system-packages pyusb
```

**Enjoy testing your racing wheel!** 🏎️
