---
layout: post
title: "SDC Timing Constraints — Complete Practical Guide for ASIC Design"
description: "Master Synopsys Design Constraints (SDC): create_clock, set_input_delay, set_output_delay, set_multicycle_path, set_false_path, clock groups — with a complete annotated constraint file for a dual-clock processor."
date: 2026-05-17
category: STA
tags: [sdc, timing-constraints, sta, asic, create_clock, set_input_delay, false_path, multicycle, synopsys, cadence]
---

A timing constraint file (`.sdc`) is how you communicate your design intent to the STA tool. Get it wrong, and either the tool misses real violations or it optimises paths that don't need it — wasting area and power. This guide covers every SDC command you'll use in production, with working examples and a complete constraint file at the end.

---

## What Is SDC?

SDC (Synopsys Design Constraints) is a Tcl-based constraint language used by:
- **Synthesis:** Design Compiler, Genus — guides logic optimisation
- **PnR:** Innovus, ICC2 — guides placement and routing
- **STA:** PrimeTime, Tempus — verifies timing sign-off

The same `.sdc` file flows through all three tools. Write it once, use it everywhere.

---

## 1. `create_clock` — Define Your Clock

The most critical constraint — every timing path check references a clock.

```tcl
# 100 MHz clock (10 ns period) on the clk port
# Rising edge at 0 ns, falling edge at 5 ns
create_clock -name clk -period 10 -waveform {0 5} [get_ports clk]

# 200 MHz second clock
create_clock -name clk_fast -period 5 -waveform {0 2.5} [get_ports clk_fast]

# Virtual clock (for I/O constraints — no physical port)
create_clock -name vclk -period 10

# Add timing uncertainty (models jitter + skew margin)
set_clock_uncertainty -setup 0.2 [get_clocks clk]
set_clock_uncertainty -hold  0.1 [get_clocks clk]

# Add clock transition time (rise/fall slew)
set_clock_transition 0.1 [get_clocks clk]
```

| Parameter | Meaning |
|-----------|---------|
| `-period` | Clock period in ns (10 ns = 100 MHz) |
| `-waveform {r f}` | Rise and fall time within one period |
| `-name` | Logical name used in other constraints |

> **Always define clocks first** — all other constraints reference them.

---

## 2. `create_generated_clock` — PLL Output Clocks

For clocks derived from PLLs or clock dividers:

```tcl
# Divided clock: clk/2 from a divider cell
create_generated_clock \
    -name       clk_div2 \
    -divide_by  2 \
    -source     [get_ports clk] \
    [get_pins   u_clkdiv/Q]

# Multiplied clock: clk × 4 from PLL
create_generated_clock \
    -name       clk_pll \
    -multiply_by 4 \
    -source     [get_ports clk] \
    [get_pins   u_pll/clk_out]

# Phase-shifted clock
create_generated_clock \
    -name       clk_90deg \
    -phase      90 \
    -source     [get_clocks clk] \
    [get_pins   u_pll/clk_90]
```

The tool propagates these through the clock tree automatically once defined.

---

## 3. `set_input_delay` — Model External Setup Time

`set_input_delay` tells the tool: "before reaching my input port, the data has already used this many nanoseconds of the clock period."

```tcl
# -max is for setup check (data arrives late in the period)
# -min is for hold check (data arrives early — could cause hold viol.)
set_input_delay -max 3.0 -clock clk [get_ports data_in]
set_input_delay -min 1.0 -clock clk [get_ports data_in]

# Multiple ports at once
set_input_delay -max 2.5 -clock clk [get_ports {addr[*] wen ren}]

# Rising-edge triggered path explicitly
set_input_delay -max 3.0 -clock clk -clock_fall [get_ports data_ddr]
```

**How to choose the value:** If the upstream chip launches data 3 ns after the clock edge, set `-max 3`. The STA tool then only allocates `Tclk - 3 ns` for your internal logic.

```
External chip: clk_edge → FF → 3ns logic → your_chip_port
                                    ↑ set_input_delay -max 3
Your chip:            port → your_logic → FF
                      Only 10-3 = 7 ns budget for your logic
```

---

## 4. `set_output_delay` — Model External Hold/Setup Needs

The downstream chip needs data to be stable before its clock edge:

```tcl
# Downstream chip needs data 2 ns before its clock edge
set_output_delay -max 2.0 -clock clk [get_ports data_out]
# Downstream chip needs data to be stable for 0.5 ns after edge
set_output_delay -min -0.5 -clock clk [get_ports data_out]

# Apply to all output ports
set_output_delay -max 1.5 -clock clk [all_outputs]
```

`-min` for output delay is usually negative (data can change slightly after the clock edge at the destination).

