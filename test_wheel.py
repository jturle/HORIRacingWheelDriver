#!/usr/bin/env python3
"""
HORI Racing Wheel - Real-time Input Tester

This tool displays the current state of all wheel inputs in real-time.
Use this to verify button mappings and test all controls.

Usage:
    sudo python3 test_wheel.py

Controls:
    Ctrl+C to exit
"""

import sys
import time
import os

try:
    import usb.core
    import usb.util
except ImportError:
    print("Error: pyusb not installed")
    print("Install with: sudo python3 -m pip install --break-system-packages pyusb")
    sys.exit(1)

# HORI Racing Wheel USB IDs
VENDOR_ID = 0x0F0D
PRODUCT_ID = 0x013E

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_BLACK = '\033[40m'
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'

def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_at(row, col, text):
    """Print text at specific position."""
    print(f"\033[{row};{col}H{text}", end='', flush=True)

def draw_bar(value, max_value, width=40, label=""):
    """Draw a horizontal bar graph."""
    filled = int((value / max_value) * width)
    empty = width - filled

    # Color based on value
    if value > max_value * 0.8:
        color = Colors.GREEN
    elif value > max_value * 0.5:
        color = Colors.YELLOW
    else:
        color = Colors.BLUE

    bar = f"{color}{'█' * filled}{Colors.RESET}{'░' * empty}"
    percentage = int((value / max_value) * 100)

    return f"{label:15s} [{bar}] {value:3d}/255 ({percentage:3d}%)"

def draw_wheel(value16):
    """Draw a visual representation of the steering wheel (16-bit value)."""
    # 0x0000 = center, 0x0001-0x7FFF = right, 0x8000-0xFFFF = left

    if value16 == 0:
        return f"====={Colors.GREEN}●{Colors.RESET}====="  # Center
    elif value16 <= 0x7FFF:
        # Turning right
        if value16 > 0x6000:
            return f"========={Colors.RED}>>>>>{Colors.RESET}"  # Far right
        else:
            return f"====={Colors.YELLOW}==>{Colors.RESET}=="  # Slight right
    else:
        # Turning left (0x8000-0xFFFF)
        if value16 >= 0xA000:
            return f"{Colors.RED}<<<<<{Colors.RESET}========="  # Far left
        else:
            return f"=={Colors.YELLOW}<=={Colors.RESET}====="  # Slight left

def draw_dpad(dpad_value):
    """Draw D-pad state visually."""
    # D-pad: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW, 8=neutral
    directions = {
        0: "  ↑  ",
        1: "  ↗  ",
        2: "  →  ",
        3: "  ↘  ",
        4: "  ↓  ",
        5: "  ↙  ",
        6: "  ←  ",
        7: "  ↖  ",
        8: "  ●  "
    }

    arrow = directions.get(dpad_value, "  ?  ")

    if dpad_value == 8:
        return f"{Colors.CYAN}{arrow}{Colors.RESET}"
    else:
        return f"{Colors.GREEN}{arrow}{Colors.RESET}"

def draw_buttons(buttons):
    """Draw button states."""
    lines = []

    # Display buttons in a grid
    for i in range(13):
        is_pressed = (buttons >> i) & 1

        if is_pressed:
            btn = f"{Colors.BG_GREEN}{Colors.BOLD} B{i+1:2d} {Colors.RESET}"
        else:
            btn = f"{Colors.BG_BLACK} B{i+1:2d} {Colors.RESET}"

        lines.append(btn)

    # Arrange in rows
    row1 = "  ".join(lines[0:5])
    row2 = "  ".join(lines[5:10])
    row3 = "  ".join(lines[10:13])

    return [row1, row2, row3]

