---
layout: post
title: "Static Timing Analysis (STA) — A Complete Beginner's Guide"
description: "A detailed, visual guide to Static Timing Analysis: timing paths, setup & hold time, slack, SDC constraints, and how to fix violations."
date: 2026-05-13
category: STA
tags: [sta, timing, asic, sdc, beginner, vlsi]
---

Static Timing Analysis (STA) is the method used to verify that a digital circuit meets its timing requirements — without running a single simulation. It is one of the most critical skills in ASIC and FPGA design, and a topic that appears in almost every chip design interview.

This guide explains STA from first principles, with diagrams, equations, and real examples.

---

## Why STA Exists

A digital circuit works correctly only if data arrives at every flip-flop's input **before** the clock captures it, and **stays stable long enough** after the clock edge. If it arrives too late or changes too soon — the flip-flop captures garbage, and your chip fails.

Simulation can check a handful of scenarios. STA checks **every possible timing path** in the design mathematically — thousands or millions of paths — in minutes. No test vectors needed.

---

## The Fundamental Concept: The Timing Path

Every STA analysis is about **timing paths**. A timing path is the route data travels from one sequential element (flip-flop or input port) to another.

<img src="{{ '/assets/images/sta-timing-path.svg' | relative_url }}" alt="STA Timing Path Diagram" style="width:100%; border-radius:12px; margin: 1.5rem 0;">

A typical timing path has four elements:

| Element | Description |
|---------|-------------|
| **Startpoint** | Where data is launched (flip-flop clock pin, or input port) |
| **Combinational logic** | Gates the data passes through (AND, OR, MUX, adder…) |
| **Endpoint** | Where data is captured (flip-flop data pin, or output port) |
| **Clock** | Controls when data is launched and captured |

---

## Setup Time and Hold Time

These are the two fundamental timing constraints every flip-flop has:

### Setup Time (T_setup)
The minimum time data must be **stable BEFORE** the clock edge for the flip-flop to correctly capture it.

> If data arrives too late → **Setup violation** → flip-flop captures wrong value

### Hold Time (T_hold)
The minimum time data must remain **stable AFTER** the clock edge.

> If data changes too soon after the clock → **Hold violation** → flip-flop captures wrong value

<img src="{{ '/assets/images/sta-setup-waveform.svg' | relative_url }}" alt="Setup Time Waveform" style="width:100%; border-radius:12px; margin: 1.5rem 0;">

---

## The Setup Timing Equation

For a path from **Launch FF → Combinational Logic → Capture FF**:

```
Data Arrival Time  = T_clk_launch + T_clk-to-Q + T_comb + T_net

Data Required Time = T_clk_capture + T_period - T_setup

Slack (Setup)      = Required Time - Arrival Time
```

**Where:**

| Term | Meaning |
|------|---------|
| `T_clk_launch` | Clock arrival time at launch flop |
| `T_clk-to-Q` | Flip-flop propagation delay (clock edge → Q output) |
| `T_comb` | Total combinational logic delay on the data path |
| `T_net` | Wire/interconnect delay |
| `T_clk_capture` | Clock arrival time at capture flop |
| `T_period` | Clock period (e.g. 10ns for 100 MHz) |
| `T_setup` | Capture flop's setup time requirement |

### The Golden Rule:
```
Slack ≥ 0  →  Timing MET   ✅
Slack < 0  →  Timing VIOLATION ❌
```

### Example Calculation:

```
Clock period     = 10 ns  (100 MHz)
T_clk-to-Q      = 0.3 ns
T_comb           = 6.2 ns
T_net            = 0.8 ns
T_setup          = 0.1 ns
Clock skew       = 0.0 ns (ideal)

Arrival Time     = 0 + 0.3 + 6.2 + 0.8  = 7.3 ns
Required Time    = 0 + 10.0 - 0.1        = 9.9 ns

Slack            = 9.9 - 7.3             = +2.6 ns  ✅ PASS
```

---

## The Hold Timing Equation

Hold analysis checks that data doesn't change **too quickly** after the clock edge:

```
Data Arrival Time  = T_clk_launch + T_clk-to-Q + T_comb_min + T_net_min

Data Required Time = T_clk_capture + T_hold

Slack (Hold)       = Arrival Time - Required Time
```

> **Key difference:** Hold uses **minimum delays** (best-case, fastest paths). Setup uses **maximum delays** (worst-case, slowest paths).

### Hold Example:

```
T_clk-to-Q (min)  = 0.2 ns
T_comb (min)      = 0.1 ns   ← fastest path (maybe a direct wire)
T_net (min)       = 0.05 ns
T_hold            = 0.15 ns

Arrival Time      = 0 + 0.2 + 0.1 + 0.05  = 0.35 ns
Required Time     = 0 + 0.15               = 0.15 ns

Slack             = 0.35 - 0.15            = +0.20 ns  ✅ PASS
```

