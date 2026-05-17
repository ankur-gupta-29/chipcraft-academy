---
layout: post
title: "Setup Time, Hold Time & Slack — Static Timing Analysis for Beginners"
description: "Understand setup time, hold time, slack, and timing violations in digital design. Learn how STA tools check every path, what causes violations, and exactly how to fix them — with diagrams."
date: 2026-05-17
category: STA
tags: [sta, timing, setup-time, hold-time, slack, timing-violation, critical-path, beginner, asic]
image: /assets/images/setup-hold-timing.svg
---

Every digital design has a maximum clock frequency. Push past it and flip-flops sample wrong values, causing silent data corruption. Static Timing Analysis (STA) is the tool that finds that limit — and tells you exactly which path is causing the problem. This guide explains setup time, hold time, and slack clearly, with no hand-waving.

---

## What Is Static Timing Analysis?

STA checks timing on **every single path** in your design, mathematically, without running a simulation. It's the gating check before physical sign-off.

| | Simulation | STA |
|--|-----------|-----|
| Method | Run vectors through design | Mathematical path analysis |
| Speed | Hours for large designs | Minutes |
| Coverage | Only tested vectors | All paths simultaneously |
| Corner analysis | Hard | Built-in (worst/best case) |
| When used | Functional verification | Timing sign-off |

Tools: Synopsys PrimeTime, Cadence Tempus, open-source OpenSTA.

---

## The Flip-Flop Model

Every timing path starts at a **launch flip-flop** and ends at a **capture flip-flop**, with combinational logic in between:

```
clk ───┬─────────────────────────────────────┬───
       │                                     │
       ▼                                     ▼
  ┌─────────┐    Tlogic                ┌─────────┐
  │ Launch  │ ──────────────────────── │ Capture │
  │   FF    │  combinational logic     │   FF    │
  └─────────┘                         └─────────┘
      Tcq                                  Tsu, Th
  (clk→Q delay)                      (setup, hold)
```

The launch FF sends data, the combinational logic processes it, and the capture FF must receive stable data before its next clock edge.

<img src="{{ '/assets/images/setup-hold-timing.svg' | relative_url }}" alt="Setup and hold time timing diagram" style="width:100%;max-width:720px;display:block;margin:1.5rem auto;">

---

## Setup Time (Tsu) — Data Must Arrive Early Enough

**Definition:** Data must be stable for at least `Tsu` nanoseconds *before* the capturing clock edge.

**Why:** The flip-flop needs time to sense the input and lock it internally before the clock edge arrives. If data is still changing when the clock fires, the FF can't decide which value to latch.

**Setup timing equation:**
```
Tcq(launch) + Tlogic ≤ Tclk − Tsu(capture) + Tskew
```

Where:
- `Tcq` = clock-to-Q propagation delay of launch FF (typically 0.1–0.3 ns in 28nm)
- `Tlogic` = total combinational delay on the path (can be many ns for long chains)
- `Tclk` = clock period (e.g. 10 ns for 100 MHz)
- `Tsu` = setup time requirement of capture FF (typically 0.05–0.1 ns)
- `Tskew` = clock skew (capture clock arrives earlier than launch clock: positive skew helps setup)

**Setup slack (positive = timing met):**
```
Setup slack = Tclk − Tsu − Tcq − Tlogic + Tskew
```

A **setup violation** means `Tlogic` is too large — data arrives too late.

---

## Hold Time (Th) — Data Must Stay Stable After the Edge

**Definition:** Data must remain stable for at least `Th` nanoseconds *after* the capturing clock edge.

**Why:** The flip-flop is still latching the value during this window. If new data arrives too soon after the clock edge (from the *next* launch FF output), it corrupts the captured value.

**Hold timing equation:**
```
Tcq(launch) + Tlogic ≥ Th(capture) + Tskew
```

**Hold slack:**
```
Hold slack = Tcq + Tlogic − Th − Tskew
```

A **hold violation** means data changes too quickly — it arrives while the FF is still capturing the previous value. Hold violations can occur even at low frequencies, since they don't depend on clock period.

---

## Slack — Your Timing Margin

Slack is the timing margin. Positive = good; negative = violation.

<img src="{{ '/assets/images/sta-slack-diagram.svg' | relative_url }}" alt="STA timing path and slack calculation" style="width:100%;max-width:720px;display:block;margin:1.5rem auto;">

```
Setup slack  > 0 → timing met ✓
Setup slack  < 0 → setup VIOLATION ✗ → reduce logic depth or slow clock

Hold slack   > 0 → timing met ✓
Hold slack   < 0 → hold VIOLATION ✗ → add buffer delay on that path
```

The **critical path** is the path with the smallest (least) positive slack — or the most negative slack if violated.

---

## Timing Path Types

| Path type | Start | End | Example |
|-----------|-------|-----|---------|
| **FF-to-FF** | Launch FF Q | Capture FF D | ALU result → result register |
| **Input-to-FF** | Input port | FF D | `data_in` → shift register |
| **FF-to-Output** | FF Q | Output port | Status reg → `valid_out` |
| **Input-to-Output** | Input port | Output port | Combinational pass-through |

