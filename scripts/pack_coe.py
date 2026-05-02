"""Pack 8-bit COE entries into 32-bit words for AXI BRAM Controller."""
import re
from pathlib import Path

src = Path(r"c:\Users\Tanmay\Downloads\aes128_image_encryption_ipcore_nexys4ddr\aes128_image_encryption_ipcore_nexys4ddr\sample_assets\sample_64x64_gradient.coe")
dst = src  # overwrite in place

text = src.read_text()
# Extract all hex values
vals = re.findall(r'[0-9A-Fa-f]+', text.split('memory_initialization_vector=')[1])
bytes_list = [int(v, 16) for v in vals]

print(f"Read {len(bytes_list)} bytes")

# Pack 4 bytes per 32-bit word (big-endian: byte0 in bits[31:24])
words = []
for i in range(0, len(bytes_list), 4):
    b0 = bytes_list[i] if i < len(bytes_list) else 0
    b1 = bytes_list[i+1] if i+1 < len(bytes_list) else 0
    b2 = bytes_list[i+2] if i+2 < len(bytes_list) else 0
    b3 = bytes_list[i+3] if i+3 < len(bytes_list) else 0
    w = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
    words.append(f"{w:08X}")

print(f"Packed into {len(words)} 32-bit words")

# Write new COE
lines = ["memory_initialization_radix=16;", "memory_initialization_vector="]
for i, w in enumerate(words):
    sep = ";" if i == len(words)-1 else ","
    lines.append(w + sep)

dst.write_text("\n".join(lines) + "\n")
print(f"Written to {dst}")
