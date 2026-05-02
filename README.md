<p align="center">
  <img src="report_images/dashboard_image.png" alt="AES-128 Hardware Encryption Dashboard" width="900"/>
</p>

<h1 align="center">ðŸ” AES-128 Image Encryption Hardware Accelerator</h1>

<p align="center">
  <strong>A FIPS-197 Compliant Cryptographic IP Core on Xilinx Artix-7 FPGA</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FPGA-Xilinx%20Artix--7-blue?style=for-the-badge&logo=xilinx" alt="FPGA"/>
  <img src="https://img.shields.io/badge/Standard-FIPS--197%20AES--128-green?style=for-the-badge" alt="FIPS-197"/>
  <img src="https://img.shields.io/badge/Interface-AXI4--Lite-orange?style=for-the-badge" alt="AXI4-Lite"/>
  <img src="https://img.shields.io/badge/Mode-CTR%20(Counter)-purple?style=for-the-badge" alt="CTR"/>
  <img src="https://img.shields.io/badge/Latency-12%20Cycles-red?style=for-the-badge" alt="Latency"/>
  <img src="https://img.shields.io/badge/Tool-Vivado%202024.2-teal?style=for-the-badge" alt="Vivado"/>
</p>

<p align="center">
  <em>End-to-end hardware-accelerated image encryption with real-time JTAG-based cryptographic verification dashboard, <br/>synthesized and validated on Digilent Nexys 4 DDR (xc7a100tcsg324-1)</em>
</p>

---

