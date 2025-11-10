# Control Mapping Tool - Summary

## 🎯 Why You Need This

The initial HID descriptor analysis assumed certain byte positions, but you noticed the **axes aren't properly configured**. This tool helps you discover the **actual byte positions** by detecting changes as you move controls.

## Key Discoveries You'll Make

### 1. Full 64-Byte Reports
The tool reads the **entire 64-byte USB report**, not just the first 7-18 bytes. This means:
- ✅ You'll see if "padding" bits are actually used
- ✅ You'll discover any hidden data in bytes 7-63
- ✅ You'll find the true report structure

### 2. Actual Control Positions
Instead of assuming based on HID descriptor, you'll know:
- Which exact byte contains steering
- Which bytes contain each pedal
- Which bit corresponds to each button
- Whether D-pad uses the expected 4-bit encoding

### 3. Bit-Level Analysis
For each control, the tool shows:
- Byte index
- Range of values seen
- Whether it's analog (0-255) or digital (bit)
- Bit-by-bit breakdown

## 🚀 How To Use It

### Quick Start
```bash
make map
```

Or directly:
```bash
sudo python3 map_controls.py
```

### Workflow

1. **Capture Baseline**
   - Put all controls in neutral
   - Steering centered
   - Pedals released
   - No buttons pressed

2. **Map Each Control**
   - Select control from menu
   - Press ENTER to start 5-second monitoring
   - Move ONLY that control
   - Tool detects which bytes changed

3. **Review Results**
   - See immediate analysis on screen
   - Results saved to `control_mapping.txt`
   - Update driver code with findings

## 📊 Example Output

### Steering Wheel
```
Byte 3: ANALOG
  Range: 0x00 - 0xFF (0 - 255)
  Unique values: 256
```
✓ Steering is definitely in byte 3, full 8-bit range

### Button 1
```
Byte 0: BUTTON/BIT
  Range: 0x00 - 0x01 (0 - 1)
  Unique values: 2
  Values seen: 0x00, 0x01
  Bit analysis:
    Bit 0: ACTIVE (values: [0, 1])
```
✓ Button 1 is bit 0 of byte 0

### D-Pad
```
Byte 2: MULTI-BIT
  Range: 0x00 - 0x08 (0 - 8)
  Unique values: 9
  Bit analysis:
    Bit 0: ACTIVE
    Bit 1: ACTIVE
    Bit 2: ACTIVE
    Bit 3: ACTIVE
```
✓ D-pad uses bits 0-3 of byte 2 (4-bit field)

### Mystery Data?
```
Byte 17: ANALOG
  Range: 0x00 - 0x3F (0 - 63)
  Unique values: 64
```
❓ Found something in the "vendor data" area!

## 🔍 Live Comparison Mode

Press "Live Comparison Mode" to see all bytes in real-time:

```
Byte | Baseline | Current | Diff | Binary (Current)      | Binary (Baseline)
--------------------------------------------------------------------------------
   0 | 0x00   0 | 0x01   1 | +  1 | 00000001 | 00000000  ← Button pressed!
   3 | 0x80 128 | 0xFF 255 | +127 | 11111111 | 10000000  ← Wheel turned right
  17 | 0x00   0 | 0x2A  42 | + 42 | 00101010 | 00000000  ← What's this?
```

Great for:
- Seeing everything at once
- Finding unexpected data
- Understanding bit patterns
- Verifying multiple controls work together

## 📝 What You'll Discover

### Expected Findings
- Steering wheel position byte
- Accelerator, brake, clutch bytes
- Button bits (probably bytes 0-1)
- D-pad encoding (probably byte 2)

### Unexpected Findings
- **Padding bits might be used!**
  - Bits marked as "padding" may actually contain data
  - Check all bits 0-7 in each byte

- **Extended precision?**
  - Steering might use 10-16 bits across multiple bytes
  - Pedals might have higher resolution

- **Hidden data in bytes 7-63**
  - Force feedback status
  - Device temperature
  - Battery level (if wireless capable)
  - Extended sensor data

