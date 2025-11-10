# HORI Racing Wheel Driver - Build Instructions

## 🎉 You're Ready to Build!

The driver now contains the **actual HID descriptor** from your device and **proper report parsing**. All the reverse engineering is complete!

## 📋 Prerequisites Checklist

- [x] macOS 11.0+ (you have macOS 26.1)
- [x] Xcode 12+ (you have Xcode 26.1)
- [x] Device analyzed (1,251 reports captured)
- [x] HID descriptor integrated
- [x] Report parsing implemented
- [ ] Apple Developer account (free or paid)
- [ ] Code signing certificate

## 🏗️ Build Steps

### Step 1: Create Xcode Project

1. Open **Xcode**
2. File → New → Project...
3. Choose **macOS** → **System Extension**
4. Configure:
   - **Product Name**: `HORIRacingWheelDriver`
   - **Team**: Select your Apple Developer team
   - **Organization Identifier**: `com.yourname` (replace with yours)
   - **Bundle Identifier**: `com.yourname.HORIRacingWheelDriver`
   - **Language**: C++
5. Choose location: `/Users/james/projects/hori/`
6. Click **Create**

### Step 2: Add Source Files to Project

In Xcode:

1. **Delete** the template files that Xcode created
2. **Add** your files to the project:
   - Right-click project → Add Files to "HORIRacingWheelDriver"...
   - Select:
     - `HORIRacingWheelDriver.iig`
     - `HORIRacingWheelDriver.cpp`
     - `Info.plist`
     - `HORIRacingWheelDriver.entitlements`
   - ✅ Check "Copy items if needed"
   - ✅ Check "Add to targets"

### Step 3: Configure Build Settings

#### General Tab
- **Deployment Target**: macOS 11.0 or later
- **Signing**: Automatic signing enabled

#### Signing & Capabilities Tab
1. **Automatically manage signing**: ✅ Enabled
2. **Team**: Select your team
3. **Entitlements File**: `HORIRacingWheelDriver.entitlements`

#### Build Settings Tab
Search and set:
- **Code Signing Entitlements**: `HORIRacingWheelDriver.entitlements`
- **Product Bundle Identifier**: Update to match your bundle ID

#### Info.plist Configuration

Open `Info.plist` in Xcode and replace placeholder values:

```xml
<!-- Find and replace -->
$(PRODUCT_BUNDLE_IDENTIFIER)
<!-- with your actual bundle ID, e.g., -->
com.yourname.HORIRacingWheelDriver
```

Update the IOKit personality:
```xml
<key>CFBundleIdentifier</key>
<string>com.yourname.HORIRacingWheelDriver</string>
```

### Step 4: Build the Driver

1. Select your Mac as the build destination
2. Product → Build (⌘B)
3. Wait for build to complete

**Build Output Location**:
```
~/Library/Developer/Xcode/DerivedData/HORIRacingWheelDriver-*/Build/Products/Debug/
```

Look for: `HORIRacingWheelDriver.dext`

### Step 5: Handle Build Errors (If Any)

Common issues:

#### "No matching provisioning profile found"
- Check that automatic signing is enabled
- Verify your team is selected
- Try Product → Clean Build Folder (Shift+⌘K), then rebuild

#### "Missing entitlements"
- Verify `HORIRacingWheelDriver.entitlements` is in the project
- Check Build Settings → Code Signing Entitlements points to it

#### "IIG file not found"
- Make sure `HORIRacingWheelDriver.iig` is in project
- Check it's added to the correct target

## 🚀 Installation

### Prepare Your System

⚠️ **Warning**: These steps reduce system security. Only do this on a development machine.

1. **Disable SIP** (System Integrity Protection):
   ```bash
   # Reboot into Recovery Mode:
   # Shut down, hold Power button, select Options
   # OR hold Command+R during Intel Mac boot

   # In Recovery Terminal:
   csrutil disable
   csrutil authenticated-root disable

   # Reboot normally
   ```

2. **Enable development mode**:
   ```bash
   sudo systemextensionsctl developer on
   ```

### Install the Driver

```bash
# Navigate to build output
cd ~/Library/Developer/Xcode/DerivedData/HORIRacingWheelDriver-*/Build/Products/Debug/

# Copy to system extensions directory
sudo cp -r HORIRacingWheelDriver.dext /Library/SystemExtensions/

# Load the driver
sudo kmutil load -p /Library/SystemExtensions/HORIRacingWheelDriver.dext
```

### Verify Installation

```bash
# Check if driver is loaded
sudo kmutil showloaded | grep -i hori

# Check for driver logs
log stream --predicate 'eventMessage contains "HORIRacingWheelDriver"' --level debug
```

Expected output in logs:
```
HORIRacingWheelDriver: init successful
HORIRacingWheelDriver: Start called
HORIRacingWheelDriver: Found interrupt IN pipe at address 0x81
HORIRacingWheelDriver: Successfully started
```

## 🧪 Testing

### Monitor Driver Activity

In one terminal, stream logs:
```bash
log stream --predicate 'eventMessage contains "HORIRacingWheelDriver"' --level debug
```

In another terminal, check device:
```bash
ioreg -l -w0 | grep -i hori -A 20
```

### Test Inputs