def parse_report(data):
    """Parse HID report and extract values - CORRECTED BASED ON ACTUAL MAPPING."""
    if len(data) < 8:
        return None

    # Extract button state (TODO: actual button positions TBD)
    buttons = data[0] | (data[1] << 8)

    # Extract D-pad (individual bits, not 0-8 encoding)
    dpad_bits = data[2] & 0x0F
    # Convert to hat switch encoding
    if dpad_bits == 0x01: dpad = 0      # Up
    elif dpad_bits == 0x09: dpad = 1    # NE
    elif dpad_bits == 0x08: dpad = 2    # Right
    elif dpad_bits == 0x0A: dpad = 3    # SE
    elif dpad_bits == 0x02: dpad = 4    # Down
    elif dpad_bits == 0x06: dpad = 5    # SW
    elif dpad_bits == 0x04: dpad = 6    # Left
    elif dpad_bits == 0x05: dpad = 7    # NW
    else: dpad = 8  # Neutral

    # Extract axes - CORRECTED POSITIONS!
    brake = data[4]     # Byte 4: Brake
    accel = data[5]     # Byte 5: Accelerator

    # Extract 16-bit steering (bytes 6-7, little-endian)
    # 0x0000 = center, 0x0001-0x7FFF = right, 0x8000-0xFFFF = left
    steering16 = data[6] | (data[7] << 8)
    steering_signed = steering16 if steering16 < 32768 else steering16 - 65536  # Convert to signed

    # Extract shoulder buttons and plus/minus from byte 2 (upper 4 bits)
    btn_plus = (data[2] & 0x10) != 0     # Bit 4: + button
    btn_minus = (data[2] & 0x20) != 0    # Bit 5: - button
    btn_lsb = (data[2] & 0x40) != 0      # Bit 6: LSB (Left Shoulder Button)
    btn_rsb = (data[2] & 0x80) != 0      # Bit 7: RSB (Right Shoulder Button)

    # Extract paddle shifters and face buttons (byte 3)
    paddle_down = (data[3] & 0x01) != 0  # Bit 0: gear down (left paddle)
    paddle_up = (data[3] & 0x02) != 0    # Bit 1: gear up (right paddle)
    btn_home = (data[3] & 0x04) != 0     # Bit 2: home button
    # Bit 3 (0x08): unknown
    btn_a = (data[3] & 0x10) != 0        # Bit 4: A button
    btn_b = (data[3] & 0x20) != 0        # Bit 5: B button
    btn_x = (data[3] & 0x40) != 0        # Bit 6: X button
    btn_y = (data[3] & 0x80) != 0        # Bit 7: Y button

    # Detect ZL and ZR buttons (they overlay on the pedal axes)
    btn_zl = (brake == 0xFF)
    btn_zr = (accel == 0xFF)

    return {
        'buttons': buttons,
        'dpad': dpad,
        'dpad_bits': dpad_bits,
        'steering16': steering16,
        'steering_signed': steering_signed,
        'accel': accel,
        'brake': brake,
        'paddle_down': paddle_down,
        'paddle_up': paddle_up,
        'btn_home': btn_home,
        'btn_a': btn_a,
        'btn_b': btn_b,
        'btn_x': btn_x,
        'btn_y': btn_y,
        'btn_plus': btn_plus,
        'btn_minus': btn_minus,
        'btn_lsb': btn_lsb,
        'btn_rsb': btn_rsb,
        'btn_zl': btn_zl,
        'btn_zr': btn_zr,
        'byte2': data[2],
        'byte3': data[3],
        'byte0': data[0],
        'byte1': data[1]
    }

