#!/usr/bin/env python3
"""
multi_image_demo.py — Multi-Image AES-128 Hardware Encryption Demonstrator

Generates 3 different 64×64 test images, loads each into the FPGA's Input BRAM
via JTAG (XSCT), triggers hardware AES-128 CTR encryption, dumps the Output BRAM,
and produces a single comprehensive HTML dashboard comparing all results.

Usage:
    python multi_image_demo.py

Requirements:
    - FPGA must be programmed and running the AES firmware (main.c)
    - Xilinx XSCT must be available at the configured path
    - Board connected via USB/JTAG
"""

import subprocess
import struct
import base64
import math
import os
import time
import sys

# ─────────────────── Configuration ───────────────────
XSCT_PATH    = r"C:\Xilinx\Vitis\2024.2\bin\xsct.bat"
PROJECT_DIR  = r"C:\Users\Tanmay\Downloads\aes128_image_encryption_ipcore_nexys4ddr\aes128_image_encryption_ipcore_nexys4ddr"
DUMP_SCRIPT  = os.path.join(PROJECT_DIR, "scripts", "dump_both.tcl")
HTML_OUTPUT  = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "aes_multi_image_demo.html")

BRAM_IN_BASE  = 0xC0000000
IMG_SIZE      = 64
IMG_BYTES     = IMG_SIZE * IMG_SIZE  # 4096

# ─────────────────── Image Generators ───────────────────

def generate_gradient(size=64):
    """Diagonal gradient: black top-left → white bottom-right."""
    pixels = bytearray(size * size)
    for y in range(size):
        for x in range(size):
            val = int(((x + y) / (2 * (size - 1))) * 255)
            pixels[y * size + x] = val
    return bytes(pixels), "Diagonal Gradient", "Smooth diagonal gradient from black (0) to white (255)"

def generate_checkerboard(size=64, block_sz=8):
    """Classic 8×8 checkerboard pattern (0 and 255)."""
    pixels = bytearray(size * size)
    for y in range(size):
        for x in range(size):
            bx = x // block_sz
            by = y // block_sz
            pixels[y * size + x] = 255 if ((bx + by) % 2 == 0) else 0
    return bytes(pixels), "Checkerboard 8×8", "High-contrast binary pattern: 0x00 and 0xFF alternating blocks"

def generate_concentric_circles(size=64):
    """Concentric rings radiating from center."""
    pixels = bytearray(size * size)
    cx, cy = size // 2, size // 2
    max_r = math.sqrt(cx*cx + cy*cy)
    for y in range(size):
        for x in range(size):
            r = math.sqrt((x - cx)**2 + (y - cy)**2)
            val = int((math.sin(r * math.pi / 4) * 0.5 + 0.5) * 255)
            pixels[y * size + x] = val
    return bytes(pixels), "Concentric Circles", "Sinusoidal rings from center, tests radial patterns"

# ─────────────────── XSCT Helpers ───────────────────

