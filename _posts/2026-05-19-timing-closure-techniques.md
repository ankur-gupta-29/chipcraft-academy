---
layout: post
title: "Timing Closure Techniques — Fixing Setup and Hold Violations"
description: "Learn how to fix timing violations after place-and-route: setup violation fixes (cell upsizing, LVT swap, retiming, pipelining), hold fixes (buffer insertion, useful skew), ECO flow, and PrimeTime commands."
date: 2026-05-19
category: ASIC Flow
tags: [timing-closure, sta, setup, hold, eco, primetime, asic, pnr, advanced, synthesis]
image: timing-closure-flow.svg
---

Timing closure is what chip designers spend most of their post-layout time doing. The design may have passed timing at synthesis, but after place-and-route — with real wire lengths, actual cell delays, and coupling capacitance — violations reappear. This guide covers the systematic approach to fixing them.

---

## Before You Start: Understand Your Violations

Run PrimeTime and classify your violations first:

```tcl
# Full STA run with annotated parasitics
read_design  -format verilog  netlist.v
read_parasitics  -format spef  design.spef
read_sdc  design.sdc
update_timing
check_timing

# Summarise all violations
report_timing_summary
report_constraint -all_violators

# Worst 20 setup paths
report_timing -max_paths 20 -delay_type max \
    -sort_by slack > setup_violations.rpt

# Worst 20 hold paths
report_timing -max_paths 20 -delay_type min \
    -sort_by slack > hold_violations.rpt
```

**Triage by slack magnitude:**

| Slack | Action |
|-------|--------|
| -0 to -50 ps | ECO fix (targeted cell change) |
| -50 to -200 ps | Multiple ECO fixes or re-optimise |
| -200 ps to -500 ps | Structural change — add pipeline stage |
| < -500 ps | Architectural problem — revisit RTL or constraints |

<img src="{{ '/assets/images/timing-closure-flow.svg' | relative_url }}" alt="Timing closure flow diagram" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

---

## Reading a Timing Report for Root Cause

```
Path Type: max (Setup)
Startpoint: u_cpu/u_alu/a_reg (rising edge-triggered FF, clk)
Endpoint:   u_cpu/u_alu/result_reg (rising edge-triggered FF, clk)

  Cell                          Delay   Arrival
  ─────────────────────────────────────────────
  u_alu/a_reg/CK→Q (DFFRX1)    0.18     0.18   ← Tcq: small FF, slow
  u_add/A  (ADDFHX1)           0.04     0.22
  u_add/CO (ADDFHX1)           0.62     0.84   ← Long adder carry chain
  u_add/CO (ADDFHX1)           0.61     1.45
  u_mux/Y  (MX2X1)             0.21     1.66
  Wire (net: sum_out)           0.38     2.04   ← Long wire — 380 ps!
  u_result_reg/D (DFFRX2)      0.00     2.04

  Required time                          1.95   (2.0 ns period - 0.05 Tsu)
  ─────────────────────────────────────────────
  Slack: -0.09 ns  ← 90 ps violation
```

**Root causes identified:**
1. `DFFRX1` — small, slow flip-flop (low drive strength, high Tcq)
2. Carry ripple through `ADDFHX1` cells — long logic chain
3. 380 ps wire delay — physical placement issue

---

## Fixing Setup Violations

### Fix 1 — Cell Upsizing (Most Common ECO)

Replace a cell with a higher drive-strength variant to reduce its output transition time, which speeds up downstream cells:

```tcl
# PrimeTime ECO: upsize the slow FF
size_cell u_alu/a_reg DFFRX2   ;# X1 → X2 (double drive strength)
size_cell u_alu/a_reg DFFRX4   ;# or go to X4 if needed

# Verify improvement
report_timing -through u_alu/a_reg/Q -max_paths 3
```

**Trade-off:** Larger cells have higher input capacitance — check that the driver of CK can meet max-capacitance DRV after upsizing.

### Fix 2 — Vt Swap: HVT → LVT

High-Vt cells are slower but leak less. Swap to Low-Vt on the critical path:

```tcl
# Check current cell library name
get_attribute [get_cells u_add/u_carry_4] ref_name
# → ADDFHX1_HVT

# Swap to LVT variant (same function, lower threshold)
size_cell u_add/u_carry_4  ADDFHX1_LVT
size_cell u_add/u_carry_5  ADDFHX1_LVT
size_cell u_add/u_carry_6  ADDFHX1_LVT

report_timing -max_paths 5
```

**Trade-off:** LVT cells have higher leakage current. Only swap cells that are actually on the critical path — use `get_timing_paths` to identify them precisely.

### Fix 3 — Logic Restructuring

Reduce the number of logic levels on the critical path. For the adder carry chain, use a faster adder architecture:

```verilog
// ❌ Ripple carry adder — O(N) delay
assign {cout, sum} = a + b + cin;

// ✅ Carry-lookahead — O(log N) delay
// (or let the synthesis tool choose with compile_ultra -retime)
```

```tcl
# In Design Compiler: restructure the adder
set_dont_touch [get_cells u_add] false
compile_ultra -incremental -timing_high_effort_script
```

### Fix 4 — Pipeline Register Insertion

When a path is too long to fix with cell changes alone, break it with a pipeline register:

```verilog
// Before: single-cycle path, violating
always @(posedge clk)
    result <= complex_function(a, b, c, d);  // 8 logic levels, timing fails

// After: two-stage pipeline, half the logic depth per stage
always @(posedge clk) begin
    mid   <= partial_result(a, b);       // 4 logic levels — stage 1
end
always @(posedge clk) begin
    result <= combine(mid, c, d);        // 4 logic levels — stage 2
end
```