---

## Clock Skew and Jitter

Real clocks are not perfect. Two effects make timing harder:

### Clock Skew
The difference in clock arrival time between the launch and capture flip-flops, due to different wire lengths or buffer delays in the clock tree.

```
Effective Setup Slack  = Slack - Skew   (skew hurts setup)
Effective Hold  Slack  = Slack + Skew   (skew can help hold)
```

> This is why **Clock Tree Synthesis (CTS)** is a dedicated step in the ASIC flow — to minimize skew.

### Clock Jitter
Cycle-to-cycle variation in the clock period due to PLL noise. STA tools model this as **uncertainty** and subtract it from your timing budget:

```
Setup Slack (with uncertainty) = Slack - T_jitter/2
```

In SDC this is set with:
```tcl
set_clock_uncertainty -setup 0.1 [get_clocks clk]
set_clock_uncertainty -hold  0.05 [get_clocks clk]
```

---

## Types of Timing Paths

There are four types of timing paths in STA:

| Path Type | From | To |
|-----------|------|----|
| **Register-to-Register** | FF clock pin | FF data pin |
| **Input-to-Register** | Input port | FF data pin |
| **Register-to-Output** | FF clock pin | Output port |
| **Input-to-Output** | Input port | Output port |

Register-to-register paths are the most common. Input/output paths require **I/O constraints** in your SDC file.

---

## SDC Constraints — Telling the Tool About Your Clocks

STA tools don't know your design intent — you tell them via **SDC (Synopsys Design Constraints)** files.

### Define a Clock
```tcl
create_clock -name clk -period 10 -waveform {0 5} [get_ports clk]
#            name       10ns period  rise=0 fall=5ns  on port "clk"
```

### Input/Output Delay Constraints
```tcl
# Data from external FF arrives 2ns after clock edge
set_input_delay -max 2.0 -clock clk [get_ports data_in]

# Data must arrive at output FF 1ns before clock edge
set_output_delay -max 1.0 -clock clk [get_ports data_out]
```

### Clock Uncertainty (Jitter + Skew margin)
```tcl
set_clock_uncertainty -setup 0.15 [get_clocks clk]
set_clock_uncertainty -hold  0.05 [get_clocks clk]
```

### False Paths (paths that don't need timing analysis)
```tcl
# Async reset path — not a real timing path
set_false_path -from [get_ports rst_n]

# Between two unrelated clock domains
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]
```

### Multicycle Paths
```tcl
# Data takes 2 cycles to propagate (pipeline with intentional extra cycle)
set_multicycle_path -setup 2 -from [get_cells reg_a] -to [get_cells reg_b]
```

---

## Reading a Timing Report

A typical STA timing report from OpenSTA / PrimeTime looks like this:

```
Startpoint: ff1 (rising edge-triggered flip-flop clocked by clk)
Endpoint:   ff2 (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type:  max (setup check)

  Point                    Incr    Path
  -----------------------------------------------
  clock clk (rise edge)    0.00    0.00
  clock network delay      0.12    0.12
  ff1/CK (DFF_X1)          0.00    0.12 r
  ff1/Q  (DFF_X1)          0.31    0.43 r   ← clk-to-Q delay
  U1/A   (AND2_X1)         0.00    0.43 r
  U1/Z   (AND2_X1)         0.08    0.51 r   ← gate delay
  U2/A   (OR2_X1)          0.00    0.51 r
  U2/Z   (OR2_X1)          0.07    0.58 r   ← gate delay
  ff2/D  (DFF_X1)          0.00    0.58 r
  data arrival time                0.58

  clock clk (rise edge)   10.00   10.00
  clock network delay      0.10   10.10
  ff2/CK (DFF_X1)          0.00   10.10 r
  library setup time      -0.09   10.01     ← T_setup of ff2
  data required time              10.01

  slack (MET)                       9.43    ← positive = PASS ✅
```

**How to read it:**
- `Incr` = incremental delay at each cell/wire
- `Path` = cumulative arrival time
- `r` = rising transition, `f` = falling transition
- Final `slack` = required − arrival

---

## Common Timing Violations and Fixes

### Setup Violation (slack < 0)

**Cause:** Data path is too slow — too many gates, long wires, or clock period too tight.

**Fixes:**
```
1. Reduce combinational logic depth
   → Pipeline the path (add a register in the middle)
   → Use faster cells (higher drive strength)

2. Reduce wire delay
   → Shorten the routing (physical design fix)
   → Add buffers to drive long nets

3. Adjust constraints
   → Relax clock period (lower frequency)
   → Use set_multicycle_path if data genuinely takes 2 cycles

4. Logic restructuring
   → Replace ripple carry adder with carry-lookahead
   → Recode FSM to reduce next-state logic depth
```

### Hold Violation (slack < 0)

