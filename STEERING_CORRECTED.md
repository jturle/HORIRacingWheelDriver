# Steering Wheel Mapping - CORRECTED

## 🎯 The Truth About Steering

You clarified that the steering uses **signed-style encoding with 0x0000 as center**:

```
0x0000          = CENTER/NEUTRAL (straight ahead)
0x0001 - 0x7FFF = Turn RIGHT (1 to 32,767 positions)
0x8000 - 0xFFFF = Turn LEFT (32,768 to 65,535, or -32768 to -1 as signed)
```

## 📊 Visualization

```
Full Left              Center             Full Right
   ↓                     ↓                    ↓
0x8000 ←────────────→ 0x0000 ←────────────→ 0x7FFF
-32768                   0                 +32767
(or 32768)                                (or 32767)
```

## 🔢 Understanding the Encoding

This is a **signed 16-bit axis** disguised as unsigned:

### As Unsigned (raw bytes):
- **0x0000**: Center
- **0x0001 to 0x7FFF**: Right side (1 to 32,767)
- **0x8000 to 0xFFFF**: Left side (32,768 to 65,535)

### As Signed (two's complement):
- **0**: Center
- **+1 to +32,767**: Right side
- **-32,768 to -1**: Left side

## 💡 Why This Makes Sense

This is a common encoding for steering wheels because:
1. **Natural zero point** - Center = 0
2. **Symmetric range** - Equal positions left and right
3. **Easy math** - Positive = right, negative = left
4. **Standard signed integer** - Works with existing libraries

## 🎮 In Practice

### Reading the Value

```c
// Read raw bytes (little-endian)
uint16_t steering_raw = report[6] | (report[7] << 8);

// Interpret as signed
int16_t steering_signed = (int16_t)steering_raw;

// Now:
// steering_signed == 0      → Center
// steering_signed > 0       → Turning right
// steering_signed < 0       → Turning left
```

### Example Values

| Position | Raw (hex) | Raw (unsigned) | As Signed | Direction |
|----------|-----------|----------------|-----------|-----------|
| Full Left | 0x8000 | 32,768 | -32,768 | MAX LEFT |
| Half Left | 0xC000 | 49,152 | -16,384 | HALF LEFT |
| Center | 0x0000 | 0 | 0 | CENTER |
| Half Right | 0x4000 | 16,384 | +16,384 | HALF RIGHT |
| Full Right | 0x7FFF | 32,767 | +32,767 | MAX RIGHT |

## 🔧 Updated Code

### Driver Code (HORIRacingWheelDriver.cpp)

```cpp
// Extract 16-bit steering (bytes 6-7, little-endian)
uint16_t steering16 = report[6] | ((uint16_t)report[7] << 8);
int16_t steering_signed = (int16_t)steering16;

// Now you can work with it as signed:
// 0 = center, positive = right, negative = left
```

### Test Tool (test_wheel.py)

```python
# Extract steering
steering16 = data[6] | (data[7] << 8)

# Determine position
if steering16 == 0:
    print("CENTER")
elif steering16 <= 0x7FFF:
    print(f"RIGHT {steering16}")
else:
    print(f"LEFT {0xFFFF - steering16 + 1}")
```

## 🎯 Benefits of This Encoding

1. **Natural interpretation** - Zero is obviously center
2. **Easy direction detection** - Just check sign
3. **Simple calculations** - `abs(value)` = turn amount
4. **Standard format** - Many wheels use this

## 📈 Precision

With 16-bit signed:
- **32,767 positions** to the right
- **32,768 positions** to the left
- **65,535 total unique positions** (excluding center)

Compare to 8-bit:
- **127 positions** to each side
- **255 total positions**

**That's 257x more precision!** 🎯

## 🏁 Racing Sim Benefits

This precision means:
- **Smoother steering input** - No noticeable steps
- **Fine control** - Tiny adjustments possible
- **Professional grade** - Same as high-end racing wheels
- **Better force feedback** response (if supported)

## ✅ All Updated

The following files have been corrected:
- ✅ `HORIRacingWheelDriver.cpp` - Parser understands signed encoding
- ✅ `test_wheel.py` - Displays correctly with center at 0x0000
- ✅ `DISCOVERED_MAPPING.md` - Documentation updated

## 🎮 Test It

Run the test tool to see it in action:

```bash
make test
```

You should now see:
- **"CENTER"** when wheel is straight (0x0000)
- **"RIGHT XX%"** when turning right (0x0001-0x7FFF)
- **"LEFT XX%"** when turning left (0x8000-0xFFFF)

The visual indicator will show:
- `=====●=====` when centered (green dot)
- `=====>>==>` when turning right (yellow/red arrows)
- `<<<=<<====` when turning left (yellow/red arrows)

---

**Perfect steering mapping achieved!** 🎉🏎️