---

## 5. `set_false_path` — Paths That Don't Need Timing

False paths exist but don't carry time-critical data:

```tcl
# Async reset from external port — not a timed path
set_false_path -from [get_ports rst_n]

# Test mode mux select — static during normal operation
set_false_path -from [get_ports scan_en]

# Paths between two unrelated clock domains (CDC crossings)
# Safer alternative: use set_clock_groups instead
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]
set_false_path -from [get_clocks clk_b] -to [get_clocks clk_a]

# Specific point-to-point false path
set_false_path -from [get_cells u_config/cfg_reg] -to [get_cells u_core/data_reg]
```

> **Caution:** Don't false-path everything to make violations disappear. Only mark paths that genuinely don't need analysis.

---

## 6. `set_multicycle_path` — Paths That Take N Cycles

Some operations (multipliers, dividers) legitimately need more than one clock cycle to complete:

```tcl
# 2-cycle multiplier: setup check uses 2×Tclk instead of 1×Tclk
set_multicycle_path -setup 2 \
    -from [get_cells u_mult/*] \
    -to   [get_cells u_result/*]

# CRITICAL: always adjust hold by (N-1) for a setup MCP
# Default hold check is at cycle N; adjust back to cycle 0
set_multicycle_path -hold 1 \
    -from [get_cells u_mult/*] \
    -to   [get_cells u_result/*]
```

**Why the hold adjustment is mandatory:**

By default, when you set `-setup 2`, the tool pushes the required time to cycle 2 but keeps the hold check at cycle 1. This creates an impossible situation (data must arrive in cycle 2 for setup but stay stable through cycle 1 for hold). Setting `-hold 1` shifts the hold check back to cycle 0, which is what you actually want.

```
Without hold fix:
  Cycle 0 (launch) → Cycle 2 (required for setup) ← correct
  Cycle 0 (launch) → Cycle 1 (required for hold)  ← WRONG, too tight

With hold fix (-hold 1):
  Cycle 0 (launch) → Cycle 2 (required for setup) ← correct
  Cycle 0 (launch) → Cycle 0 (required for hold)  ← correct
```

---

## 7. `set_clock_groups` — Declare Asynchronous Clock Relationships

More precise than `set_false_path` — bidirectional, and correctly handles the entire crossing:

```tcl
# Two completely unrelated clocks — no timing between them
set_clock_groups -asynchronous \
    -group [get_clocks clk_a] \
    -group [get_clocks clk_b]

# Three clock groups — all asynchronous to each other
set_clock_groups -asynchronous \
    -group {clk_core} \
    -group {clk_peri} \
    -group {clk_ddr}

# Exclusive: only one clock active at a time (clock mux)
set_clock_groups -exclusive \
    -group [get_clocks clk_slow] \
    -group [get_clocks clk_fast]
```

| | `set_false_path` | `set_clock_groups -async` |
|--|-----------------|--------------------------|
| Bidirectional? | No (must specify both directions) | Yes |
| Applies to all paths? | No (specific from/to) | Yes (all paths between groups) |
| Use for | Specific paths | Entire clock groups |

---

## 8. `set_driving_cell` and `set_load`

Model the external drive strength and capacitive load on ports:

```tcl
# External driver: BUF_X4 cell drives all inputs
set_driving_cell -lib_cell BUF_X4 -pin Y [all_inputs]

# Specific slower driver on slow control ports
set_driving_cell -lib_cell INV_X1 -pin ZN [get_ports {wen ren}]

# External capacitive load on outputs (pF)
set_load 0.05 [all_outputs]      # 50 fF = light PCB trace
set_load 0.5  [get_ports data_out]  # 500 fF = heavy load
```

---

## 9. Design Rule Constraints

```tcl
# Maximum fanout — tool inserts buffers if exceeded
set_max_fanout 32 [current_design]

# Maximum transition time (slew) — prevents slow edges
set_max_transition 0.5 [current_design]   # 500 ps max slew

# Maximum net capacitance
set_max_capacitance 0.2 [current_design]  # 200 fF max
```

---

## 10. Useful `get_*` Query Commands

```tcl
get_ports clk                     # port named clk
get_ports data_*                  # all ports starting with data_
get_ports [all_inputs]            # all input ports
get_ports [all_outputs]           # all output ports

get_cells u_alu                   # cell named u_alu
get_cells u_core/*                # all cells under u_core hierarchy
get_cells -hier *reg*             # all cells with 'reg' in name (hierarchical)

get_pins u_alu/A                  # pin A of cell u_alu
get_clocks clk                    # clock named clk
get_nets data_bus                 # net named data_bus
```

---