**Cause:** Data arrives too quickly at the capture flop — path has no delay (e.g. direct register-to-register connection with tiny combinational logic).

**Fixes:**
```
1. Add delay buffers on the data path
   → Tool inserts buffer cells automatically during ECO

2. Fix in physical design
   → Route the net with longer wire (adds delay)

3. Check your CDC crossings
   → Hold violations across clock domains are often false paths
   → Use set_false_path for truly async crossings
```

---

## Process, Voltage, Temperature (PVT) Corners

Real chips operate across a range of conditions. STA must be run at multiple **corners**:

| Corner | Process | Voltage | Temperature | Use |
|--------|---------|---------|-------------|-----|
| **SS** (Slow-Slow) | Slow | Low (0.9V) | Hot (125°C) | Setup check (worst case slow) |
| **FF** (Fast-Fast) | Fast | High (1.1V) | Cold (−40°C) | Hold check (worst case fast) |
| **TT** (Typical) | Typical | Nom (1.0V) | 25°C | Characterization |

> **Rule:** Check setup at SS corner. Check hold at FF corner.

In modern signoff, **POCV (Parametric OCV)** or **AOCV** models are used, which apply different derating factors to launch and capture paths instead of single corner analysis.

---

## Clock Domain Crossing (CDC)

When data passes between two flip-flops clocked by **different, unrelated clocks**, STA cannot analyze the path correctly. These are **Clock Domain Crossings (CDCs)**.

```
clk_a (100 MHz) → FF_A → ... → FF_B ← clk_b (83 MHz)
                              ↑
                         CDC crossing!
```

**STA treatment:** Use `set_false_path` or `set_max_delay -datapath_only` for CDC paths. Then verify CDC correctness separately with CDC tools (Questa CDC, SpyGlass CDC) or synchronizer circuits.

---

## Key STA Metrics in Reports

| Metric | Meaning | Target |
|--------|---------|--------|
| **WNS** (Worst Negative Slack) | Worst setup slack across all paths | ≥ 0 |
| **TNS** (Total Negative Slack) | Sum of all negative setup slacks | 0 |
| **WHS** (Worst Hold Slack) | Worst hold slack across all paths | ≥ 0 |
| **THS** (Total Hold Slack) | Sum of all negative hold slacks | 0 |
| **WPWS** (Worst Pulse Width Slack) | Min pulse width violations | ≥ 0 |

A clean sign-off requires **WNS ≥ 0, TNS = 0, WHS ≥ 0, THS = 0**.

---

## Free Tools for STA Practice

| Tool | Use |
|------|-----|
| **OpenSTA** | Free open-source STA engine (same engine used in OpenROAD) |
| **OpenLane / LibreLane** | Full flow including STA reports |
| **Icarus + GTKWave** | Simulate to understand timing intuitively first |

Run OpenSTA standalone:
```bash
# Install
sudo apt install opensta

# Run
opensta my_constraints.tcl
```

Inside the Tcl script:
```tcl
read_liberty  sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog  counter.v
link_design   counter
create_clock  -period 10 [get_ports clk]
report_checks -path_delay max -format full
report_wns
report_tns
```

---

## STA Interview Questions

These come up in nearly every VLSI/RTL interview:

**Q: What is slack? What does negative slack mean?**
> Slack = Required arrival time − Actual arrival time. Negative slack means the data arrives too late — timing is violated.

**Q: What is the difference between setup and hold violations?**
> Setup: data arrives too late (fix by making data path faster or reducing clock frequency). Hold: data changes too soon (fix by adding delay on data path).

**Q: Why do we check hold with fast corners?**
> Hold violations occur when paths are too fast. Fast (FF) corners represent the fastest the silicon can run — worst case for hold.

**Q: What is clock skew and how does it affect timing?**
> Skew = difference in clock arrival time between two flops. Positive skew helps setup but hurts hold. Negative skew hurts setup.

**Q: What is a false path?**
> A timing path that physically exists in the netlist but is never sensitized in real operation. We tell STA to ignore it with `set_false_path`.

---

## Summary

```
STA checks:  Does data arrive on time at every flip-flop?

Setup check: Data must arrive BEFORE clock edge (by T_setup)
             Slack = Required - Arrival ≥ 0

Hold check:  Data must stay stable AFTER clock edge (for T_hold)  
             Slack = Arrival - Required ≥ 0

Tools tell timing via SDC:
  create_clock, set_input_delay, set_output_delay,
  set_false_path, set_multicycle_path

Sign-off requires: WNS ≥ 0, TNS = 0 at SS corner (setup)
                   WHS ≥ 0, THS = 0 at FF corner (hold)
```

---

*Want a condensed STA cheat sheet you can print? The [STA Reference PDF](/shop) in the shop covers all equations, SDC commands, and timing report interpretation on 20 pages.*
