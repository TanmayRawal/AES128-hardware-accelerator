#!/usr/bin/env python3
"""
compare_results.py  –  Compare FPGA UART output to software golden reference

Usage:
    python scripts/compare_results.py <fpga_raw_or_uart_dump> <golden_raw>

Examples:
    python scripts/compare_results.py capture_output/fpga_encrypted.raw sample_assets/sample_64x64_gradient_encrypted_ctr.raw
    python scripts/compare_results.py capture_output/uart_dump.txt       sample_assets/sample_64x64_gradient_encrypted_ctr.raw --fpga-mode hextext

Output:
    - Total bytes compared
    - Number of mismatches
    - Match percentage
    - First mismatch location (if any)
    - Side-by-side diff of first mismatching block
    - Saves side-by-side comparison PNG
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


def load_raw(path: Path) -> bytes:
    return path.read_bytes()


def load_hextext(path: Path) -> bytes:
    """Parse UART dump: extract all hex pairs from BLOCK NNN: HHHH lines."""
    text  = path.read_text(errors="replace")
    pairs = re.findall(r"BLOCK\s+\d+:\s+([0-9A-Fa-f]+)", text)
    result = bytearray()
    for p in pairs:
        result.extend(bytes.fromhex(p))
    return bytes(result)


def compare(fpga: bytes, golden: bytes, image_size: int = 64) -> bool:
    print("=" * 58)
    print("  AES-128 CTR Encryption — FPGA vs Software Reference")
    print("=" * 58)

    n = min(len(fpga), len(golden))
    if len(fpga) != len(golden):
        print(f"WARNING: Length mismatch — FPGA={len(fpga)}, Golden={len(golden)}, comparing {n} bytes\n")

    mismatches = []
    for i in range(n):
        if fpga[i] != golden[i]:
            mismatches.append(i)

    pct = 100.0 * (n - len(mismatches)) / n if n > 0 else 0.0
    print(f"Bytes compared : {n}")
    print(f"Mismatches     : {len(mismatches)}")
    print(f"Match          : {pct:.2f}%")

    if not mismatches:
        print("\n✅  PERFECT MATCH — FPGA output is cryptographically correct!")
        ok = True
    else:
        print(f"\n❌  MISMATCH detected!")
        first = mismatches[0]
        blk   = first // 16
        print(f"   First mismatch at byte {first}  (block {blk}, byte {first%16} within block)")
        print(f"\n   Block {blk} comparison:")
        off = blk * 16
        fpga_blk   = fpga  [off:off+16]
        golden_blk = golden[off:off+16]
        print(f"   FPGA  : {fpga_blk.hex().upper()}")
        print(f"   Golden: {golden_blk.hex().upper()}")
        diff = "".join("^" if fpga_blk[i] != golden_blk[i] else " "
                       for i in range(min(16, len(fpga_blk))))
        print(f"   Diff  : {diff}")

        print("\n   HINT: Check AES key and initial counter match software_reference_ctr.py defaults.")
        ok = False

    print("=" * 58)

    # Save comparison PNG (original | encrypted-fpga | encrypted-golden)
    expected_len = image_size * image_size
    if len(fpga) >= expected_len and len(golden) >= expected_len:
        try:
            fpga_img   = Image.frombytes("L", (image_size, image_size), fpga[:expected_len])
            golden_img = Image.frombytes("L", (image_size, image_size), golden[:expected_len])

            # Composite: FPGA | Golden  (side by side)
            combined = Image.new("L", (image_size * 2 + 4, image_size), 128)
            combined.paste(fpga_img,   (0, 0))
            combined.paste(golden_img, (image_size + 4, 0))
            out = Path("comparison.png")
            combined.save(out)
            print(f"\nComparison image saved: {out}")
            print("  Left  = FPGA encrypted output")
            print("  Right = Software golden reference")
        except Exception as e:
            print(f"(Could not save comparison PNG: {e})")

    return ok


def main():
    ap = argparse.ArgumentParser(description="Compare FPGA vs software AES-CTR output")
    ap.add_argument("fpga_file",   type=Path, help="FPGA output: .raw bytes or UART hex dump .txt")
    ap.add_argument("golden_file", type=Path, help="Golden reference .raw file")
    ap.add_argument("--fpga-mode", choices=["raw", "hextext"], default=None,
                    help="Force parse mode for fpga_file (default: auto-detect by extension)")
    ap.add_argument("--size",      type=int,  default=64, help="Image dimension (default: 64)")
    args = ap.parse_args()

    if not args.fpga_file.exists():
        print(f"ERROR: FPGA file not found: {args.fpga_file}"); sys.exit(1)
    if not args.golden_file.exists():
        print(f"ERROR: Golden file not found: {args.golden_file}"); sys.exit(1)

    # Auto-detect mode
    mode = args.fpga_mode
    if mode is None:
        mode = "hextext" if args.fpga_file.suffix == ".txt" else "raw"

    fpga   = load_hextext(args.fpga_file) if mode == "hextext" else load_raw(args.fpga_file)
    golden = load_raw(args.golden_file)

    ok = compare(fpga, golden, args.size)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