## ðŸ“‹ Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Hardware Accelerator Pipeline](#-hardware-accelerator-pipeline)
- [AES-128 IP Core Microarchitecture](#-aes-128-ip-core-microarchitecture)
- [Project Structure](#-project-structure)
- [AXI4-Lite Register Map](#-axi4-lite-register-map)
- [FPGA Implementation Results](#-fpga-implementation-results)
- [Cryptographic Validation](#-cryptographic-validation)
- [Getting Started](#-getting-started)
- [Real-Time Dashboard](#-real-time-dashboard)
- [Hardware Demo](#-hardware-demo)
- [Troubleshooting](#-troubleshooting)
- [References](#-references)
- [License](#-license)

---

## ðŸŽ¯ Overview

This project implements a **complete hardware-accelerated AES-128 CTR-mode image encryption system** on the Digilent Nexys 4 DDR FPGA. At its core is a custom-designed, fully synthesizable **AES-128 encryption engine** (FIPS-197 compliant) packaged as a reusable Vivado IP core with an **AXI4-Lite slave interface**. The accelerator is integrated into a MicroBlaze soft-processor SoC, enabling real-time image encryption with automated verification against a software golden reference.

> **Why CTR Mode?** Counter mode transforms the block cipher into a stream cipher â€” only the encryption direction is needed (no inverse S-box or inverse MixColumns), making decryption trivially symmetric. CTR also eliminates the ECB pattern-leakage vulnerability, as each block is XORed with a unique keystream derived from an incrementing counter.

### What Makes This a Hardware Accelerator?

| Aspect | Software-Only | This Hardware Accelerator |
|--------|--------------|--------------------------|
| **AES Engine** | CPU instruction loop | Dedicated RTL datapath |
| **Latency** | ~100+ cycles/block (CPU) | **12 cycles/block** (fixed pipeline) |
| **Throughput** | Sequential, cache-dependent | **Deterministic, wire-speed** |
| **Key Expansion** | Computed per-block | **Combinational, single-cycle** |
| **Integration** | Library call | **Memory-mapped AXI peripheral** |
| **Reusability** | Platform-specific binary | **Portable Verilog IP core** |

---

## âœ¨ Key Features

- ðŸ”’ **FIPS-197 Compliant** â€” Full AES-128 implementation with all 10 rounds, S-box, ShiftRows, MixColumns, and key expansion
- âš¡ **12-Cycle Latency** â€” Deterministic encryption pipeline: 1 cycle key expansion + 11 round iterations
- ðŸ”Œ **AXI4-Lite Interface** â€” Standard AMBA bus integration for seamless SoC connectivity
- ðŸ–¼ï¸ **Image Encryption** â€” Real-time 64Ã—64 grayscale image encryption (256 AES blocks) with visual verification
- ðŸ“Š **Cryptographic Dashboard** â€” Live HTML dashboard with entropy analysis, histogram equalization, and statistical quality indicators
- ðŸ”„ **One-Command Build** â€” Complete TCL automation: IP packaging â†’ Block Design â†’ Address assignment
- âœ… **Byte-Perfect Verification** â€” Automated comparison against Python `cryptography` library golden reference
- ðŸŽ›ï¸ **JTAG Memory Access** â€” Direct BRAM read/write via Xilinx XSCT for automated test pipelines

---

## ðŸ—ï¸ System Architecture

<p align="center">
  <img src="report_images/block_design.png" alt="Vivado Block Design" width="900"/>
</p>
<p align="center"><em>Fig 1. Vivado IP Integrator Block Design â€” MicroBlaze SoC with custom AES-128 AXI-Lite accelerator</em></p>

The system is built around a **MicroBlaze soft-processor** orchestrating data flow between memory-mapped peripherals over an AXI4 interconnect:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        Nexys 4 DDR FPGA                            â”‚
â”‚                                                                     â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     AXI4 Interconnect      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”‚
â”‚   â”‚          â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º â”‚  AES-128 IP Core â”‚     â”‚
â”‚   â”‚          â”‚                             â”‚  (AXI4-Lite)     â”‚     â”‚
â”‚   â”‚ Micro-   â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚  12-cycle engine â”‚     â”‚
â”‚   â”‚ Blaze    â”‚                â”‚            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â”‚
â”‚   â”‚ CPU      â”‚â—„â”€â”€â”€â”           â”‚                                     â”‚
â”‚   â”‚          â”‚    â”‚           â”‚            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”‚
â”‚   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â”‚           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º â”‚  Input BRAM      â”‚     â”‚
â”‚                   â”‚                        â”‚  (8KB, COE init) â”‚     â”‚
│                   │                        └──────────────────┘     │
│                   │                                                 │
│                   │                        ┌──────────────────┐     │
│                   │           ┌───────────►│  Output BRAM     │     │
│                   │           │            │  (8KB)           │     │
│                   │           │            └──────────────────┘     │
│                   │           │                                     │
│                   └───────────┘            ┌──────────────────┐     │
│                                   ┌───────►│  AXI GPIO        │     │
│                                   │        │  LEDs + Buttons  │     │
│                                   │        └──────────────────┘     │
└───────────────┬───────────────────┼─────────────────────────────────┘
                │                   │
       ┌────────▼────────┐    ┌─────▼────┐
       │  Host PC        │    │  BTNC    │
       │  JTAG (XSCT)    │    │  LED16   │
       │  Python Scripts  │    └──────────┘
       └─────────────────┘
```

---

## ðŸ”„ Hardware Accelerator Pipeline

The following flowchart illustrates the complete encryption pipeline â€” from image loading to cryptographic verification:

```mermaid
flowchart TD
    A["ðŸ–¼ï¸ Input Image<br/>(64Ã—64 grayscale)"] --> B["ðŸ“¦ Preprocess<br/>Python: preprocess_image.py"]
    B --> C["ðŸ’¾ .COE File<br/>BRAM Initialization"]
    C --> D["âš™ï¸ Vivado Synthesis<br/>+ Implementation"]
    D --> E["ðŸ“¥ Bitstream â†’ FPGA<br/>Program Device"]
    E --> F["ðŸŽ›ï¸ MicroBlaze Boot<br/>Wait for BTNC press"]
    
    F --> G{"ðŸ”˜ Button<br/>Pressed?"}
    G -->|No| F
    G -->|Yes| H["ðŸ”‘ Load AES Key<br/>to IP Core registers"]
    
    H --> I["ðŸ“– Read Block from<br/>Input BRAM"]
    I --> J["ðŸ”¢ Write Counter<br/>to AES IP"]
    J --> K["âš¡ AES-128 Encrypt<br/>(12 clock cycles)"]
    K --> L["ðŸ” XOR Keystream<br/>âŠ• Plaintext"]
    L --> M["ðŸ’¾ Write Cipher<br/>to Output BRAM"]
    M --> O["âž• Increment<br/>Counter"]
    
    O --> P{"All 256<br/>blocks?"}
    P -->|No| I
    P -->|Yes| Q["âœ… LED16_G ON<br/>Encryption Complete"]
    
    Q --> R["ðŸ–¥ï¸ JTAG Extract<br/>multi_image_demo.py"]
    R --> S["ðŸ” Verify vs Golden<br/>compare_results.py"]
    S --> T["ðŸ“Š Dashboard<br/>Entropy + Histogram"]

    style A fill:#4a9eff,stroke:#333,color:#fff
    style K fill:#ff6b6b,stroke:#333,color:#fff
    style Q fill:#51cf66,stroke:#333,color:#fff
    style T fill:#cc5de8,stroke:#333,color:#fff
```

---

## ðŸ§  AES-128 IP Core Microarchitecture

The hardware accelerator implements the full FIPS-197 AES-128 algorithm as a **3-state FSM** with combinational round logic:

```mermaid
stateDiagram-v2
    [*] --> IDLE
    
    IDLE --> RUNNING : start pulse â†‘<br/>Key Expand (combinational)<br/>AddRoundKey(state, key)
    
    RUNNING --> RUNNING : round < 10<br/>SubBytes â†’ ShiftRows â†’<br/>MixColumns â†’ AddRoundKey
    
    RUNNING --> DONE : round == 10<br/>SubBytes â†’ ShiftRows â†’<br/>AddRoundKey (no MixColumns)
    
    DONE --> IDLE : Output latched<br/>done â†‘ for 1 cycle
```

### Round Function Datapath

```mermaid
flowchart LR
    subgraph "Rounds 1â€“9"
        A1["128-bit State"] --> B1["SubBytes<br/>(S-box Ã— 16)"]
        B1 --> C1["ShiftRows<br/>(Row rotation)"]
        C1 --> D1["MixColumns<br/>(GF(2â¸) multiply)"]
        D1 --> E1["AddRoundKey<br/>(âŠ• Round Key)"]
        E1 --> A1
    end
    
    subgraph "Round 10 (Final)"
        A2["128-bit State"] --> B2["SubBytes"]
        B2 --> C2["ShiftRows"]
        C2 --> E2["AddRoundKey<br/>(No MixColumns)"]
        E2 --> F2["âœ… Ciphertext"]
    end

    subgraph "Key Schedule"
        K1["128-bit Key"] --> K2["RotWord"]
        K2 --> K3["SubWord"]
        K3 --> K4["âŠ• Rcon"]
        K4 --> K5["44 Words<br/>(11 Round Keys)"]
    end
```

### CTR Mode Operation

```mermaid
flowchart LR
    subgraph "CTR Mode â€” No Decryption Hardware Needed"
        CTR["Counter Block<br/>(128-bit, incremented)"] --> AES["AES-128<br/>Encrypt Only"]
        KEY["Secret Key<br/>(128-bit)"] --> AES
        AES --> KS["Keystream<br/>(128-bit)"]
        PT["Plaintext Block"] --> XOR["âŠ• XOR"]
        KS --> XOR
        XOR --> CT["Ciphertext Block"]
    end
```

> **Implementation Detail:** The entire key schedule (44 words, 1408 bits) is expanded **combinationally** in a single clock cycle using a Verilog `task`. This trades area for latency â€” the expanded keys are stored in a 1408-bit register and indexed per round.

---

## ðŸ“ Project Structure

```
aes128_image_encryption_ipcore_nexys4ddr/
â”‚
â”œâ”€â”€ ðŸ“‚ hw/                              â† Hardware Design
â”‚   â”œâ”€â”€ ðŸ“‚ ip/aes128_axilite/
â”‚   â”‚   â”œâ”€â”€ ðŸ“‚ hdl/
â”‚   â”‚   â”‚   â”œâ”€â”€ aes128_core.v           â† AES-128 FIPS-197 encryption engine (307 lines)
â”‚   â”‚   â”‚   â””â”€â”€ aes128_axilite_wrapper.v â† AXI4-Lite slave interface (237 lines)
â”‚   â”‚   â”œâ”€â”€ component.xml               â† Vivado IP-XACT descriptor
â”‚   â”‚   â””â”€â”€ ðŸ“‚ xgui/                    â† IP Customization GUI
â”‚   â”œâ”€â”€ ðŸ“‚ constraints/
â”‚   â”‚   â””â”€â”€ nexys4ddr_image_crypto.xdc  â† Pin assignments (UART, GPIO, buttons)
â”‚   â””â”€â”€ ðŸ“‚ vivado/
â”‚       â””â”€â”€ create_project.tcl          â† One-command project builder (282 lines)
â”‚
â”œâ”€â”€ ðŸ“‚ sw/                              â† Firmware
â”‚   â””â”€â”€ ðŸ“‚ microblaze/
â”‚       â”œâ”€â”€ main.c                      â† CTR-mode encryption firmware (190 lines)
â”‚       â””â”€â”€ aes_ip_driver.h             â† AXI register access driver (126 lines)
â”‚
â”œâ”€â”€ ðŸ“‚ scripts/                         â† Host-Side Automation
â”‚   â”œâ”€â”€ preprocess_image.py             â† Any image â†’ 64Ã—64 grayscale â†’ .COE
â”‚   â”œâ”€â”€ software_reference_ctr.py       â† Golden reference generator (PyCryptodome)
â”‚   â”œâ”€â”€ reconstruct_image.py            â† Raw cipher bytes â†’ PNG visualization
â”‚   â”œâ”€â”€ compare_results.py             â† Byte-level FPGA vs golden verification
â”‚   â”œâ”€â”€ generate_demo_image.py          â† Synthetic test pattern generator
â”‚   â”œâ”€â”€ pack_coe.py                     â† Raw binary â†’ Vivado .COE format
â”‚   â””â”€â”€ requirements.txt               â† Python dependencies
â”‚
â”œâ”€â”€ ðŸ“‚ sample_assets/                   â† Pre-built Test Vectors
â”‚   â”œâ”€â”€ sample_64x64_gradient.png       â† Original test image
â”‚   â”œâ”€â”€ sample_64x64_gradient.raw       â† Raw 4096 bytes
â”‚   â”œâ”€â”€ sample_64x64_gradient.coe       â† BRAM initialization file
â”‚   â””â”€â”€ sample_64x64_gradient_encrypted_ctr.raw  â† Golden reference output
â”‚
â”œâ”€â”€ ðŸ“‚ report_images/                   â† Documentation Assets
â”‚   â”œâ”€â”€ block_design.png                â† Vivado block design screenshot
â”‚   â”œâ”€â”€ schematic.png                   â† Top-level RTL schematic
â”‚   â”œâ”€â”€ dashboard_image.png             â† Cryptographic analysis dashboard
â”‚   â”œâ”€â”€ dashboard_stats.png             â† statistical quality indicators panel
â”‚   â”œâ”€â”€ hardware_1.jpg                  â† Lab setup photo (board + dashboard)
â”‚   â”œâ”€â”€ hardware_2.jpg                  â† Lab setup photo (statistics panel)
â”‚   â”œâ”€â”€ report_utilization.png          â† FPGA resource utilization
â”‚   â”œâ”€â”€ report_timing.png              â† Timing analysis summary
â”‚   â”œâ”€â”€ report_power.png               â† Power analysis report
â”‚   â”œâ”€â”€ project_summary.png            â† Vivado project summary
â”‚   â”œâ”€â”€ vitis_project.png              â† Vitis IDE build success
â”‚   â””â”€â”€ python_terminal.png            â† Dashboard automation terminal
â”‚
â”œâ”€â”€ multi_image_demo.py                   â† JTAG-based live dashboard generator
â”œâ”€â”€ multi_image_demo.py                 â† Multi-image automated test pipeline
â””â”€â”€ README.md                           â† This file
```

---

## ðŸ“ AXI4-Lite Register Map

The AES-128 IP core exposes a simple, flat register interface for software control:

| Offset | Name | Access | Width | Description |
|:------:|:----:|:------:|:-----:|:------------|
| `0x00` | **CTRL** | W | 32 | `bit[0]` = START pulse, `bit[1]` = SOFT_RST |
| `0x04` | **STATUS** | R | 32 | `bit[0]` = DONE (latched until next START) |
| `0x08` | **KEY_W0** | W | 32 | AES Key `[127:96]` |
| `0x0C` | **KEY_W1** | W | 32 | AES Key `[95:64]` |
| `0x10` | **KEY_W2** | W | 32 | AES Key `[63:32]` |
| `0x14` | **KEY_W3** | W | 32 | AES Key `[31:0]` |
| `0x18` | **DIN_W0** | W | 32 | Data Input `[127:96]` |
| `0x1C` | **DIN_W1** | W | 32 | Data Input `[95:64]` |
| `0x20` | **DIN_W2** | W | 32 | Data Input `[63:32]` |
| `0x24` | **DIN_W3** | W | 32 | Data Input `[31:0]` |
| `0x28` | **DOUT_W0** | R | 32 | Data Output `[127:96]` |
| `0x2C` | **DOUT_W1** | R | 32 | Data Output `[95:64]` |
| `0x30` | **DOUT_W2** | R | 32 | Data Output `[63:32]` |
| `0x34` | **DOUT_W3** | R | 32 | Data Output `[31:0]` |

**Base Address:** `0x44A0_0000` (configured in TCL automation)

---

## ðŸ“Š FPGA Implementation Results

### Resource Utilization

<p align="center">
  <img src="report_images/report_utilization.png" alt="FPGA Resource Utilization" width="850"/>
</p>
<p align="center"><em>Fig 2. Post-implementation hierarchical resource utilization (Vivado 2024.2)</em></p>

| Resource | Used | Available | Utilization |
|:---------|:----:|:---------:|:-----------:|
| **Slice LUTs** | 5,511 | 63,400 | 8.7% |
| **Slice Registers** | 3,697 | 126,800 | 2.9% |
| **Block RAM Tiles** | 16 | 135 | 11.9% |
| **DSPs** | 3 | 240 | 1.3% |
| **F7 Muxes** | 569 | 31,700 | 1.8% |
| **Bonded IOBs** | 9 | 210 | 4.3% |

> **AES Core Alone:** 3,709 LUTs, 2,114 Registers, 4 BRAMs â€” a compact, area-efficient implementation suitable for resource-constrained embedded systems.

### Timing Analysis

<p align="center">
  <img src="report_images/report_timing.png" alt="Timing Summary" width="750"/>
</p>
<p align="center"><em>Fig 3. Design timing summary â€” all constraints met with positive slack</em></p>

| Metric | Value | Status |
|:-------|:-----:|:------:|
| **Worst Negative Slack (WNS)** | 0.776 ns | âœ… Met |
| **Worst Hold Slack (WHS)** | 0.016 ns | âœ… Met |
| **Worst Pulse Width Slack** | 3.000 ns | âœ… Met |
| **Failing Endpoints** | 0 | âœ… |
| **Total Endpoints** | 11,378 | â€” |

### Power Analysis

<p align="center">
  <img src="report_images/report_power.png" alt="Power Report" width="600"/>
</p>
<p align="center"><em>Fig 4. On-chip power breakdown â€” total 0.236 W</em></p>

| Component | Power | Percentage |
|:----------|:-----:|:----------:|
| **Total On-Chip** | 0.236 W | 100% |
| Dynamic | 0.138 W | 58% |
| Device Static | 0.098 W | 42% |
| **Junction Temp** | 26.1Â°C | â€” |

---

## ðŸ” Cryptographic Validation

### Visual Proof: Plaintext â†’ Ciphertext â†’ Keystream

<p align="center">
  <img src="report_images/dashboard_image.png" alt="Cryptographic Analysis Dashboard" width="900"/>
</p>
<p align="center"><em>Fig 5. Real-time cryptographic analysis dashboard showing plaintext, hardware ciphertext, and extracted keystream with pixel distribution histograms</em></p>

### Observed Statistical Indicators

> **Note:** The metrics below are lightweight observational indicators computed by our dashboard — they are **not** a formal NIST SP 800-22 randomness test suite. They serve as practical sanity checks for ciphertext quality.

<p align="center">
  <img src="report_images/dashboard_stats.png" alt="Statistical Indicators" width="700"/>
</p>
<p align="center"><em>Fig 6. Hardware diagnostics and statistical quality indicators</em></p>

| Metric | Measured | Ideal | Verdict |
|:-------|:--------:|:-----:|:-------:|
| **Shannon Entropy** | 7.9555 bits/byte | 8.0 | âœ… Near-ideal randomness |
| **Bit Balance (1s)** | 50.11% | 50.0% | âœ… Balanced |
| **Bit Balance (0s)** | 49.89% | 50.0% | âœ… Balanced |
| **Chi-Square** | 250.50 | ~255.0 | âœ… Uniform distribution |
| **Data Integrity** | VERIFIED PASS | â€” | âœ… Byte-perfect match |

### Encryption Visualization

| Original (Plaintext) | Encrypted (Ciphertext) |
|:--------------------:|:---------------------:|
| <img src="sample_assets/sample_64x64_gradient_preview.png" width="200"/> | <img src="sample_assets/golden_encrypted.png" width="200"/> |
| Structured gradient pattern | Pseudorandom noise (ideal) |

### Demo Parameters

| Parameter | Value |
|:----------|:------|
| **Image** | 64Ã—64 grayscale (4,096 bytes â†’ 256 AES blocks) |
| **AES Key** | `00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F` |
| **Initial Counter (IV)** | `F0 E0 D0 C0 B0 A0 90 80 70 60 50 40 30 20 10 00` |
| **Data Extraction** | JTAG (XSCT `mrd` command) |
| **Input BRAM** | `0xC000_0000` (8 KB) |
| **Output BRAM** | `0xC200_0000` (8 KB) |
| **AES IP Base** | `0x44A0_0000` (4 KB) |

---

## ðŸš€ Getting Started

### Prerequisites

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| **Vivado** | 2024.2 | Synthesis, implementation, bitstream |
| **Vitis Unified IDE** | 2024.2 | MicroBlaze firmware development |
| **Python** | 3.8+ | Host scripts, verification, dashboard |
| **Hardware** | Nexys 4 DDR | Target FPGA board |

### Phase 0 â€” Install Python Dependencies

```bash
pip install -r scripts/requirements.txt
```

### Phase 1 â€” Generate Golden Reference (Optional)

> The golden reference is pre-included in `sample_assets/`. Run only if you change the key or counter.

```bash
python scripts/software_reference_ctr.py sample_assets/sample_64x64_gradient.raw \
    --output sample_assets/sample_64x64_gradient_encrypted_ctr.raw

python scripts/reconstruct_image.py sample_assets/sample_64x64_gradient_encrypted_ctr.raw \
    --output sample_assets/golden_encrypted.png
```

### Phase 2 â€” Build Vivado Project (One Command)

```tcl
# In Vivado 2024.2 TCL Console:
cd {/path/to/aes128_image_encryption_ipcore_nexys4ddr}
source hw/vivado/create_project.tcl
```

This single script automates:
1. âœ… AES-128 IP packaging with AXI4-Lite interface
2. âœ… Vivado project creation for xc7a100tcsg324-1
3. âœ… Complete block design assembly (MicroBlaze + AES + BRAMs + UART + GPIO)
4. âœ… Address map configuration
5. âœ… HDL wrapper generation

### Phase 3 â€” Synthesize & Implement

In Vivado Flow Navigator:
1. **Run Synthesis** â†’ wait (~5â€“10 min)
2. **Run Implementation** â†’ wait (~10â€“15 min)
3. **Generate Bitstream** â†’ wait (~5 min)

### Phase 4 â€” Export & Build Firmware

1. **File â†’ Export â†’ Export Hardware** (include bitstream)
2. Open **Vitis Unified IDE**
3. Create platform from `.xsa` file
4. Import `sw/microblaze/main.c` and `aes_ip_driver.h`
5. **Build** â†’ 0 errors expected

<p align="center">
  <img src="report_images/vitis_project.png" alt="Vitis Build Success" width="700"/>
</p>
<p align="center"><em>Fig 7. Vitis Unified IDE â€” successful build of AES firmware application</em></p>

### Phase 5 â€” Program & Run

1. Connect Nexys 4 DDR via USB-JTAG
2. **Program Device** in Vitis
3. **Run â†’ Launch Hardware**
4. Press **BTNC** (center button) to trigger encryption
5. LED16 turns **Red** (encrypting) â†’ **Green** (done)

### Phase 6 — Extract & Verify (JTAG)

The project uses **JTAG-based BRAM extraction** via Xilinx XSCT for reliable, automated data capture:

```bash
# Run the full multi-image automated pipeline
python multi_image_demo.py
```

This script automatically:
1. ✅ Uploads image data to Input BRAM via JTAG
2. ✅ Triggers encryption on the MicroBlaze
3. ✅ Extracts ciphertext from Output BRAM via JTAG
4. ✅ Compares against the software golden reference
5. ✅ Generates an HTML dashboard with visual + statistical analysis

Expected output:
```
✅  PERFECT MATCH — FPGA output is cryptographically correct!
```

---

## ðŸ“¡ Real-Time Dashboard

The project includes an automated JTAG-based dashboard that extracts BRAM contents directly from the FPGA and generates a live HTML cryptographic analysis report:

<p align="center">
  <img src="report_images/python_terminal.png" alt="Dashboard Automation" width="700"/>
</p>
<p align="center"><em>Fig 8. Dashboard automation script â€” JTAG upload, encrypt, extract, visualize</em></p>

```bash
python multi_image_demo.py
```

The dashboard computes and displays:
- **Plaintext vs. Ciphertext** side-by-side with pixel-level rendering
- **Extracted Keystream** (Plain âŠ• Cipher) visualization
- **Pixel Distribution Histograms** for all three views
- **Shannon Entropy** of ciphertext (ideal: 8.0 bits/byte)
- **Bit Balance Test** (50/50 split of 1s and 0s)
- **Chi-Square Uniformity Test** (ideal: ~255.0 for 256 bins)

---

## ðŸ”¬ Hardware Demo

<p align="center">
  <img src="report_images/hardware_1.jpg" alt="Lab Setup" width="700"/>
</p>
<p align="center"><em>Fig 9. Lab demonstration setup â€” Nexys 4 DDR FPGA connected to host running the cryptographic analysis dashboard</em></p>

<p align="center">
  <img src="report_images/hardware_2.jpg" alt="Statistical Quality Dashboard" width="700"/>
</p>
<p align="center"><em>Fig 10. Hardware diagnostics and Statistical Quality Dashboarded in real-time from FPGA memory</em></p>

<p align="center">
  <img src="report_images/schematic.png" alt="Top-Level Schematic" width="700"/>
</p>
<p align="center"><em>Fig 11. Top-level RTL schematic â€” I/O buffers wrapping the image_crypto_bd block design</em></p>

---

## ðŸ› ï¸ Troubleshooting

| Problem | Solution |
|:--------|:--------|
| TCL script fails at IP packaging | Ensure Vivado **2024.2** is used. Verify `hw/ip/aes128_axilite/hdl/` contains both `.v` files |
| `component.xml` already exists | Delete `hw/ip/aes128_axilite/component.xml` and re-run TCL |
| Synthesis error on AES core | Both files must be `.v` (Verilog-2001), not `.sv` |
| XSCT connection fails | Ensure only one JTAG client is connected. Close Vitis hardware manager if open |
| Mismatch in compare_results | Verify key/counter in `main.c` matches `software_reference_ctr.py` defaults |
| Vitis can't find `xparameters.h` | Re-export `.xsa` after any hardware changes |
| Dashboard not updating | Ensure XSCT path in `multi_image_demo.py` matches your Vitis installation |

---

## ðŸ“š References

1. **NIST FIPS 197** â€” Advanced Encryption Standard (AES), November 2001
2. **NIST SP 800-38A** â€” Recommendation for Block Cipher Modes of Operation (CTR Mode)
3. **Xilinx UG984** â€” MicroBlaze Processor Reference Guide
4. **Xilinx PG078** â€” AXI4-Lite Interface Specification
5. **Digilent Nexys 4 DDR** â€” Reference Manual (xc7a100tcsg324-1)

---

## âš–ï¸ License

This project is released for **academic and educational purposes**. The AES-128 IP core is an original implementation based on the public FIPS-197 specification. Feel free to use, modify, and extend for research or coursework.

---

<p align="center">
  <strong>Built with â¤ï¸ on Xilinx Artix-7 | Vivado 2024.2 | Vitis Unified IDE</strong>
</p>

<p align="center">
  <img src="report_images/project_summary.png" alt="Vivado Project Summary" width="700"/>
</p>
<p align="center"><em>Vivado Project Summary â€” Synthesis âœ… | Implementation âœ… | Timing âœ… | Power âœ…</em></p>