def draw_ui(state):
    """Draw the entire UI."""
    clear_screen()

    # Header
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  HORI Racing Wheel - Real-time Input Tester{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print()

    if state is None:
        print(f"{Colors.YELLOW}  Waiting for input data...{Colors.RESET}")
        return

    # Steering Wheel
    print(f"{Colors.BOLD}  STEERING WHEEL (16-BIT!){Colors.RESET}")
    print(f"  {draw_wheel(state['steering16'])}")

    # Show position as percentage from center
    if state['steering16'] == 0:
        position_str = "CENTER"
    elif state['steering16'] <= 0x7FFF:
        pct = int((state['steering16'] / 0x7FFF) * 100)
        position_str = f"RIGHT {pct}%"
    else:
        left_val = 0xFFFF - state['steering16']
        pct = int((left_val / 0x7FFF) * 100)
        position_str = f"LEFT {pct}%"

    print(f"  Position: {position_str}")
    print(f"  Raw: 0x{state['steering16']:04X} (unsigned: {state['steering16']:5d}, signed: {state['steering_signed']:6d})")
    print()

    # Pedals
    print(f"{Colors.BOLD}  PEDALS{Colors.RESET}")
    print(f"  {draw_bar(state['accel'], 255, 50, 'Accelerator')}")
    print(f"  {draw_bar(state['brake'], 255, 50, 'Brake')}")
    print()

    # Paddle Shifters
    print(f"{Colors.BOLD}  PADDLE SHIFTERS{Colors.RESET}")
    paddle_down_str = f"{Colors.BG_GREEN}{Colors.BOLD} GEAR DOWN {Colors.RESET}" if state['paddle_down'] else f"{Colors.BG_BLACK} GEAR DOWN {Colors.RESET}"
    paddle_up_str = f"{Colors.BG_GREEN}{Colors.BOLD} GEAR UP   {Colors.RESET}" if state['paddle_up'] else f"{Colors.BG_BLACK} GEAR UP   {Colors.RESET}"
    print(f"  {paddle_down_str}  {paddle_up_str}")
    print()

    # Shoulder Buttons & Plus/Minus (Byte 2 upper bits)
    print(f"{Colors.BOLD}  SHOULDER BUTTONS & +/- (Byte 2){Colors.RESET}")
    btn_lsb_str = f"{Colors.BG_GREEN}{Colors.BOLD}  L  {Colors.RESET}" if state['btn_lsb'] else f"{Colors.BG_BLACK}  L  {Colors.RESET}"
    btn_rsb_str = f"{Colors.BG_GREEN}{Colors.BOLD}  R  {Colors.RESET}" if state['btn_rsb'] else f"{Colors.BG_BLACK}  R  {Colors.RESET}"
    btn_plus_str = f"{Colors.BG_GREEN}{Colors.BOLD}  +  {Colors.RESET}" if state['btn_plus'] else f"{Colors.BG_BLACK}  +  {Colors.RESET}"
    btn_minus_str = f"{Colors.BG_GREEN}{Colors.BOLD}  -  {Colors.RESET}" if state['btn_minus'] else f"{Colors.BG_BLACK}  -  {Colors.RESET}"
    print(f"  {btn_lsb_str}  {btn_rsb_str}  {btn_plus_str}  {btn_minus_str}")
    print()

    # ZL/ZR Buttons (overlay on pedals)
    print(f"{Colors.BOLD}  ZL/ZR BUTTONS (Overlay on Pedals){Colors.RESET}")
    btn_zl_str = f"{Colors.BG_GREEN}{Colors.BOLD} ZL  {Colors.RESET}" if state['btn_zl'] else f"{Colors.BG_BLACK} ZL  {Colors.RESET}"
    btn_zr_str = f"{Colors.BG_GREEN}{Colors.BOLD} ZR  {Colors.RESET}" if state['btn_zr'] else f"{Colors.BG_BLACK} ZR  {Colors.RESET}"
    print(f"  {btn_zl_str}  {btn_zr_str}")
    print(f"  {Colors.YELLOW}Note: ZL sets Brake to 0xFF, ZR sets Accel to 0xFF{Colors.RESET}")
    print()

    # Face Buttons (Byte 3)
    print(f"{Colors.BOLD}  FACE BUTTONS (Byte 3){Colors.RESET}")
    btn_a_str = f"{Colors.BG_GREEN}{Colors.BOLD}  A  {Colors.RESET}" if state['btn_a'] else f"{Colors.BG_BLACK}  A  {Colors.RESET}"
    btn_b_str = f"{Colors.BG_GREEN}{Colors.BOLD}  B  {Colors.RESET}" if state['btn_b'] else f"{Colors.BG_BLACK}  B  {Colors.RESET}"
    btn_x_str = f"{Colors.BG_GREEN}{Colors.BOLD}  X  {Colors.RESET}" if state['btn_x'] else f"{Colors.BG_BLACK}  X  {Colors.RESET}"
    btn_y_str = f"{Colors.BG_GREEN}{Colors.BOLD}  Y  {Colors.RESET}" if state['btn_y'] else f"{Colors.BG_BLACK}  Y  {Colors.RESET}"
    btn_home_str = f"{Colors.BG_GREEN}{Colors.BOLD} HOME {Colors.RESET}" if state['btn_home'] else f"{Colors.BG_BLACK} HOME {Colors.RESET}"
    print(f"  {btn_a_str}  {btn_b_str}  {btn_x_str}  {btn_y_str}  {btn_home_str}")
    print()

    # D-pad
    print(f"{Colors.BOLD}  D-PAD{Colors.RESET}")
    dpad_names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "Neutral"]
    dpad_idx = state['dpad'] if state['dpad'] <= 8 else 8
    print(f"  Direction: {draw_dpad(state['dpad'])} ({dpad_names[dpad_idx]})")
    print()

    # Unknown Buttons (Bytes 0-1)
    print(f"{Colors.BOLD}  UNKNOWN (Bytes 0-1){Colors.RESET}")
    print(f"  Byte 0: 0x{state['byte0']:02X} (binary: {state['byte0']:08b})")
    print(f"  Byte 1: 0x{state['byte1']:02X} (binary: {state['byte1']:08b})")
    print(f"  {Colors.YELLOW}Note: All buttons appear to be mapped!{Colors.RESET}")
    print()

    # Raw values
    print(f"{Colors.BOLD}  RAW VALUES{Colors.RESET}")
    print(f"  Steering:   0x{state['steering16']:04X} (signed: {state['steering_signed']:6d}) [Bytes 6-7]")
    print(f"              0x0000=center, 0x0001-0x7FFF=right, 0x8000-0xFFFF=left")
    print(f"  Accel:      0x{state['accel']:02X} ({state['accel']:3d}) [Byte 5] {'(ZR pressed!)' if state['btn_zr'] else ''}")
    print(f"  Brake:      0x{state['brake']:02X} ({state['brake']:3d}) [Byte 4] {'(ZL pressed!)' if state['btn_zl'] else ''}")
    print(f"  Byte 2:     0x{state['byte2']:02X} (binary: {state['byte2']:08b})")
    print(f"              D-pad: {state['dpad']} (bits: 0x{state['dpad_bits']:02X}), "
          f"Shoulder: {'L' if state['btn_lsb'] else '-'}{'R' if state['btn_rsb'] else '-'}, "
          f"+/-: {'+' if state['btn_plus'] else '-'}{'-' if state['btn_minus'] else '.'}")
    print(f"  Byte 3:     0x{state['byte3']:02X} (binary: {state['byte3']:08b})")
    print(f"              Paddles: {'D' if state['paddle_down'] else '-'}{'U' if state['paddle_up'] else '-'}, "
          f"Face: {'H' if state['btn_home'] else '-'}{'A' if state['btn_a'] else '-'}"
          f"{'B' if state['btn_b'] else '-'}{'X' if state['btn_x'] else '-'}{'Y' if state['btn_y'] else '-'}")
    print(f"  Bytes 0-1:  0x{state['byte0']:02X} 0x{state['byte1']:02X} (unknown)")
    print()

    # Footer
    print(f"{Colors.CYAN}{'─'*80}{Colors.RESET}")
    print(f"{Colors.YELLOW}  Press Ctrl+C to exit{Colors.RESET}")

