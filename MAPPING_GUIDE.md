# Interactive Control Mapping Guide

## 🎯 Purpose

The `map_controls.py` tool helps you discover the **exact byte positions** for each control by detecting which bytes change when you move specific controls.

This is essential because:
- The HID descriptor may not be accurate
- Padding bits might actually be used
- Button assignments may differ from the descriptor
- You can verify the actual data format

## 🚀 Usage

```bash
sudo python3 map_controls.py
```

## 📋 How It Works

### 1. Capture Baseline
First, the tool captures a "baseline" report with all controls in neutral position:
- Steering wheel centered
- All pedals released
- No buttons pressed
- D-pad neutral

### 2. Map Each Control
For each control you select:
1. Keep everything else in neutral
2. Press ENTER to start 5-second monitoring
3. **Move ONLY that control** during monitoring
4. Tool detects which bytes changed

### 3. Analyze Results
The tool shows:
- Which bytes changed
- The range of values (min to max)
- Whether it's a button (bit) or analog (range)
- Bit-level analysis for multi-bit fields

## 🎮 Recommended Mapping Order

### Start with Analog Controls

1. **Steering Wheel (Full Left to Full Right)**
   - Turn wheel all the way left
   - Sweep smoothly to all the way right
   - Shows full range

2. **Accelerator Pedal**
   - Start: not pressed
   - End: fully pressed
   - Shows full range

3. **Brake Pedal**
   - Start: not pressed
   - End: fully pressed

4. **Clutch Pedal** (if equipped)
   - Start: not pressed
   - End: fully pressed

### Then Buttons (One at a Time!)

5-17. **Each Button (1-13)**
   - Press and hold one button
   - Release before 5 seconds ends
   - Or: press and release multiple times

### Finally D-Pad

18-21. **D-Pad Directions**
   - Hold each direction firmly
   - Try diagonals too if available

## 📊 Understanding Results

### Analog Control Example
```
Byte 3: ANALOG
  Range: 0x00 - 0xFF (0 - 255)
  Unique values: 256
```
This is a full 8-bit axis (like steering or pedal).

### Button Example
```
Byte 0: BUTTON/BIT
  Range: 0x00 - 0x01 (0 - 1)
  Unique values: 2
  Values seen: 0x00, 0x01
  Bit analysis:
    Bit 0: ACTIVE (values: [0, 1])
```
This is a single button on bit 0 of byte 0.

### Multi-Bit Field Example
```
Byte 2: MULTI-BIT
  Range: 0x00 - 0x08 (0 - 8)
  Unique values: 9
  Values seen: 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
  Bit analysis:
    Bit 0: ACTIVE
    Bit 1: ACTIVE
    Bit 2: ACTIVE
    Bit 3: ACTIVE
```
This is a 4-bit field (like D-pad, uses bits 0-3).

## 💡 Pro Tips

### For Steering Wheel
- Map it multiple times:
  1. Full left to full right (full range)
  2. Center to left only (verify center point)
  3. Center to right only (verify center point)
- This helps identify if there's any asymmetry

### For Buttons
- Press each button **individually**
- Don't press multiple buttons simultaneously (yet)
- If a button doesn't register, try pressing harder
- Note which physical button corresponds to which byte/bit

### For D-Pad
- Hold each direction for the full 5 seconds
- Try corner directions (NE, SE, SW, NW) separately
- See if they map to multiple bits or a single multi-bit value

### For Pedals
- Move slowly and smoothly from 0% to 100%
- This shows if there are any dead zones
- Helps verify full range is achievable

## 🔬 Live Comparison Mode

Select "Live Comparison Mode" to see real-time byte changes:

```
Byte | Baseline | Current | Diff | Binary (Current)      | Binary (Baseline)
--------------------------------------------------------------------------------
   0 | 0x00   0 | 0x01   1 | +  1 | 00000001 | 00000000
   1 | 0x00   0 | 0x00   0 |   0  | 00000000 | 00000000
   2 | 0x08   8 | 0x00   0 | -  8 | 00000000 | 00001000
   3 | 0x80 128 | 0xFF 255 | +127 | 11111111 | 10000000
```