STA checks all four types. Input/output paths need `set_input_delay` and `set_output_delay` in SDC to model the external logic.

---

## Reading an STA Report

Here is a typical PrimeTime timing report (annotated):

```
Path Group: clk
Path Type:  max (setup check)
Point                                    Incr       Path
─────────────────────────────────────────────────────────
clock clk (rise edge)                    0.00       0.00
clock network delay (propagated)         0.12       0.12  ← Tskew / clock insertion

u_alu/reg_a_reg/CK (DFFX1)              0.00       0.12  ← Launch FF clock pin
u_alu/reg_a_reg/Q  (DFFX1)              0.18       0.30  ← Tcq = 0.18 ns

u_alu/u_add/A[0]   (ADDF_X1)           0.04       0.34  ← Logic delay starts
u_alu/u_add/CO     (ADDF_X1)           0.31       0.65
u_alu/u_carry/A    (AOI21_X1)          0.08       0.73
...
u_result/D         (DFFX1)             0.00       4.82  ← Data arrives at capture FF

data arrival time                                  4.82  ← Tcq + Tlogic

clock clk (rise edge)                   10.00     10.00  ← Next clock edge
clock network delay (propagated)         0.09     10.09
u_result/CK  (DFFX1)                   0.00     10.09
library setup time                      -0.07     10.02  ← Tsu = 0.07 ns

data required time                                10.02  ← Tclk − Tsu + Tskew

─────────────────────────────────────────────────────────
data required time                                10.02
data arrival time                                 -4.82
─────────────────────────────────────────────────────────
slack (MET)                                        5.20  ← 5.2 ns of margin ✓
```

Key fields to look at:
- **Startpoint**: the launch FF
- **Endpoint**: the capture FF D pin
- **Slack (MET)**: positive → timing met. **VIOLATED** with a negative number means you have a problem.
- Each row's "Incr" column is the incremental delay through each cell

---

## Causes and Fixes — Setup Violations

| Cause | Fix |
|-------|-----|
| Long combinational chain (adder, multiplier) | Insert pipeline register to split the path |
| Slow (high-drive) standard cells | Replace with faster (larger drive) cells |
| High fanout net (1 driver → 1000 loads) | Add buffers to split the fanout; use CTS |
| Long routing wire | Move cells closer (PnR re-floorplanning) |
| Too-tight clock period | Lower frequency, or accept lower performance |
| Missing false path | Mark paths that don't need timing analysis |

**Most impactful fix: pipeline insertion**

```verilog
// BEFORE: 40 ns path — violates 10 ns clock
always @(posedge clk)
    result <= a * b * c + d;    // 40 ns of multiply+add

// AFTER: split into 2 pipeline stages — each 20 ns, meets 25 ns clock
always @(posedge clk)
    pipe1 <= a * b;             // Stage 1: multiply (20 ns)

always @(posedge clk)
    result <= pipe1 * c + d;   // Stage 2: multiply+add (20 ns)
```

---

## Causes and Fixes — Hold Violations

Hold violations are independent of frequency — they happen when data changes too fast.

| Cause | Fix |
|-------|-----|
| Zero-delay combinational path | Add buffer cells to create minimum delay |
| Large positive clock skew | Fix clock tree; reduce skew |
| Very fast standard cell (low Tcq) | Replace with slightly slower cell |
| Multicycle path constraint missing | Add `set_multicycle_path -hold` |

**Fix: add delay buffers**

```tcl
# In PrimeTime/Innovus: tool automatically inserts hold buffers
# Or in RTL, explicitly delay:
# (usually done by the tool, not manually in RTL)
```

---

## SDC Clock Definition

The STA tool doesn't know your clock frequency unless you tell it:

```tcl
# 100 MHz clock (10 ns period) on port clk, rising edge at 0 ns
create_clock -name clk -period 10 -waveform {0 5} [get_ports clk]

# Add clock uncertainty (jitter + skew margin) — tightens analysis
set_clock_uncertainty -setup 0.2 [get_clocks clk]
set_clock_uncertainty -hold  0.1 [get_clocks clk]
```

---

## Common Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| No `create_clock` in SDC | STA tool has no timing reference | Always define clocks first |
| Fixing setup by slowing clock | Hides the problem | Fix the path, not the clock |
| Ignoring hold violations | Silent data corruption at high temp/voltage corners | Fix hold first (buffers) |
| Positive slack everywhere | Design may be over-constrained | Check constraints, not just violations |
| Forgetting clock uncertainty | Optimistic slack — fails silicon | Add `set_clock_uncertainty` |
| Single corner only | Misses slow/fast PVT corner violations | Always run min/max corners |

---

## What's Next

- **[Clock Domain Crossing (CDC)]({% post_url 2026-05-17-clock-domain-crossing %})** — when two clocks interact, STA can't check across — you need CDC analysis
- **[SDC Timing Constraints]({% post_url 2026-05-17-sdc-timing-constraints %})** — write complete constraint files that correctly model your design
- **[Pipelining RTL Design]({% post_url 2026-05-17-pipeline-rtl-design %})** — the primary technique for fixing setup violations
