#!/usr/bin/env python3
"""
Reconstruct an image from:
- raw byte file
or
- hex text UART dump (one line per block or plain hex stream)

Default output is a 64x64 grayscale PNG.
"""

from pathlib import Path
from PIL import Image
import argparse
import re

def load_bytes_from_hex_text(path: Path) -> bytes:
    text = path.read_text()
    hex_pairs = re.findall(r'[0-9A-Fa-f]{2}', text)
    return bytes(int(x, 16) for x in hex_pairs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_file", type=Path)
    ap.add_argument("--mode", choices=["raw", "hextext"], default="raw")
    ap.add_argument("--size", type=int, default=64)
    ap.add_argument("--output", type=Path, default=Path("reconstructed.png"))
    args = ap.parse_args()

    if args.mode == "raw":
        data = args.input_file.read_bytes()
    else:
        data = load_bytes_from_hex_text(args.input_file)

    expected_len = args.size * args.size
    data = data[:expected_len]

    if len(data) != expected_len:
        raise ValueError(f"Need {expected_len} bytes, got {len(data)}")

    img = Image.frombytes("L", (args.size, args.size), data)
    img.save(args.output)
    print(f"Saved: {args.output}")

if __name__ == "__main__":
    main()