- **Button layout differences**
  - Physical button labels may not match HID button IDs
  - Some buttons might be multi-bit encoded

## 🔧 Using Results to Fix Driver

After mapping, you'll have a file `control_mapping.txt` like:

```
Control: Steering Wheel
Byte  3: ANALOG | Range: 0x00-0xFF | Span: 255

Control: Accelerator Pedal
Byte  4: ANALOG | Range: 0x00-0xFF | Span: 255

Control: Button 1
Byte  0: BUTTON/BIT | Range: 0x00-0x01 | Span: 1
```

### Update Driver Code

Edit `HORIRacingWheelDriver.cpp`, function `ParseWheelData()`:

```cpp
void HORIRacingWheelDriver::ParseWheelData(uint8_t *report, uint32_t reportLength)
{
    // Update based on actual findings:
    uint8_t steering = report[3];   // Confirmed from mapping
    uint8_t accel = report[4];      // Confirmed from mapping
    uint8_t brake = report[5];      // Confirmed from mapping

    // Buttons - update based on actual bits
    uint16_t buttons = report[0] | (report[1] << 8);

    // etc...
}
```

### Update HID Descriptor (if needed)

If bytes don't match the descriptor, you have two options:

1. **Update descriptor** to match hardware
2. **Keep descriptor, adjust parsing** to work around it

## 💡 Pro Tips

### Test Systematically
1. Map all analog controls first (axes have larger ranges)
2. Then map buttons one at a time
3. Finally map D-pad
4. Use live mode to see everything together

### Look for Patterns
- Buttons usually cluster in consecutive bits
- Axes usually get their own byte(s)
- Multi-byte values are usually little-endian

### Document Everything
- Note which physical button = which bit
- Record any unexpected findings
- Take screenshots of interesting patterns

### Verify Findings
After mapping:
1. Use `test_wheel.py` to see if values make sense
2. Test combinations (multiple buttons, wheel + pedals)
3. Check for consistency across multiple runs

## 🎯 Common Scenarios

### "Steering wheel doesn't center at 0x80"
- Map "Center to Left" and "Center to Right" separately
- Find actual center value
- Update driver code

### "Some buttons don't register"
- They might be in unexpected bytes
- Check bits 0-7 in multiple bytes
- Try pressing harder (mechanical issue?)

### "Pedals have limited range"
- They might not reach 0x00 or 0xFF
- Note actual min/max values
- Update driver to scale appropriately

### "D-pad doesn't use 0-8 encoding"
- It might use different encoding
- Could be 4 separate bits (N, E, S, W)
- Map each direction to find pattern

## 📈 Expected Timeline

- **Setup and baseline**: 2 minutes
- **Map steering and pedals**: 5 minutes
- **Map all 13 buttons**: 10-15 minutes
- **Map D-pad**: 3 minutes
- **Explore with live mode**: 5-10 minutes
- **Total**: ~30 minutes

## 🎓 Understanding the Data

### Byte
A byte is 8 bits, can hold 0-255 (0x00-0xFF)

### Bit
A single binary digit (0 or 1), used for buttons

### Analog vs Digital
- **Analog**: Range of values (0-255), used for axes
- **Digital**: On/off (0 or 1), used for buttons

### Little-Endian
Multi-byte values store least significant byte first:
```
Value 0x1234 stored as:
  Byte 0: 0x34
  Byte 1: 0x12
```

## 🚀 Next Steps After Mapping

1. **Review `control_mapping.txt`**
2. **Update `HORIRacingWheelDriver.cpp`** with actual byte positions
3. **Rebuild driver** with corrected parsing
4. **Test with `test_wheel.py`** to verify
5. **Install and use in games!**

---

## Quick Commands

```bash
# Run the mapper
make map

# Or directly
sudo python3 map_controls.py

# After mapping, view results
cat control_mapping.txt

# Test with corrected understanding
make test
```

This tool will give you **ground truth** about your device's protocol! 🔍