**Latency impact:** Adding a pipeline stage increases output latency by 1 cycle. Update any dependent timing paths and protocol handshakes.

### Fix 5 — Physical Optimisation (Relocation)

When wire delay dominates (> 20% of path delay), move cells closer:

```tcl
# Innovus: move cell closer to driver
moveInst -inst u_result_reg \
         -loc  {245.3 187.6}   ;# coordinates from timing report

# Re-route affected nets
routeDesign -selectedNets {sum_out}

# Re-run STA with new parasitics
extractRC
write_parasitics -format spef -output post_eco.spef
# Re-run PrimeTime with post_eco.spef
```

---

## Fixing Hold Violations

Hold violations mean data arrives **too early** at the capture FF — before the previous cycle's data has been safely latched. **Never fix hold by slowing the clock** — always add delay on the data path.

### Fix 1 — Buffer Insertion (Standard Hold Fix)

```tcl
# Insert delay buffer on the violating path
# hold violation: slack = -0.08 ns → need to add ≥ 80 ps of delay

insert_buffer -net sum_short_path \
              -buffer_list {BUFX2 BUFX4} \
              -min_delay 0.1            ;# target 100 ps delay

report_timing -delay_type min -through sum_short_path
```

**Important:** Fixing hold with buffers slightly increases dynamic power (extra switching). This is unavoidable — every hold fix buffer switches with the data.

### Fix 2 — Cell Downsizing

Smaller cells have higher input capacitance → slower transitions → more delay. Downsize cells on the violating path:

```tcl
# Downsize to add delay on the short path
size_cell u_alu/pass_gate  BUFX1     ;# X4 → X1 (slower, smaller)

report_timing -delay_type min -max_paths 5
```

### Fix 3 — Useful Skew for Hold

Delay the **capture** clock (so data is allowed to arrive earlier relative to the capture edge):

```tcl
# Innovus: apply useful skew to fix hold
set_ccopt_mode -hold_fix_by_skew true
ccopt_design -hold_effort high

# Check results
report_clock_tree -skew
report_timing -delay_type min -max_paths 10
```

**Warning:** Useful skew that helps hold on one path hurts setup on that same path. The tool must maintain setup margin simultaneously.

---

## The ECO Flow — Fixing Without Full Recompile

An ECO (Engineering Change Order) makes targeted netlist changes post-route without re-running full synthesis and place-and-route. Critical for late-stage timing closure.

```
Full P&R run (weeks)
        ↓
Sign-off STA reveals 3 setup violations
        ↓
ECO: make minimal changes in PrimeTime
        ↓
Push ECO changes into Innovus
        ↓
Re-route only changed nets (minutes)
        ↓
Re-run STA → verify fixed
```

```tcl
# ── PrimeTime ECO Script ─────────────────────────────────────────
# 1. Run STA and identify violations
update_timing
report_timing -max_paths 10 > pre_eco_timing.rpt

# 2. Make targeted fixes
size_cell  u_core/u_alu/adder/FA_3  ADDFHX2   ;# upsize
size_cell  u_core/u_alu/adder/FA_4  ADDFHX2_LVT ;# LVT swap
insert_buffer -net critical_wire -buffer_list BUFX4

# 3. Write ECO netlist changes
write_changes -format innovus \
              -output eco_fixes.tcl

# 4. Write new full netlist
write_verilog  post_eco_netlist.v

# ── In Innovus: apply ECO ─────────────────────────────────────────
ecoChangeCell  -file eco_fixes.tcl   ;# resize cells
ecoRoute                              ;# re-route only changed nets
extractRC -effortLevel medium
```

---

## Checking for New Violations After ECO

**Critical rule:** Every setup fix risks creating a hold violation, and every hold fix risks creating a setup violation. Always run both checks after each ECO:

```tcl
# After ECO, check both setup AND hold
report_timing -delay_type max -max_paths 20   ;# setup
report_timing -delay_type min -max_paths 20   ;# hold

# Check for new DRV violations from upsized cells
report_constraint -max_capacitance -all_violators
report_constraint -max_transition   -all_violators
report_constraint -max_fanout       -all_violators
```

---

## Timing Closure Checklist

Before sign-off:

- [ ] Zero setup violations at worst-case PVT corner (SS, 125°C, low VDD)
- [ ] Zero hold violations at best-case PVT corner (FF, -40°C, high VDD)
- [ ] Zero max-capacitance DRV violations
- [ ] Zero max-transition DRV violations
- [ ] LVT cell usage < 30% of total cells (leakage budget)
- [ ] Post-ECO extraction and STA re-run completed
- [ ] Functional simulation re-run on post-ECO netlist

---

## Common Timing Closure Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Fixing setup by inserting buffers | Makes hold violations worse | Use upsizing or Vt swap for setup |
| Fixing hold by removing buffers | Makes setup violations worse | Only insert buffers for hold |
| Running STA with ideal clocks post-CTS | Skew not modelled | Switch to `set_propagated_clock` |
| Ignoring DRV violations after upsizing | Downstream cells may be over-driven | Check max-cap after every ECO |
| Re-running full synthesis after each ECO | Loses manual ECO changes | Use incremental ECO flow |

---

## What's Next

- **[Setup & Hold Time — STA]({{ '/blog/2026/05/17/setup-hold-time-sta/' | relative_url }})** — the theory behind setup and hold checks
- **[SDC Timing Constraints]({{ '/blog/2026/05/17/sdc-timing-constraints/' | relative_url }})** — ensure constraints are correct before blaming the design
- **[Clock Tree Synthesis]({{ '/blog/2026/05/19/clock-tree-synthesis-cts/' | relative_url }})** — clock skew directly affects hold violations
