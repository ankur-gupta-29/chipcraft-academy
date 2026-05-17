---
layout: post
title: "RTL Synthesis with Synopsys Design Compiler — Beginner Walkthrough"
description: "Step-by-step guide to RTL synthesis with Synopsys Design Compiler: read_verilog, elaborate, compile_ultra, timing reports, area reports, common errors — with a complete dc_shell script."
date: 2026-05-17
category: ASIC Flow
tags: [synthesis, design-compiler, synopsys, asic, rtl, netlist, timing, beginner]
image: /assets/images/dc-synthesis-flow.svg
---

Synthesis converts your RTL (Verilog/SystemVerilog) into a gate-level netlist using a technology library. Synopsys Design Compiler (DC) is the industry standard. This guide walks through a complete synthesis run — from RTL to signed-off netlist — with annotated commands and output.

---

## What Synthesis Does

```
RTL (.v/.sv)          Technology Library (.db)
       │                        │
       └──────────┬─────────────┘
                  ▼
          Design Compiler
                  ▼
     Gate Netlist (.v)  +  Timing Report  +  Area Report
```

DC maps your behavioural RTL to real transistor-level gates from the foundry's standard cell library, optimising for timing, area, and power under the constraints you provide.

<img src="{{ '/assets/images/dc-synthesis-flow.svg' | relative_url }}" alt="Design Compiler synthesis flow" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

---

## Prerequisites

```bash
# Start Design Compiler interactive shell
dc_shell

# Or batch mode (recommended for scripts)
dc_shell -f synth.tcl | tee synth.log
```

You need:
- `RTL source files` (.v, .sv)
- `Technology library` (.db format — from foundry/IP vendor)
- `SDC constraints file` (.sdc)

---

## Step 1 — Set Up Libraries

```tcl
# Tell DC which technology libraries to use
set target_library "slow.db fast.db"   # timing corners
set link_library   "* slow.db fast.db" # * = keep already-linked

# Set search path for RTL and constraints
set search_path [list . ./rtl ./constraints ./libs]
```

| Library type | Purpose |
|-------------|---------|
| `target_library` | Standard cell timing/area library for mapping |
| `link_library` | All libs to link against (include `*` for current design) |
| `symbol_library` | Schematic symbols (optional, for GUI) |

---

## Step 2 — Read and Elaborate RTL

```tcl
# Read Verilog/SystemVerilog files
read_verilog [list \
    rtl/alu.v \
    rtl/regfile.v \
    rtl/control_unit.v \
    rtl/riscv_core.v \
]

# Or use analyze+elaborate for better dependency handling
analyze -library work -format sverilog [glob rtl/*.sv]
elaborate riscv_core

# Set the top-level design
current_design riscv_core

# Check for any RTL issues
check_design
```

`check_design` output to watch for:
```
Warning: Cannot find cell 'u_pll' in library...     ← missing library cell
Warning: Unresolved reference 'imem'                 ← missing module
Error: Multi-driver on net 'data_bus'                ← RTL error
```

---

## Step 3 — Apply Constraints

```tcl
# Apply SDC constraints
source constraints/riscv.sdc

# Or apply manually:
create_clock -name clk -period 10 [get_ports clk]
set_input_delay  -max 3 -clock clk [all_inputs]
set_output_delay -max 2 -clock clk [all_outputs]
set_false_path -from [get_ports rst_n]
```

---

## Step 4 — Compile

```tcl
# Standard compile — good for most designs
compile

# High-effort compile — best QoR, slower runtime (~3–5x longer)
compile_ultra

# compile_ultra options:
compile_ultra -no_autoungroup          # preserve hierarchy for debugging
compile_ultra -timing_high_effort_script  # extra timing effort
compile_ultra -area_high_effort_script    # optimise for area
compile_ultra -gate_clock               # enable automatic clock gating
```

During compile you'll see:
```
Compiling...
Phase 1: Constraint Driven Mapping
    Number of cells = 12450
    Timing violations: 3
Phase 2: Incremental Compilation
    ...
Phase 3: Timing Driven Optimisation
    All timing constraints met
```

---

## Step 5 — Read Timing Reports

```tcl
# Overall timing summary
report_timing_summary

# Worst path (most critical — most negative slack)
report_timing -max_paths 1

# Top-10 worst paths
report_timing -max_paths 10

# Specific path from FF to FF
report_timing \
    -from [get_cells u_alu/a_reg/*] \
    -to   [get_cells u_alu/result_reg/*]
```

**Annotated timing report:**
```
Path Type: max (Library Setup Time)
Startpoint: u_alu/a_reg/Q
Endpoint:   u_alu/result_reg/D
Path Group: clk

  Point                           Incr    Path
  ─────────────────────────────────────────────
  clock clk (rise)                0.00    0.00
  u_alu/a_reg/CK (DFFX2)         0.00    0.00
  u_alu/a_reg/Q  (DFFX2)         0.13    0.13  ← Tcq
  u_alu/u_add/A  (ADD32)         0.02    0.15
  u_alu/u_add/S  (ADD32)         2.84    2.99  ← Long adder delay
  u_alu/result_reg/D (DFFX2)     0.00    2.99  ← Arrival

  clock clk (rise)               10.00   10.00
  library setup time             -0.07    9.93  ← Tsu
  data required time                      9.93

  data required time              9.93
  data arrival time              -2.99
  ─────────────────────────────────────────────
  slack (MET)                     6.94   ← 6.94 ns margin ✓
```

