#!/usr/bin/env python3
"""
HORI Racing Wheel - Interactive Control Mapper

This tool helps you identify which bytes/bits correspond to each control
by detecting changes as you move controls one at a time.

Usage:
    sudo python3 map_controls.py
"""

import sys
import time
import os
from collections import deque

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

class ControlMapper:
    def __init__(self, dev, endpoint):
        self.dev = dev
        self.endpoint = endpoint
        self.baseline = None
        self.report_size = 64  # Read full 64 bytes to catch everything
        self.history = deque(maxlen=100)

    def read_report(self):
        """Read a single report from the device."""
        try:
            data = self.dev.read(self.endpoint, self.report_size, timeout=100)
            return bytes(data)
        except usb.core.USBError as e:
            if e.errno != 110:  # Ignore timeout
                raise
            return None

    def capture_baseline(self, samples=20):
        """Capture baseline state (neutral position)."""
        print(f"{Colors.YELLOW}Capturing baseline... Keep all controls in neutral position!{Colors.RESET}")

        reports = []
        for i in range(samples):
            report = self.read_report()
            if report:
                reports.append(report)
            time.sleep(0.05)

        if not reports:
            print(f"{Colors.RED}Failed to capture baseline!{Colors.RESET}")
            return False

        # Use most common report as baseline
        self.baseline = max(set(reports), key=reports.count)

        print(f"{Colors.GREEN}✓ Baseline captured ({len(self.baseline)} bytes){Colors.RESET}")
        print(f"  Baseline: {' '.join(f'{b:02X}' for b in self.baseline[:20])}...")
        print()
        return True

    def detect_changes(self, duration=5, threshold=1):
        """Detect which bytes change during the specified duration."""
        print(f"{Colors.CYAN}Monitoring for {duration} seconds...{Colors.RESET}")
        print(f"{Colors.YELLOW}MOVE THE CONTROL NOW!{Colors.RESET}")
        print()

        changes = {}  # byte_index -> set of values seen
        min_values = [255] * self.report_size
        max_values = [0] * self.report_size

        start_time = time.time()
        sample_count = 0

        while time.time() - start_time < duration:
            report = self.read_report()
            if report:
                sample_count += 1

                # Compare with baseline
                for i in range(min(len(report), len(self.baseline))):
                    if report[i] != self.baseline[i]:
                        if i not in changes:
                            changes[i] = set()
                        changes[i].add(report[i])

                    # Track min/max for range analysis
                    min_values[i] = min(min_values[i], report[i])
                    max_values[i] = max(max_values[i], report[i])

        print(f"{Colors.GREEN}✓ Captured {sample_count} samples{Colors.RESET}")
        print()

        return changes, min_values, max_values, sample_count

    def analyze_changes(self, changes, min_values, max_values):
        """Analyze and display which bytes changed."""
        if not changes:
            print(f"{Colors.YELLOW}⚠ No changes detected!{Colors.RESET}")
            print("  Make sure you moved the control during monitoring.")
            return None

        print(f"{Colors.BOLD}Changes Detected:{Colors.RESET}")
        print()

        results = []

        for byte_idx in sorted(changes.keys()):
            values = sorted(changes[byte_idx])
            value_range = max_values[byte_idx] - min_values[byte_idx]

            # Determine if it's a bit field or analog value
            if len(values) == 2 and set(values).issubset({0, 1}):
                change_type = "BUTTON/BIT"
                color = Colors.MAGENTA
            elif len(values) <= 16 and value_range <= 15:
                change_type = "MULTI-BIT"
                color = Colors.CYAN
            else:
                change_type = "ANALOG"
                color = Colors.GREEN

            print(f"  {color}Byte {byte_idx:2d}{Colors.RESET}: {change_type}")
            print(f"    Range: 0x{min_values[byte_idx]:02X} - 0x{max_values[byte_idx]:02X} ({min_values[byte_idx]:3d} - {max_values[byte_idx]:3d})")
            print(f"    Unique values: {len(values)}")

            if len(values) <= 20:
                print(f"    Values seen: {', '.join(f'0x{v:02X}' for v in values)}")

            # Bit analysis for bytes with small number of values
            if len(values) <= 16:
                print(f"    Bit analysis:")
                for bit in range(8):
                    bit_values = set((v >> bit) & 1 for v in values)
                    if len(bit_values) > 1:
                        print(f"      Bit {bit}: ACTIVE (values: {sorted(bit_values)})")

            print()

            results.append({
                'byte': byte_idx,
                'type': change_type,
                'min': min_values[byte_idx],
                'max': max_values[byte_idx],
                'range': value_range,
                'values': values
            })

        return results

    def compare_reports_live(self, duration=10):
        """Show live comparison of current report vs baseline."""
        print(f"{Colors.CYAN}Live comparison mode (Ctrl+C to stop){Colors.RESET}")
        print()

        try:
            while True:
                report = self.read_report()
                if report:
                    # Clear screen
                    os.system('clear')

                    print(f"{Colors.BOLD}LIVE REPORT COMPARISON{Colors.RESET}")
                    print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
                    print()

                    # Show header
                    print("Byte | Baseline | Current | Diff | Binary (Current)      | Binary (Baseline)")
                    print("-" * 80)

                    # Show first 32 bytes (enough to catch all important data)
                    for i in range(min(32, len(report))):
                        baseline_val = self.baseline[i] if i < len(self.baseline) else 0
                        current_val = report[i]
                        diff = current_val - baseline_val

                        # Color code based on difference
                        if diff != 0:
                            color = Colors.GREEN if abs(diff) > 10 else Colors.YELLOW
                        else:
                            color = Colors.RESET

                        print(f"{color}{i:4d} | 0x{baseline_val:02X} {baseline_val:3d} | "
                              f"0x{current_val:02X} {current_val:3d} | {diff:+4d} | "
                              f"{current_val:08b} | {baseline_val:08b}{Colors.RESET}")

                    print()
                    print(f"{Colors.YELLOW}Move controls to see changes. Press Ctrl+C to exit.{Colors.RESET}")

                time.sleep(0.05)

        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}✓ Live mode stopped{Colors.RESET}\n")

