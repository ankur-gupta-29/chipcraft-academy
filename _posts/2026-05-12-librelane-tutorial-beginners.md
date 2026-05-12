---
layout: post
title: "LibreLane Tutorial — Open-Source ASIC Flow for Beginners"
description: "A step-by-step guide to running your first ASIC design through LibreLane, the modern open-source RTL-to-GDSII flow."
date: 2026-05-12
category: ASIC Flow
tags: [asic, librelane, openlane, rtl-to-gdsii, open-source, tutorial]
---

LibreLane is a modern, open-source RTL-to-GDSII flow — the pipeline that takes your Verilog code and produces a layout file ready for chip fabrication. It builds on the foundation of OpenLane but with a cleaner, more modular Python-based architecture.

In this tutorial, you'll go from a simple Verilog module to a complete GDSII layout using LibreLane and the free SkyWater 130nm PDK — entirely at zero cost.

---

## What Is LibreLane?

LibreLane is an automated ASIC implementation flow that chains together open-source EDA tools:

```
Verilog RTL
    ↓
Yosys          → Logic synthesis (RTL → gate netlist)
    ↓
OpenROAD       → Floorplanning, placement, CTS, routing
    ↓
Magic          → DRC (Design Rule Checks)
    ↓
Netgen         → LVS (Layout vs Schematic)
    ↓
GDSII Layout   → Ready for fabrication
```

It was developed as a next-generation successor to OpenLane, with a cleaner Python-based configuration system and better modularity. It targets the **SkyWater 130nm PDK** — a fully open-source process design kit supported by Google.

---

## Prerequisites

Before starting, you need:

- A Linux machine, WSL2 (Windows), or macOS
- Docker installed
- Basic Verilog knowledge
- ~15 GB free disk space (for the PDK)

---

## Step 1: Install Docker

LibreLane runs inside Docker containers — no tool installation needed beyond Docker itself.

**Ubuntu / WSL2:**
```bash
sudo apt update
sudo apt install docker.io
sudo usermod -aG docker $USER
newgrp docker
```

**Verify:**
```bash
docker --version
# Docker version 24.x.x
```

---

## Step 2: Install LibreLane

```bash
pip3 install librelane
```

Verify the install:
```bash
librelane --version
```

---

## Step 3: Download the SkyWater 130nm PDK

LibreLane uses **Volare** to manage PDK versions:

```bash
pip3 install volare
volare enable --pdk sky130
```

This downloads the SkyWater 130nm PDK (~10 GB). Go make a coffee.

Set the PDK environment variable:
```bash
export PDK_ROOT=$HOME/.volare
export PDK=sky130A
```

Add these to your `~/.bashrc` so they persist.

---

## Step 4: Create Your Design

Let's implement a simple 8-bit counter as our first design.

Create a project directory:
```bash
mkdir -p ~/librelane_projects/counter/src
cd ~/librelane_projects/counter
```

Create the RTL file `src/counter.v`:
```verilog
module counter #(
  parameter WIDTH = 8
)(
  input  wire             clk,
  input  wire             rst,
  input  wire             en,
  output reg  [WIDTH-1:0] count
);
  always @(posedge clk) begin
    if (rst)
      count <= 0;
    else if (en)
      count <= count + 1;
  end
endmodule
```

---

## Step 5: Create the LibreLane Configuration

Create `config.json` in your project root:

```json
{
  "meta": {
    "version": 2
  },
  "PDK": "sky130A",
  "DESIGN_NAME": "counter",
  "VERILOG_FILES": ["src/counter.v"],
  "CLOCK_PORT": "clk",
  "CLOCK_PERIOD": 10.0,
  "FP_CORE_UTIL": 40,
  "PL_TARGET_DENSITY": 0.5,
  "DIE_AREA": "0 0 100 100",
  "FP_SIZING": "absolute"
}
```

**Key config parameters explained:**

| Parameter | Meaning |
|-----------|---------|
| `CLOCK_PERIOD` | Target clock period in ns (10ns = 100 MHz) |
| `FP_CORE_UTIL` | Core utilization % (40 = use 40% of die area) |
| `PL_TARGET_DENSITY` | Placement density (0.5 = 50% filled) |
| `DIE_AREA` | Die dimensions in microns (x0 y0 x1 y1) |

---

## Step 6: Run the Flow

From your project directory:

```bash
librelane config.json
```

LibreLane will run all stages automatically. You'll see output like:

```
[INFO] Running synthesis...
[INFO] Running floorplan...
[INFO] Running placement...
[INFO] Running CTS (Clock Tree Synthesis)...
[INFO] Running routing...
[INFO] Running DRC...
[INFO] Running LVS...
[INFO] Flow complete!
```

This takes **5–15 minutes** depending on your machine.

---

## Step 7: Examine the Results

Results are saved in `runs/RUN_<timestamp>/`:

