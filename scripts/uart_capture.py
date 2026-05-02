#!/usr/bin/env python3
"""
uart_capture.py  –  Capture AES-CTR encrypted image data from Nexys 4 DDR UART

Usage:
    python scripts/uart_capture.py --port COM4 --output uart_dump.txt

The script:
  - Opens the serial port at 115200 8N1
  - Reads lines until "DONE" is received
  - Parses "BLOCK NNN: <32 hex chars>" lines
  - Saves:
      uart_dump.txt      – raw UART log (all lines)
      fpga_encrypted.raw – 4096 raw binary bytes of ciphertext
      fpga_encrypted.png – reconstructed 64x64 grayscale PNG
"""

import argparse
import sys
import time
from pathlib import Path

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


def list_ports():
    """List available serial ports."""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        if ports:
            print("Available serial ports:")
            for p in ports:
                print(f"  {p.device}  –  {p.description}")
        else:
            print("No serial ports found.")
    except Exception:
        pass


def capture(port: str, baud: int, timeout: int, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path  = out_dir / "uart_dump.txt"
    raw_path  = out_dir / "fpga_encrypted.raw"
    png_path  = out_dir / "fpga_encrypted.png"

    print(f"Opening {port} at {baud} baud ...")
    try:
        ser = serial.Serial(port, baud, timeout=2)
    except serial.SerialException as e:
        print(f"ERROR: Could not open {port}: {e}")
        list_ports()
        sys.exit(1)

    print("Waiting for data  (press BTNC on the board) ...")
    print("-" * 55)

    blocks = {}       # index → bytes
    log_lines = []
    deadline = time.time() + timeout
    done = False

    while time.time() < deadline:
        try:
            raw = ser.readline()
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            break

        if not raw:
            continue

        line = raw.decode("ascii", errors="replace").rstrip("\r\n")
        log_lines.append(line)
        print(line)

        if line.startswith("BLOCK "):
            # Format: BLOCK NNN: HHHH...HHHH  (32 hex chars)
            try:
                parts = line.split(":")
                idx   = int(parts[0].split()[1])
                hexstr= parts[1].strip()
                data  = bytes.fromhex(hexstr)
                if len(data) == 16:
                    blocks[idx] = data
                    deadline = time.time() + timeout  # reset timeout on each block
            except Exception:
                pass

        elif line.strip() == "DONE":
            done = True
            break

    ser.close()
    print("-" * 55)

    if not done:
        print("WARNING: Did not receive DONE — capture may be incomplete.")

    # Write log
    log_path.write_text("\n".join(log_lines))
    print(f"Log saved: {log_path}")

    # Assemble raw bytes (256 blocks × 16 bytes = 4096)
    if not blocks:
        print("ERROR: No BLOCK data received.")
        sys.exit(1)

    num_blocks = max(blocks.keys()) + 1
    raw_bytes = bytearray()
    for i in range(num_blocks):
        raw_bytes.extend(blocks.get(i, bytes(16)))  # zero-fill missing

    raw_path.write_bytes(bytes(raw_bytes))
    print(f"Raw bytes saved: {raw_path}  ({len(raw_bytes)} bytes, {num_blocks} blocks)")

    # Reconstruct PNG
    size = 64
    expected = size * size
    img_data = bytes(raw_bytes[:expected])
    if len(img_data) == expected:
        img = Image.frombytes("L", (size, size), img_data)
        img.save(png_path)
        print(f"Encrypted image saved: {png_path}")
    else:
        print(f"WARNING: Expected {expected} bytes, got {len(img_data)} – skipping PNG.")

    print(f"\nCapture complete. {len(blocks)}/256 blocks received.")
    return raw_path


def main():
    ap = argparse.ArgumentParser(
        description="Capture AES-CTR encrypted image from Nexys 4 DDR UART"
    )
    ap.add_argument("--port",    default=None,       help="Serial port (e.g. COM4, /dev/ttyUSB0)")
    ap.add_argument("--baud",    type=int, default=115200, help="Baud rate (default: 115200)")
    ap.add_argument("--timeout", type=int, default=60,     help="Idle timeout in seconds (default: 60)")
    ap.add_argument("--outdir",  type=Path, default=Path("capture_output"),
                    help="Output directory (default: capture_output/)")
    args = ap.parse_args()

    if args.port is None:
        print("ERROR: --port is required.")
        list_ports()
        ap.print_help()
        sys.exit(1)

    capture(args.port, args.baud, args.timeout, args.outdir)


if __name__ == "__main__":
    main()