def generate_load_tcl(pixel_data, tcl_path):
    """Create a TCL script that writes pixel_data into Input BRAM via mwr commands."""
    lines = ['connect', 'targets -set -filter {name =~ "MicroBlaze #0"}']

    # Pack pixel bytes into 32-bit big-endian words and write via mwr
    for word_idx in range(0, len(pixel_data), 4):
        chunk = pixel_data[word_idx:word_idx+4]
        if len(chunk) < 4:
            chunk = chunk + b'\x00' * (4 - len(chunk))
        word_val = struct.unpack('>I', chunk)[0]
        addr = BRAM_IN_BASE + word_idx
        lines.append(f"mwr 0x{addr:08X} 0x{word_val:08X}")

    # Reset the MicroBlaze processor so firmware restarts fresh
    # This does NOT re-program the bitstream, so BRAM data is preserved
    lines.append('rst -processor')
    lines.append('con')
    lines.append('after 500')
    lines.append('disconnect')
    lines.append('exit')

    with open(tcl_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def load_image_to_fpga(tcl_path):
    """Run the XSCT load script to fill Input BRAM."""
    result = subprocess.run(
        [XSCT_PATH, tcl_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120
    )
    return result.returncode == 0

def dump_bram():
    """Run dump_both.tcl to extract both BRAMs to .raw files."""
    result = subprocess.run(
        [XSCT_PATH, DUMP_SCRIPT],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60
    )
    return result.returncode == 0

def read_raw_file(filename):
    """Read a .raw binary file and return bytes (padded/truncated to IMG_BYTES)."""
    path = os.path.join(PROJECT_DIR, filename)
    with open(path, 'rb') as f:
        data = f.read()
    data = data[:IMG_BYTES]
    if len(data) < IMG_BYTES:
        data += b'\x00' * (IMG_BYTES - len(data))
    return data

# ─────────────────── Crypto Statistics ───────────────────

def calc_entropy(data):
    """Shannon entropy in bits per byte."""
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    total = len(data)
    entropy = 0.0
    for f in freq:
        if f > 0:
            p = f / total
            entropy -= p * math.log2(p)
    return entropy

def calc_bit_balance(data):
    """Percentage of 1-bits vs total bits."""
    ones = sum(bin(b).count('1') for b in data)
    total = len(data) * 8
    return (ones / total) * 100

def calc_chi_square(data):
    """Chi-square statistic for uniformity test."""
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    expected = len(data) / 256
    chi2 = sum((f - expected)**2 / expected for f in freq)
    return chi2

def calc_correlation(data):
    """Correlation coefficient between adjacent pixels."""
    n = len(data) - 1
    if n <= 0:
        return 0.0
    x = [data[i] for i in range(n)]
    y = [data[i+1] for i in range(n)]
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
    var_x = sum((xi - mean_x)**2 for xi in x) / n
    var_y = sum((yi - mean_y)**2 for yi in y) / n
    denom = math.sqrt(var_x * var_y)
    return cov / denom if denom > 0 else 0.0


# ─────────────────── HTML Dashboard ───────────────────

def generate_html(results, timestamp):
    """Build a comprehensive multi-image comparison dashboard."""

    # Build image cards HTML
    image_cards = ""
    stats_rows = ""

    for idx, r in enumerate(results):
        in_b64 = base64.b64encode(r['input_data']).decode()
        out_b64 = base64.b64encode(r['output_data']).decode()
        key_data = bytes(a ^ b for a, b in zip(r['input_data'], r['output_data']))
        key_b64 = base64.b64encode(key_data).decode()

        image_cards += f"""
    <div class="image-set">
      <h2 class="set-title">Test Image {idx+1}: {r['name']}</h2>
      <p class="set-desc">{r['description']}</p>
      <div class="triple">
        <div class="img-card">
          <h3>Plaintext (Input)</h3>
          <canvas id="pIn{idx}" width="64" height="64" class="img-canvas"></canvas>
          <canvas id="hIn{idx}" width="256" height="60" class="hist-canvas"></canvas>
        </div>
        <div class="img-card">
          <h3>Ciphertext (FPGA Output)</h3>
          <canvas id="pOut{idx}" width="64" height="64" class="img-canvas"></canvas>
          <canvas id="hOut{idx}" width="256" height="60" class="hist-canvas"></canvas>
        </div>
        <div class="img-card">
          <h3>Keystream (P ⊕ C)</h3>
          <canvas id="pKey{idx}" width="64" height="64" class="img-canvas"></canvas>
          <canvas id="hKey{idx}" width="256" height="60" class="hist-canvas"></canvas>
        </div>

      </div>
    </div>
"""
        # Stats for this image
        entropy_val = r['entropy']
        bits_val = r['bit_balance']
        chi_val = r['chi_square']
        corr_in = r['corr_input']
        corr_out = r['corr_output']
        entropy_class = "pass" if entropy_val > 7.5 else "warn"
        bits_class = "pass" if 48 < bits_val < 52 else "warn"

        stats_rows += f"""
      <tr>
        <td>{r['name']}</td>
        <td class="{entropy_class}">{entropy_val:.4f}</td>
        <td class="{bits_class}">{bits_val:.2f}% / {100-bits_val:.2f}%</td>
        <td>{chi_val:.1f}</td>
        <td>{corr_in:.4f}</td>
        <td class="pass">{corr_out:.4f}</td>
      </tr>"""

    # Build JavaScript data arrays
    js_data = "const imageData = [\n"
    for idx, r in enumerate(results):
        in_b64 = base64.b64encode(r['input_data']).decode()
        out_b64 = base64.b64encode(r['output_data']).decode()
        js_data += f'  {{ inB64: "{in_b64}", outB64: "{out_b64}" }},\n'
    js_data += "];\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AES-128 Multi-Image FPGA Hardware Validation</title>
  <style>
    :root {{
      --bg: #0a0e1a; --panel: #141b2d; --border: #1e2d4a;
      --text: #e8ecf4; --muted: #7a8ba8; --accent: #38bdf8;
      --purple: #a78bfa; --green: #4ade80; --pink: #f472b6;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg); color: var(--text);
      font-family: 'Segoe UI', system-ui, sans-serif;
      padding: 30px 20px;
    }}
    h1 {{
      text-align: center; font-size: 2.4rem; font-weight: 800;
      background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 50%, #f472b6 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      margin-bottom: 5px;
    }}
    .subtitle {{ text-align: center; color: var(--muted); font-size: 1.05rem; margin-bottom: 10px; }}
    .timestamp {{ text-align: center; color: #4a5568; font-size: 0.85rem; margin-bottom: 30px; }}

    .crypto-params {{
      max-width: 900px; margin: 0 auto 30px auto;
      background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
      padding: 20px 25px;
    }}
    .crypto-params h2 {{ color: var(--purple); font-size: 1.1rem; margin-bottom: 12px; }}
    .param-row {{ display: flex; gap: 20px; flex-wrap: wrap; }}
    .param {{
      flex: 1; min-width: 300px; background: rgba(0,0,0,0.25); padding: 12px 16px;
      border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);
    }}
    .param .label {{ color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }}
    .param .value {{ font-family: 'Consolas', monospace; font-size: 1rem; color: var(--accent); letter-spacing: 1.5px; margin-top: 4px; }}

    .image-set {{
      max-width: 1100px; margin: 0 auto 35px auto;
      background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
      padding: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.35);
    }}
    .set-title {{
      color: var(--accent); font-size: 1.3rem; margin-bottom: 4px;
      border-bottom: 1px solid var(--border); padding-bottom: 10px;
    }}
    .set-desc {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 20px; }}

    .triple {{ display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }}
    .img-card {{
      display: flex; flex-direction: column; align-items: center;
      background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.04);
    }}
    .img-card h3 {{ color: #cbd5e1; font-size: 0.95rem; margin-bottom: 10px; }}
    .img-canvas {{
      width: 200px; height: 200px; image-rendering: pixelated;
      border: 2px solid var(--border); border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.4); margin-bottom: 10px;
    }}
    .hist-canvas {{
      width: 200px; height: 50px; background: rgba(0,0,0,0.3);
      border-radius: 4px; border: 1px solid rgba(255,255,255,0.05);
    }}

    .stats-panel {{
      max-width: 1100px; margin: 0 auto 30px auto;
      background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
      padding: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.35);
    }}
    .stats-panel h2 {{
      color: var(--green); font-size: 1.3rem; margin-bottom: 15px;
      border-bottom: 1px solid var(--border); padding-bottom: 10px;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th {{
      text-align: left; padding: 10px 12px; color: var(--muted);
      text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px;
      border-bottom: 2px solid var(--border);
    }}
    td {{ padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }}
    td.pass {{ color: var(--green); font-weight: 600; }}
    td.warn {{ color: #fbbf24; font-weight: 600; }}

    .footer {{
      text-align: center; color: #3a4560; font-size: 0.8rem; margin-top: 30px;
      padding-top: 20px; border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <h1>AES-128 Multi-Image Hardware Validation</h1>
  <p class="subtitle">Nexys 4 DDR — Custom RTL IP Core — JTAG Memory Extraction</p>
  <p class="timestamp">Generated: {timestamp}</p>

  <div class="crypto-params">
    <h2>Cryptographic Parameters</h2>
    <div class="param-row">
      <div class="param">
        <div class="label">AES-128 Key</div>
        <div class="value">00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F</div>
      </div>
      <div class="param">
        <div class="label">CTR Initial Counter (IV)</div>
        <div class="value">F0 E0 D0 C0 B0 A0 90 80 70 60 50 40 30 20 10 00</div>
      </div>
    </div>
  </div>

  {image_cards}

  <div class="stats-panel">
    <h2>NIST-Inspired Cryptographic Metrics — Comparison Table</h2>
    <table>
      <thead>
        <tr>
          <th>Test Image</th>
          <th>Entropy (bits/byte)</th>
          <th>Bit Balance (1s / 0s)</th>
          <th>Chi-Square</th>
          <th>Input Correlation</th>
          <th>Output Correlation</th>

        </tr>
      </thead>
      <tbody>
        {stats_rows}
        <tr style="border-top: 2px solid var(--border);">
          <td style="color: var(--muted);"><em>Ideal Random</em></td>
          <td style="color: var(--muted);"><em>8.0000</em></td>
          <td style="color: var(--muted);"><em>50.00% / 50.00%</em></td>
          <td style="color: var(--muted);"><em>~255.0</em></td>
          <td style="color: var(--muted);"><em>varies</em></td>
          <td style="color: var(--muted);"><em>≈ 0.0000</em></td>

        </tr>
      </tbody>
    </table>
  </div>

  <div class="footer">
    AES-128 CTR Image Encryption IP Core — Nexys 4 DDR (xc7a100tcsg324-1)<br>
    MicroBlaze + Custom AXI4-Lite AES IP — 12-cycle latency per block
  </div>

  <script>
    {js_data}

    function renderAll() {{
      for (let idx = 0; idx < imageData.length; idx++) {{
        const plain = atob(imageData[idx].inB64);
        const cipher = atob(imageData[idx].outB64);


        const pCtx = document.getElementById('pIn'+idx).getContext('2d');
        const cCtx = document.getElementById('pOut'+idx).getContext('2d');
        const kCtx = document.getElementById('pKey'+idx).getContext('2d');


        const pImg = pCtx.createImageData(64, 64);
        const cImg = cCtx.createImageData(64, 64);
        const kImg = kCtx.createImageData(64, 64);


        let pFreq = new Array(256).fill(0);
        let cFreq = new Array(256).fill(0);
        let kFreq = new Array(256).fill(0);

        for (let i = 0; i < Math.min(plain.length, 4096); i++) {{
          const pv = plain.charCodeAt(i);
          const cv = cipher.charCodeAt(i);
          const kv = pv ^ cv;

          pFreq[pv]++; cFreq[cv]++; kFreq[kv]++;
          const j = i * 4;
          pImg.data[j]=pv; pImg.data[j+1]=pv; pImg.data[j+2]=pv; pImg.data[j+3]=255;
          cImg.data[j]=cv; cImg.data[j+1]=cv; cImg.data[j+2]=cv; cImg.data[j+3]=255;
          kImg.data[j]=kv; kImg.data[j+1]=kv; kImg.data[j+2]=kv; kImg.data[j+3]=255;

        }}
        pCtx.putImageData(pImg, 0, 0);
        cCtx.putImageData(cImg, 0, 0);
        kCtx.putImageData(kImg, 0, 0);


        drawHist('hIn'+idx, pFreq, '#a78bfa');
        drawHist('hOut'+idx, cFreq, '#38bdf8');
        drawHist('hKey'+idx, kFreq, '#4ade80');
      }}
    }}

    function drawHist(id, freq, color) {{
      const c = document.getElementById(id);
      const ctx = c.getContext('2d');
      ctx.clearRect(0, 0, c.width, c.height);
      const mx = Math.max(...freq);
      ctx.fillStyle = color;
      for (let i = 0; i < 256; i++) {{
        const h = (freq[i] / mx) * c.height;
        ctx.fillRect(i, c.height - h, 1, h);
      }}
    }}

    renderAll();
  </script>
</body>
</html>"""
    return html

# ─────────────────── Main Flow ───────────────────

def run_single_image(pixel_data, name, description, idx):
    """Load one image, encrypt on FPGA, dump results, compute stats."""
    tcl_path = os.path.join(PROJECT_DIR, f"_temp_load_{idx}.tcl")

    print(f"\n{'='*55}")
    print(f"  IMAGE {idx+1}: {name}")
    print(f"{'='*55}")

    # Step 1: Generate TCL and load into FPGA
    print("  [1/3] Generating TCL load script...")
    generate_load_tcl(pixel_data, tcl_path)
    print(f"        → {len(pixel_data)} bytes → {len(pixel_data)//4} mwr commands")

    print("  [2/3] Uploading to FPGA Input BRAM via JTAG...")
    if not load_image_to_fpga(tcl_path):
        print("  ❌ XSCT load failed! Make sure the board is connected.")
        sys.exit(1)
    print("        ✅ Upload complete!")

    # Step 2: User presses button
    print("")
    print("  ┌─────────────────────────────────────────────────┐")
    print("  │  Press BTNC on the Nexys 4 DDR board NOW.       │")
    print("  │  Wait for GREEN LED, then press ENTER here.     │")
    print("  └─────────────────────────────────────────────────┘")
    input("  >>> ")

    # Step 3: Dump BRAMs
    print("  [3/3] Extracting encrypted data from Output BRAM...")
    if not dump_bram():
        print("  ❌ BRAM dump failed!")
        sys.exit(1)

    output_data = read_raw_file("output_image.raw")
    print(f"        ✅ Captured {len(output_data)} encrypted bytes")

    # Compute statistics
    entropy    = calc_entropy(output_data)
    bit_bal    = calc_bit_balance(output_data)
    chi2       = calc_chi_square(output_data)
    corr_in    = calc_correlation(pixel_data)
    corr_out   = calc_correlation(output_data)

    print(f"        Entropy:     {entropy:.4f} bits/byte (ideal: 8.0)")
    print(f"        Bit Balance: {bit_bal:.2f}% ones")
    print(f"        Chi-Square:  {chi2:.1f} (ideal: ~255)")
    print(f"        Correlation: {corr_in:.4f} (input) → {corr_out:.4f} (output)")



    # Cleanup temp file
    try:
        os.remove(tcl_path)
    except OSError:
        pass

    return {
        'name': name,
        'description': description,
        'input_data': pixel_data,
        'output_data': output_data,
        'entropy': entropy,
        'bit_balance': bit_bal,
        'chi_square': chi2,
        'corr_input': corr_in,
        'corr_output': corr_out,
    }


def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║  AES-128 Multi-Image FPGA Encryption Demonstrator   ║")
    print("║  Nexys 4 DDR — Custom AES IP Core                   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print("This script will test 3 different images on your FPGA.")
    print("For each image you will need to press BTNC once.")
    print()

    images = [
        generate_gradient(),
        generate_checkerboard(),
        generate_concentric_circles(),
    ]

    results = []
    for idx, (pixels, name, desc) in enumerate(images):
        result = run_single_image(pixels, name, desc, idx)
        results.append(result)

    # Generate final dashboard
    print("\n" + "="*55)
    print("  GENERATING FINAL DASHBOARD")
    print("="*55)

    timestamp = time.strftime("%B %d, %Y at %I:%M:%S %p")
    html = generate_html(results, timestamp)

    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n  ✅ Dashboard saved to:")
    print(f"     {HTML_OUTPUT}")
    print(f"\n  Open it in your browser to see all 3 encrypted images!")
    print(f"\n  Summary:")
    print(f"  ┌─────────────────────┬──────────┬───────────┬──────────┐")
    print(f"  │ Image               │ Entropy  │ Bit Bal.  │ Chi-Sq.  │")
    print(f"  ├─────────────────────┼──────────┼───────────┼──────────┤")
    for r in results:
        name = r['name'][:19].ljust(19)
        print(f"  │ {name} │ {r['entropy']:7.4f}  │ {r['bit_balance']:6.2f}%   │ {r['chi_square']:7.1f}  │")
    print(f"  └─────────────────────┴──────────┴───────────┴──────────┘")
    print()


if __name__ == "__main__":
    main()