This is great for:
- Seeing all changes at once
- Understanding bit patterns
- Finding "hidden" data in padding bytes
- Verifying baseline is correct

## 📝 Output File

Results are saved to `control_mapping.txt`:

```
================================================================================
Control: Steering Wheel (Full Left to Full Right)
Samples: 98
================================================================================
Byte  3: ANALOG     | Range: 0x00-0xFF (  0-255) | Span: 255

================================================================================
Control: Button 1
Samples: 95
================================================================================
Byte  0: BUTTON/BIT | Range: 0x00-0x01 (  0-  1) | Span:   1
```

Use this to update the driver code with actual byte positions!

## 🐛 Troubleshooting

### "No changes detected"
- Make sure you moved the control during the 5 seconds
- Try moving it more (larger range)
- Verify the control actually works (use test_wheel.py)

### Multiple bytes changing
- This is normal! Buttons may span multiple bytes
- Note all bytes that changed
- The tool shows bit analysis to help identify patterns

### Values seem wrong
- Re-capture baseline (select "Re-capture Baseline")
- Make sure nothing is moving during baseline capture
- Physically inspect that wheel/pedals are truly neutral

### Unexpected padding bytes active
- This is a discovery! Those "padding" bits are actually used
- Note which bits change
- Update the driver accordingly

## 🎯 Example Session

```bash
$ sudo python3 map_controls.py

# 1. Capture baseline (all controls neutral)
Press ENTER when ready...

# 2. Select "1. Steering Wheel (Full Left to Full Right)"
Enter number: 1

# 3. Move steering wheel during 5-second window
MOVE THE CONTROL NOW!

# Result shows:
Byte 3: ANALOG
  Range: 0x00 - 0xFF (0 - 255)
  ✓ This is the steering axis!

# 4. Continue with other controls...

# 5. When done, review control_mapping.txt
```

## 🔧 What To Do With Results

After mapping all controls:

1. **Review `control_mapping.txt`**
   - Note byte positions for each control
   - Compare with HID descriptor assumptions

2. **Update Driver Code**
   - Edit `HORIRacingWheelDriver.cpp`
   - Update `ParseWheelData()` function
   - Use actual byte positions discovered

3. **Update HID Descriptor** (if needed)
   - If bytes don't match descriptor, update it
   - Or adjust parsing to match actual format

4. **Test Again**
   - Rebuild driver
   - Verify all inputs work correctly

## 📈 Expected Findings

You'll likely discover:
- ✅ Steering wheel is in byte 3 (or different?)
- ✅ Pedals are in bytes 4-6 (or different?)
- ✅ Buttons span bytes 0-1 (or more?)
- ✅ D-pad is in byte 2, bits 0-3 (or different?)
- ⚠️ **"Padding" bits might actually be used!**
- ⚠️ **Report might be larger than 7 bytes**
- ⚠️ **Bytes 7-18 might contain useful data**

## 🎓 Understanding Bytes vs Bits

### Byte Numbering
- Byte 0 = first byte
- Byte 1 = second byte
- etc.

### Bit Numbering (within a byte)
- Bit 0 = rightmost bit (LSB)
- Bit 7 = leftmost bit (MSB)

### Example: Button in byte 0, bit 0
```
Byte 0: 0 0 0 0 0 0 0 1
Bit:    7 6 5 4 3 2 1 0
                      ^-- Bit 0 is ON (button pressed)
```

## 🚀 Quick Start

```bash
# Run the mapper
sudo python3 map_controls.py

# Map these in order:
1. Steering wheel (full range)
2. Accelerator
3. Brake
4. All 13 buttons (one at a time!)
5. D-pad directions

# Review results
cat control_mapping.txt

# Update driver code with findings
# Build and test!
```

---

**This tool reads the full 64-byte USB report**, so you'll see ALL data including any "padding" that's actually used!