```
runs/RUN_2026.05.12_10.30.00/
├── final/
│   ├── gds/counter.gds        ← Final GDSII layout
│   ├── lef/counter.lef        ← Abstract layout (LEF)
│   ├── nl/counter.nl.v        ← Gate-level netlist
│   └── spef/counter.spef      ← Parasitics
├── reports/
│   ├── synthesis/             ← Yosys synthesis reports
│   ├── signoff/
│   │   ├── drc/               ← DRC results
│   │   └── lvs/               ← LVS results
│   └── timing/                ← STA timing reports
└── logs/                      ← Tool logs
```

### View Key Reports

**Check timing (did we meet 100 MHz?):**
```bash
cat runs/RUN_*/reports/signoff/*-sta.rpt | grep "wns\|tns"
```
- `wns` (Worst Negative Slack) should be ≥ 0 — positive means timing is met
- `tns` (Total Negative Slack) should be 0

**Check DRC:**
```bash
cat runs/RUN_*/reports/signoff/drc/sky130*.rpt | tail -20
```
You want: `Total DRC violations: 0`

**Check utilization:**
```bash
cat runs/RUN_*/reports/synthesis/1-synthesis.AREA_0.rpt
```

---

## Step 8: View the Layout in KLayout

Install KLayout (free):
```bash
sudo apt install klayout   # Ubuntu
# or download from klayout.de
```

Open your GDSII:
```bash
klayout runs/RUN_*/final/gds/counter.gds
```

You'll see your routed layout — standard cells placed on a grid, metal routing layers connecting them. For an 8-bit counter you should see a small, compact block.

---

## Step 9: Understand What Just Happened

Here's what LibreLane did under the hood:

### Synthesis (Yosys)
Converted your Verilog `always` block into sky130 standard cells — actual NAND gates, flip-flops, buffers from the SkyWater library.

### Floorplanning (OpenROAD)
Defined the chip boundary and placed I/O pins (clk, rst, en, count[7:0]) around the edges.

### Placement (OpenROAD)
Arranged standard cells inside the core area, optimizing for timing and wire length.

### Clock Tree Synthesis (OpenROAD)
Built a balanced clock distribution network so every flip-flop sees the clock at nearly the same time (minimizing clock skew).

### Routing (OpenROAD)
Connected all cell pins with metal wires across 5 routing layers (met1–met5 in sky130).

### DRC (Magic)
Checked every shape against SkyWater's manufacturing rules — minimum widths, spacings, enclosures.

### LVS (Netgen)
Compared the routed layout's connectivity against the original netlist to confirm they match.

---

## Common Issues and Fixes

### "Timing not met" (negative slack)
```json
// Increase clock period in config.json
"CLOCK_PERIOD": 20.0   // Try 50 MHz instead of 100 MHz
```

### "DRC violations"
Usually caused by routing density. Try:
```json
"PL_TARGET_DENSITY": 0.4,   // Reduce density
"FP_CORE_UTIL": 35
```

### "No connections made" / synthesis fails
Check your Verilog for latches or combinational loops. LibreLane will print the Yosys error — read it carefully.

### Docker permission denied
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

---

## Going Further

### Try a More Complex Design

Once the counter works, try:

```verilog
// FIFO, UART TX, PWM controller, or simple ALU
// All good candidates for a first "real" ASIC flow run
```

### Submit for Free Fabrication

Google's **Open MPW shuttle** program lets you submit designs for free fabrication on SkyWater 130nm. Chips come back in ~6 months.

Check open shuttle slots at: [efabless.com/open_shuttle_program](https://efabless.com/open_shuttle_program)

### Explore the OpenROAD GUI

```bash
openroad -gui
```

OpenROAD has a full GUI for interactive floorplanning, placement visualization, and timing analysis.

---

## LibreLane vs OpenLane — What's Different?

| | OpenLane | LibreLane |
|-|----------|-----------|
| **Config format** | Tcl + JSON | JSON (v2, cleaner) |
| **Architecture** | Monolithic | Modular Python |
| **Customization** | Harder | Easier (Python steps) |
| **PDK support** | sky130, gf180 | sky130, gf180, more |
| **Status** | Mature, stable | Modern, actively developed |

If you're learning, either works. LibreLane's cleaner Python config makes it easier to understand what each step does.

---

## Summary

```
1. Install Docker + LibreLane + Volare
2. Write your Verilog RTL
3. Create config.json with PDK and timing settings
4. Run: librelane config.json
5. Check: timing slack ≥ 0, DRC = 0 violations
6. View layout in KLayout
```

You just ran a complete ASIC flow — the same fundamental steps used to design chips that go into real products, using free and open-source tools.

---

*Want a structured PDF reference for the full ASIC flow? Check the [Shop](/shop) for the ASIC Design Flow guide.*
