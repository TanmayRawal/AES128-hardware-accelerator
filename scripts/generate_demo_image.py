#!/usr/bin/env python3
"""
Generate a visually impressive 64x64 grayscale demo image for AES demo.
The image has clear structure so the encryption effect is visually obvious.
Outputs: sample_64x64_gradient.png, .raw, .coe  (overwrites existing files)
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

def write_coe(byte_data, out_path):
    hex_vals = [f"{b:02X}" for b in byte_data]
    text  = "memory_initialization_radix=16;\n"
    text += "memory_initialization_vector=\n"
    text += ",\n".join(hex_vals) + ";\n"
    out_path.write_text(text)

def generate_demo_image(w=64, h=64):
    img = Image.new("L", (w, h), 0)
    px  = img.load()
    cx, cy = w // 2, h // 2

    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            dist   = math.sqrt(dx*dx + dy*dy)
            angle  = math.atan2(dy, dx)

            # Concentric rings (bright/dark)
            rings = int(128 + 127 * math.cos(dist * 0.8)) & 0xFF

            # Radial spokes (8 spokes)
            spokes = int(128 + 127 * math.sin(angle * 8)) & 0xFF

            # Blend: rings dominate in centre, spokes dominate at edge
            t = min(dist / 35.0, 1.0)
            val = int(rings * (1 - t) + spokes * t)

            # Add a bright cross (horizontal + vertical lines)
            if abs(dx) <= 1 or abs(dy) <= 1:
                val = 255

            # Bright square frame border
            if x <= 2 or x >= w-3 or y <= 2 or y >= h-3:
                val = 200

            # Dark corners
            if dist > 30:
                val = max(0, val - 40)

            px[x, y] = max(0, min(255, val))

    return img


outdir = Path("sample_assets")
outdir.mkdir(exist_ok=True)

img  = generate_demo_image()
data = img.tobytes()

png_path = outdir / "sample_64x64_gradient.png"
raw_path = outdir / "sample_64x64_gradient.raw"
coe_path = outdir / "sample_64x64_gradient.coe"

img.save(png_path)
raw_path.write_bytes(data)
write_coe(data, coe_path)

# Also save a 4x upscaled version for easy viewing
img_big = img.resize((256, 256), Image.NEAREST)
img_big.save(outdir / "sample_64x64_gradient_preview.png")

print(f"Generated: {png_path}")
print(f"Generated: {raw_path}  ({len(data)} bytes)")
print(f"Generated: {coe_path}")
print(f"Preview (256x256): {outdir / 'sample_64x64_gradient_preview.png'}")
