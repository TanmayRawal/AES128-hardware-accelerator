#!/usr/bin/env python3
"""
Convert an input image into:
- 64x64 grayscale PNG
- raw byte file
- .coe file for BRAM initialization
"""

from pathlib import Path
from PIL import Image
import argparse

def write_coe(byte_data, out_path):
    hex_vals = [f"{b:02X}" for b in byte_data]
    text = "memory_initialization_radix=16;\n"
    text += "memory_initialization_vector=\n"
    text += ",\n".join(hex_vals) + ";\n"
    out_path.write_text(text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_image", type=Path)
    ap.add_argument("--size", type=int, default=64)
    ap.add_argument("--outdir", type=Path, default=Path("out_preprocess"))
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    img = Image.open(args.input_image).convert("L").resize((args.size, args.size))
    png_path = args.outdir / f"image_{args.size}x{args.size}_gray.png"
    raw_path = args.outdir / f"image_{args.size}x{args.size}.raw"
    coe_path = args.outdir / f"image_{args.size}x{args.size}.coe"

    img.save(png_path)
    data = img.tobytes()
    raw_path.write_bytes(data)
    write_coe(data, coe_path)

    print(f"Saved: {png_path}")
    print(f"Saved: {raw_path}")
    print(f"Saved: {coe_path}")

if __name__ == "__main__":
    main()