def print_header():
    """Print welcome header."""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  HORI Racing Wheel - Interactive Control Mapper{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print()
    print("This tool helps you identify which bytes correspond to each control")
    print("by detecting changes as you move controls one at a time.")
    print()

def main():
    print_header()

    print(f"Looking for device: VID=0x{VENDOR_ID:04X}, PID=0x{PRODUCT_ID:04X}")

    # Find device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print(f"{Colors.RED}✗ HORI Racing Wheel not found!{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ Device found: {dev.product}{Colors.RESET}")
    print()

    # Setup device
    interface_num = 0
    try:
        if dev.is_kernel_driver_active(interface_num):
            try:
                dev.detach_kernel_driver(interface_num)
            except usb.core.USBError:
                pass
    except (usb.core.USBError, NotImplementedError):
        pass

    try:
        dev.set_configuration()
    except usb.core.USBError:
        pass

    cfg = dev.get_active_configuration()
    interface = cfg[(0, 0)]

    # Find endpoint
    endpoint_in = None
    for ep in interface:
        if (ep.bEndpointAddress & 0x80) and ((ep.bmAttributes & 0x03) == 0x03):
            endpoint_in = ep.bEndpointAddress
            break

    if endpoint_in is None:
        print(f"{Colors.RED}✗ Could not find interrupt IN endpoint{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ Ready to start mapping{Colors.RESET}")
    print()

    # Create mapper
    mapper = ControlMapper(dev, endpoint_in)

    # Main menu
    controls_to_map = [
        "Steering Wheel (Full Left to Full Right)",
        "Steering Wheel (Center to Left)",
        "Steering Wheel (Center to Right)",
        "Accelerator Pedal (Not Pressed to Full)",
        "Brake Pedal (Not Pressed to Full)",
        "Clutch Pedal (Not Pressed to Full)",
        "Button 1",
        "Button 2",
        "Button 3",
        "Button 4",
        "Button 5",
        "Button 6",
        "Button 7",
        "Button 8",
        "Button 9",
        "Button 10",
        "Button 11",
        "Button 12",
        "Button 13",
        "D-Pad Up",
        "D-Pad Right",
        "D-Pad Down",
        "D-Pad Left",
        "Live Comparison Mode",
        "Re-capture Baseline",
        "Exit"
    ]

    # Capture initial baseline
    print(f"{Colors.BOLD}Step 1: Capture Neutral Position{Colors.RESET}")
    print("Place all controls in neutral position:")
    print("  - Steering wheel centered")
    print("  - All pedals released")
    print("  - No buttons pressed")
    print("  - D-pad centered")
    print()
    input("Press ENTER when ready...")
    print()

    if not mapper.capture_baseline():
        sys.exit(1)

    # Interactive mapping
    mapping_results = {}

    while True:
        print(f"{Colors.BOLD}Select a control to map:{Colors.RESET}")
        print()

        for i, control in enumerate(controls_to_map, 1):
            status = f" {Colors.GREEN}[MAPPED]{Colors.RESET}" if control in mapping_results else ""
            print(f"  {i:2d}. {control}{status}")

        print()
        choice = input(f"{Colors.CYAN}Enter number (or 'q' to quit): {Colors.RESET}").strip()

        if choice.lower() in ['q', 'quit', 'exit']:
            break

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(controls_to_map):
                print(f"{Colors.RED}Invalid choice!{Colors.RESET}\n")
                continue
        except ValueError:
            print(f"{Colors.RED}Invalid input!{Colors.RESET}\n")
            continue

        control = controls_to_map[idx]

        if control == "Live Comparison Mode":
            mapper.compare_reports_live()
            continue
        elif control == "Re-capture Baseline":
            mapper.capture_baseline()
            continue
        elif control == "Exit":
            break

        print()
        print(f"{Colors.BOLD}Mapping: {control}{Colors.RESET}")
        print()
        print(f"{Colors.YELLOW}Instructions:{Colors.RESET}")
        print(f"  1. Keep the control in neutral position")
        print(f"  2. Press ENTER to start monitoring")
        print(f"  3. Move ONLY this control during the 5 seconds")
        print(f"  4. Return to neutral before time runs out")
        print()
        input("Press ENTER to start...")
        print()

        # Detect changes
        changes, min_vals, max_vals, samples = mapper.detect_changes(duration=5)
        results = mapper.analyze_changes(changes, min_vals, max_vals)

        if results:
            mapping_results[control] = results

            # Save to file
            with open('control_mapping.txt', 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Control: {control}\n")
                f.write(f"Samples: {samples}\n")
                f.write(f"{'='*80}\n")
                for r in results:
                    f.write(f"Byte {r['byte']:2d}: {r['type']:10s} | "
                           f"Range: 0x{r['min']:02X}-0x{r['max']:02X} "
                           f"({r['min']:3d}-{r['max']:3d}) | "
                           f"Span: {r['range']:3d}\n")

        print(f"{Colors.GREEN}✓ Results saved to control_mapping.txt{Colors.RESET}")
        print()
        input("Press ENTER to continue...")
        print()
        os.system('clear')

    # Final summary
    print()
    print(f"{Colors.BOLD}{Colors.GREEN}Mapping Session Complete!{Colors.RESET}")
    print()
    print(f"Mapped {len(mapping_results)} controls")
    print(f"Results saved to: control_mapping.txt")
    print()

    # Cleanup
    try:
        usb.util.release_interface(dev, interface_num)
    except:
        pass

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{Colors.RED}Error: This script must be run with sudo{Colors.RESET}")
        print(f"Usage: sudo python3 {sys.argv[0]}")
        sys.exit(1)

    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