---

## Step 6 — Read Area Reports

```tcl
# Total area
report_area

# Hierarchical area breakdown
report_area -hierarchy

# Cell count
report_cell
```

**Example area report:**
```
Design: riscv_core

Combinational area:   45823.25 (sq microns)
Noncombinational area: 18204.00 (flip-flop area)
Net Interconnect area: 12450.00 (estimated)
─────────────────────────────────────────────
Total cell area:       76477.25

Hierarchical area:
  u_alu          12340.50    16.1%
  u_regfile      18200.00    23.8%
  u_ctrl          4320.25     5.6%
  u_dmem         22010.00    28.8%
  (other)        19606.50    25.6%
```

---

## Step 7 — Read Power Reports

```tcl
# Estimate power (requires .saif activity file for accuracy)
report_power

# With switching activity from simulation
read_saif -input simulation.saif -instance u_core
report_power
```

**Example power report:**
```
                    Internal  Switching  Leakage   Total
                    Power     Power      Power     Power
  ──────────────────────────────────────────────────────
  u_alu              0.456     0.234      0.012    0.702 mW
  u_regfile          0.312     0.145      0.008    0.465 mW
  u_ctrl             0.089     0.042      0.003    0.134 mW
  ──────────────────────────────────────────────────────
  Total              1.423     0.732      0.031    2.186 mW
```

---

## Step 8 — Write Outputs

```tcl
# Gate-level netlist (Verilog)
write -format verilog -hierarchy -output outputs/riscv_netlist.v

# Standard Delay Format (for simulation with back-annotated timing)
write_sdf -version 3.0 outputs/riscv.sdf

# Design Constraints (propagated constraints for PnR)
write_sdc outputs/riscv_mapped.sdc

# DC internal format (for incremental runs)
write -format ddc outputs/riscv.ddc
```

---

## Complete dc_shell Script

```tcl
#!/usr/bin/env dc_shell -f
# synth.tcl — complete synthesis script

##── Setup ──────────────────────────────────────────────────
set DESIGN     riscv_core
set RTL_DIR    ./rtl
set OUT_DIR    ./outputs
set CONS_FILE  ./constraints/riscv.sdc

file mkdir $OUT_DIR

##── Libraries ──────────────────────────────────────────────
set target_library "slow_tt_25c_1v0.db"
set link_library   "* slow_tt_25c_1v0.db"
set search_path    [list . $RTL_DIR ./libs]

##── Read RTL ────────────────────────────────────────────────
analyze -library work -format sverilog [glob $RTL_DIR/*.sv]
elaborate $DESIGN

current_design $DESIGN
check_design

##── Constraints ─────────────────────────────────────────────
source $CONS_FILE

##── Compile ─────────────────────────────────────────────────
compile_ultra -gate_clock

##── Reports ─────────────────────────────────────────────────
report_timing_summary > $OUT_DIR/timing_summary.txt
report_timing -max_paths 20 > $OUT_DIR/timing_paths.txt
report_area -hierarchy   > $OUT_DIR/area.txt
report_power             > $OUT_DIR/power.txt
report_qor               > $OUT_DIR/qor.txt

##── Write outputs ───────────────────────────────────────────
write -format verilog -hierarchy -output $OUT_DIR/${DESIGN}_netlist.v
write_sdc $OUT_DIR/${DESIGN}_mapped.sdc
write_sdf -version 3.0 $OUT_DIR/${DESIGN}.sdf
write -format ddc $OUT_DIR/${DESIGN}.ddc

echo "Synthesis complete. Check $OUT_DIR/"
exit
```

---

## Common Errors and Fixes

| Error / Warning | Cause | Fix |
|-----------------|-------|-----|
| `Cannot resolve reference 'foo'` | Module not read or not in library | Add the file to `read_verilog` or `link_library` |
| `Undriven net 'data_bus'` | Signal has no driver | Check RTL for missing assignments |
| `Multi-driver on net 'x'` | Two always blocks drive same signal | Fix RTL — use one driver per signal |
| `Cannot meet timing — slack -2.5` | Critical path too long | Add pipeline register, or use faster cells |
| `High fanout net 'clk_en'` | 1 signal drives too many cells | Add `set_max_fanout`, DC inserts buffers |
| `Latch inferred from always block` | Missing default assignment | Add default before `case` in always_comb |
| `Library not found` | `.db` file not in search_path | Add directory to `set_search_path` |

---

## What's Next

- **[SDC Timing Constraints]({{ '/blog/2026/05/17/sdc-timing-constraints/' | relative_url }})** — write the `.sdc` file that this synthesis script sources
- **[VLSI Floorplanning]({{ '/blog/2026/05/17/vlsi-floorplanning/' | relative_url }})** — take the gate netlist into physical design
- **[Setup & Hold Time — STA]({{ '/blog/2026/05/17/setup-hold-time-sta/' | relative_url }})** — understand the timing reports DC generates