## Complete Annotated SDC File

```tcl
##############################################################
# processor.sdc — Complete constraint file for a dual-clock
# RISC-V processor with DDR memory interface
##############################################################

##-- Clocks --------------------------------------------------

# Core clock: 500 MHz
create_clock -name clk_core -period 2.0 -waveform {0 1.0} \
    [get_ports clk_core]
set_clock_uncertainty -setup 0.05 [get_clocks clk_core]
set_clock_uncertainty -hold  0.03 [get_clocks clk_core]
set_clock_transition    0.05      [get_clocks clk_core]

# Peripheral clock: 100 MHz (from PLL)
create_generated_clock -name clk_peri -divide_by 5 \
    -source [get_ports clk_core] \
    [get_pins u_pll/peri_out]
set_clock_uncertainty -setup 0.1 [get_clocks clk_peri]

# DDR clock: 200 MHz
create_clock -name clk_ddr -period 5.0 \
    [get_ports clk_ddr]

##-- Clock domain relationships ------------------------------

# Core and DDR are asynchronous — proper CDCs instantiated in RTL
set_clock_groups -asynchronous \
    -group {clk_core} \
    -group {clk_ddr}

# Peripheral is synchronous to core (derived by PLL, known phase)
# No set_clock_groups between clk_core and clk_peri

##-- Resets (false paths) ------------------------------------

set_false_path -from [get_ports rst_n]
set_false_path -from [get_ports peri_rst_n]

##-- Test/scan (false paths) ---------------------------------

set_false_path -from [get_ports scan_en]
set_false_path -from [get_ports test_mode]

##-- Input delays (clk_core domain) -------------------------

# Data from external SRAM (3 ns registered output delay)
set_input_delay -max 1.0 -clock clk_core \
    [get_ports {instr_data[*] mem_data[*]}]
set_input_delay -min 0.2 -clock clk_core \
    [get_ports {instr_data[*] mem_data[*]}]

# Control inputs (slower paths)
set_input_delay -max 0.8 -clock clk_core \
    [get_ports {irq[*] debug_req}]

##-- Output delays (clk_core domain) ------------------------

set_output_delay -max 0.5 -clock clk_core \
    [get_ports {mem_addr[*] mem_we mem_re}]
set_output_delay -min -0.1 -clock clk_core \
    [get_ports {mem_addr[*] mem_we mem_re}]

##-- Multicycle paths ----------------------------------------

# 4×4 multiplier takes 2 core cycles
set_multicycle_path -setup 2 \
    -from [get_cells u_mul/*] \
    -to   [get_cells u_mul/result_reg/*]
set_multicycle_path -hold 1 \
    -from [get_cells u_mul/*] \
    -to   [get_cells u_mul/result_reg/*]

# Division unit takes 4 cycles
set_multicycle_path -setup 4 \
    -from [get_cells u_div/*] \
    -to   [get_cells u_div/quot_reg/*]
set_multicycle_path -hold 3 \
    -from [get_cells u_div/*] \
    -to   [get_cells u_div/quot_reg/*]

##-- Design rules -------------------------------------------

set_max_fanout    20 [current_design]
set_max_transition 0.15 [current_design]
set_driving_cell -lib_cell BUF_X4 -pin Y [all_inputs]
set_load 0.05 [all_outputs]

##-- End of constraints --------------------------------------
```

---

## Common Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Missing `-hold N-1` on multicycle path | Hold violation on MCP | Always pair `-setup N` with `-hold N-1` |
| `set_false_path` to hide violations | Real violations masked | Only false-path genuinely non-functional paths |
| Wrong `set_input_delay` value | Tool optimises wrong budget | Match to datasheet of upstream chip |
| No `set_clock_groups` for async clocks | STA analyses impossible paths | Add `set_clock_groups -asynchronous` |
| Forgetting clock uncertainty | Overly optimistic slack | Add `set_clock_uncertainty` for jitter/skew |
| `create_clock` on wrong point | Wrong propagation | Clock should be on the port or clock cell output |
| Ignoring `set_load` | Output paths under-constrained | Always set load on outputs |

---

## What's Next

- **[Setup & Hold Time — STA]({{ '/blog/2026/05/17/setup-hold-time-sta/' | relative_url }})** — understand what the STA tool is actually computing
- **[Clock Domain Crossing]({{ '/blog/2026/05/17/clock-domain-crossing/' | relative_url }})** — implement the `set_clock_groups` and `set_false_path` CDC patterns in RTL
- **[RTL Synthesis with Design Compiler]({{ '/blog/2026/05/17/synopsys-design-compiler/' | relative_url }})** — feed this SDC file into synthesis and interpret the report