def main():
    print(f"{Colors.BOLD}HORI Racing Wheel - Real-time Input Tester{Colors.RESET}")
    print(f"Looking for device: VID=0x{VENDOR_ID:04X}, PID=0x{PRODUCT_ID:04X}")
    print()

    # Find the device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    if dev is None:
        print(f"{Colors.RED}✗ HORI Racing Wheel not found!{Colors.RESET}")
        print("Make sure the device is connected.")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ Device found: {dev.product}{Colors.RESET}")
    print(f"  Manufacturer: {dev.manufacturer}")
    print(f"  Serial: {dev.serial_number}")
    print()

    # Detach kernel driver if necessary
    interface_num = 0
    try:
        if dev.is_kernel_driver_active(interface_num):
            try:
                dev.detach_kernel_driver(interface_num)
            except usb.core.USBError:
                pass
    except (usb.core.USBError, NotImplementedError):
        pass

    # Set configuration
    try:
        dev.set_configuration()
    except usb.core.USBError as e:
        print(f"{Colors.YELLOW}Warning: Could not set configuration: {e}{Colors.RESET}")

    # Get configuration
    cfg = dev.get_active_configuration()
    interface = cfg[(0, 0)]

    # Find interrupt IN endpoint
    endpoint_in = None
    for ep in interface:
        if (ep.bEndpointAddress & 0x80) and ((ep.bmAttributes & 0x03) == 0x03):
            endpoint_in = ep.bEndpointAddress
            break

    if endpoint_in is None:
        print(f"{Colors.RED}✗ Could not find interrupt IN endpoint{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ Found interrupt endpoint: 0x{endpoint_in:02X}{Colors.RESET}")
    print()
    print(f"{Colors.BOLD}Starting real-time monitor...{Colors.RESET}")
    print(f"{Colors.YELLOW}Move the wheel, press pedals, and push buttons!{Colors.RESET}")
    print()
    time.sleep(2)

    # Start reading
    last_state = None
    update_counter = 0

    try:
        clear_screen()
        while True:
            try:
                # Read from device
                data = dev.read(endpoint_in, 64, timeout=100)

                if data:
                    state = parse_report(data)

                    if state:
                        # Update display every few reports to reduce flicker
                        update_counter += 1
                        if update_counter >= 3 or last_state is None or state != last_state:
                            draw_ui(state)
                            last_state = state
                            update_counter = 0

            except usb.core.USBError as e:
                if e.errno != 110:  # Ignore timeout errors
                    print(f"\n{Colors.RED}USB Error: {e}{Colors.RESET}")
                    break

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Exiting...{Colors.RESET}")

    finally:
        # Cleanup
        try:
            usb.util.release_interface(dev, interface_num)
        except:
            pass

    print(f"{Colors.GREEN}✓ Test complete!{Colors.RESET}\n")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{Colors.RED}Error: This script must be run with sudo{Colors.RESET}")
        print(f"Usage: sudo python3 {sys.argv[0]}")
        sys.exit(1)

    try:
        main()
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