The driver logs every 100th report. Move the controls and watch for:
```
HORIRacingWheelDriver: Wheel: 0x80, Accel: 0x00, Brake: 0x00, Clutch: 0x00, Buttons: 0x0000, D-pad: 8
HORIRacingWheelDriver: Wheel: 0xFF, Accel: 0xFF, Brake: 0xFF, Clutch: 0x00, Buttons: 0x0001, D-pad: 0
```

### Test with Applications

1. **System Settings** → Game Controllers (if available)
2. **Enjoyable** ([download](https://yukkurigames.com/enjoyable/))
3. **Joystick Show** (Mac App Store)
4. **Steam** with Big Picture mode
5. **Racing games** that support controllers

### Expected Behavior

- ✅ Wheel appears as "HORI Racing Wheel Switch"
- ✅ Steering axis moves left/right
- ✅ Pedals register pressure
- ✅ All 13 buttons work
- ✅ D-pad responds in all 8 directions

## 🐛 Troubleshooting

### Driver won't load

```bash
# Check for errors
log show --last 5m --predicate 'eventMessage contains "HORIRacingWheelDriver"'

# Verify file permissions
ls -l /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Try unloading and reloading
sudo kmutil unload -p /Library/SystemExtensions/HORIRacingWheelDriver.dext
sudo kmutil load -p /Library/SystemExtensions/HORIRacingWheelDriver.dext
```

### Device not responding

```bash
# Unplug and replug the wheel
# Check USB connection
ioreg -p IOUSB -w0 -l | grep -i hori

# Restart the driver
sudo kmutil unload -p /Library/SystemExtensions/HORIRacingWheelDriver.dext
sudo kmutil load -p /Library/SystemExtensions/HORIRacingWheelDriver.dext
```

### Build failures

```bash
# Clean build
# In Xcode: Product → Clean Build Folder (Shift+⌘K)

# Check Xcode command line tools
xcode-select --print-path
xcode-select --install

# Verify SDK
xcodebuild -showsdks
```

### System crashes

If the system becomes unstable:

1. **Unload the driver immediately**:
   ```bash
   sudo kmutil unload -p /Library/SystemExtensions/HORIRacingWheelDriver.dext
   ```

2. **Review logs** for kernel panics:
   ```bash
   log show --predicate 'messageType == 17' --last 1h
   ```

3. **Remove the driver**:
   ```bash
   sudo rm -rf /Library/SystemExtensions/HORIRacingWheelDriver.dext
   ```

## 🎮 Game Testing

### Recommended Test Games

- **GRID Autosport** (Mac)
- **DiRT Rally** (Mac)
- **F1 2019** (Mac)
- **Assetto Corsa** (via Steam)
- **Any Steam game** with controller support

### Configuration

Most games will auto-detect the wheel. You may need to:
1. Go to game settings → Controls
2. Select "HORI Racing Wheel" or "Game Pad"
3. Map steering axis to X
4. Map accelerator to Y
5. Map brake to Z
6. Calibrate if needed

## 📊 Performance Tuning

### Reduce Log Spam

Edit `HORIRacingWheelDriver.cpp`, line 305:
```cpp
// Change from logging every 100 reports to every 1000
if ((logCounter++ % 1000) == 0) {
```

Or disable completely:
```cpp
// Comment out the entire logging section
// if ((logCounter++ % 100) == 0) { ... }
```

Rebuild after changes.

### Adjust Report Buffer Size

If you experience dropped inputs, increase buffer size in line 156:
```cpp
// Change from 64 to 128 bytes
ret = IOBufferMemoryDescriptor::Create(kIOMemoryDirectionIn, 128, 0, &ivars->reportBuffer);
```

## 🎯 Success Metrics

You'll know it's working when:
- ✅ Driver loads without errors
- ✅ Logs show "Successfully started"
- ✅ Wheel movements appear in logs
- ✅ Games detect the controller
- ✅ All inputs respond correctly
- ✅ No system instability

## 🔄 Uninstalling

```bash
# Unload driver
sudo kmutil unload -p /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Remove files
sudo rm -rf /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Re-enable SIP (recommended)
# Reboot to Recovery Mode, then:
csrutil enable
csrutil authenticated-root enable
# Reboot
```

## 📦 Distribution (Future)

To share with others:

1. **Get a paid Developer account** (required for distribution)
2. **Code sign** with Developer ID certificate
3. **Notarize** with Apple
4. **Create installer** using `pkgbuild`
5. **Provide install instructions**

## 🎓 Learning Resources

- [DriverKit Documentation](https://developer.apple.com/documentation/driverkit)
- [IOUserHIDEventService](https://developer.apple.com/documentation/hiddriverkit/iouserhideventservice)
- [System Extensions](https://developer.apple.com/documentation/systemextensions)

---

## Quick Command Reference

```bash
# Build (in Xcode)
⌘B

# Install
sudo cp -r build/Debug/HORIRacingWheelDriver.dext /Library/SystemExtensions/
sudo kmutil load -p /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Monitor
log stream --predicate 'eventMessage contains "HORIRacingWheelDriver"' --level debug

# Unload
sudo kmutil unload -p /Library/SystemExtensions/HORIRacingWheelDriver.dext

# Remove
sudo rm -rf /Library/SystemExtensions/HORIRacingWheelDriver.dext
```

**Good luck! You're ready to build your racing wheel driver!** 🏁🎮
