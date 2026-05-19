---
layout: post
title: "Clock Tree Synthesis (CTS) — How the Clock Reaches Every Flip-Flop"
description: "Understand Clock Tree Synthesis: clock skew, insertion delay, H-tree topology, buffer insertion, useful skew, NDR routing rules, and Innovus CTS commands — the step between floorplanning and routing."
date: 2026-05-19
category: ASIC Flow
tags: [cts, clock-tree, skew, asic, innovus, physical-design, timing, pnr, intermediate]
image: cts-htree.svg
---

After placement, every flip-flop in your design needs a clock signal. In a chip with millions of FFs spread across 10 mm², you cannot just run a single wire from the PLL to every FF — the wire delay would be huge, different FFs would see the clock at wildly different times, and the capacitance would be enormous. **Clock Tree Synthesis (CTS)** solves this by inserting a balanced tree of clock buffers so that every FF sees the clock at approximately the same time.

---

## What CTS Must Achieve

CTS has three goals, in priority order:

| Goal | Target (typical 7 nm SoC) | Why It Matters |
|------|--------------------------|----------------|
| **Minimise clock skew** | < 50 ps | Skew steals timing budget from every path |
| **Minimise insertion delay** | < 500 ps | Long insertion delay means less margin for data paths |
| **Meet DRV targets** | No max-cap/max-tran violations | Buffers must be sized to drive clock net legally |

---

## Clock Skew and Why It Kills Timing

**Clock skew** is the arrival time difference between the clock at the launch FF and the capture FF:

```
Tskew = T_capture_clock - T_launch_clock

Setup slack  = Tclk - Tsu - Tcq - Tlogic + Tskew
Hold  slack  = Tcq + Tlogic - Th - Tskew
```

**Positive skew** (capture FF clock arrives later than launch FF clock):
- ✅ Helps setup timing — capture FF has more time to receive data
- ❌ Hurts hold timing — data arrives too early relative to the late capture clock

**Negative skew** (capture FF clock arrives earlier):
- ❌ Hurts setup timing — capture FF clocks in before data arrives
- ✅ Helps hold timing

A 200 ps skew on a 1 GHz clock (1000 ps period) eats 20% of your timing budget immediately. CTS targets skew below 50 ps on modern designs.

---

## Clock Insertion Delay

**Clock insertion delay** is the time from the clock source (PLL output) to the FF clock pin:

```
T_insertion = sum of all buffer delays along the clock path
```

Insertion delay of 400 ps on a 1 GHz clock means data must arrive at the FF input 400 ps *after* the PLL output rises. This is accounted for in STA automatically — but larger insertion delay means more power (bigger buffers) and more area.

---

## H-Tree Topology — Equal Lengths, Equal Delays

The most common CTS topology for regular chip layouts is the **H-tree**: a binary tree where every path from root to leaf has identical wire length.

<img src="{{ '/assets/images/cts-htree.svg' | relative_url }}" alt="H-tree clock distribution topology" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

**Why equal lengths work:** Wire delay is proportional to length (R × C). Equal lengths → equal wire delays → equal arrival times → minimal skew.

**Buffer insertion at each level:**
- Each branch drives fewer FFs → smaller capacitance
- Each buffer is sized to meet max-capacitance and max-transition DRV targets
- Typical design: 4–8 buffer levels for large dies

**Other topologies:**

| Topology | Best for | Trade-off |
|----------|---------|-----------|
| H-tree | Square symmetric dies | Doesn't fit irregular floorplans |
| Fishbone | Long narrow dies | Slightly higher skew at extremes |
| Mesh | Ultra-low skew (< 10 ps) | Very high power — many buffers |
| Spine | Simple, low fanout | Only for small designs |

---

## CTS in Innovus — Step by Step

### Step 1 — Define the Clock Tree Specification

```tcl
# Specify which cells to use for clock buffers and inverters
set_ccopt_property buffer_cells  {CLKBUFX2 CLKBUFX4 CLKBUFX8 CLKBUFX16}
set_ccopt_property inverter_cells {CLKINVX2 CLKINVX4}

# Set targets
set_ccopt_property target_skew        0.050   ;# 50 ps
set_ccopt_property target_insertion_delay 0.5 ;# 500 ps

# Non-default routing rules for clock nets
add_ndr -name CLK_NDR \
    -width {M3 0.2 M4 0.2 M5 0.4} \
    -spacing {M3 0.2 M4 0.2 M5 0.4}   ;# 2x width, 2x spacing

# Assign NDR to clock nets
set_db [get_nets -of_objects [get_pins -hierarchical */CK]] \
    .ndr CLK_NDR
```

### Step 2 — Run CTS

```tcl
# Run CTS with concurrent optimisation
ccopt_design

# Alternatively for older Innovus flows:
# create_clock_tree_spec
# clock_design
```

### Step 3 — Report and Analyse

```tcl
# Report skew and insertion delay
report_clock_tree -summary
report_clock_tree -skew

# Check for DRV violations (max cap, max tran) on clock nets
report_constraint -max_capacitance -all_violators
report_constraint -max_transition   -all_violators

# Timing with propagated (real) clocks
set_propagated_clock [all_clocks]
report_timing -max_paths 20

# Clock tree power
report_power -clock_only
```

**Example output:**
```
Clock Tree Report — clk (500 MHz)
──────────────────────────────────────────────
  Source:           u_pll/CLK_OUT
  Sinks:            48,320 FF clock pins
  Insertion delay:  387 ps (max) / 342 ps (min)
  Global skew:      45 ps   ← target: 50 ps ✓
  Local skew:       38 ps
  Buffer count:     1,240
  Clock net length: 18.4 mm
  Clock power:      42.3 mW (32% of total)
──────────────────────────────────────────────
```

---

## Ideal vs Propagated Clocks

| Mode | When used | Skew modelled? |
|------|-----------|----------------|
| **Ideal clocks** | Pre-CTS (synthesis, placement) | No — clock arrives everywhere at T=0 |
| **Propagated clocks** | Post-CTS (routing, sign-off) | Yes — actual buffer delays computed |

```tcl
# In synthesis (DC) — ideal clocks
create_clock -name clk -period 2.0 [get_ports clk]
# Skew is modelled via set_clock_uncertainty:
set_clock_uncertainty -setup 0.05 [get_clocks clk]  ;# 50 ps budget

# After CTS in Innovus — switch to propagated
set_propagated_clock [all_clocks]
# Now STA uses actual measured skew from the clock tree
```

---

## Useful Skew — Borrowing Time From Slack

After CTS, the tool can intentionally **shift** the clock arrival time at individual FFs to fix timing violations. This is called **useful skew** or **skew scheduling**:

```
Path A has setup slack = +300 ps  (lots of margin)
Path B has setup slack =  -50 ps  (failing by 50 ps)

Solution: Delay capture FF clock of path B by 60 ps
  → Path B setup slack = -50 + 60 = +10 ps  ✓
  → Path A setup slack = +300 - 60 = +240 ps ✓ (still positive)
```

```tcl
# Enable useful skew in Innovus
set_ccopt_property -opt_type local
# Or post-CTS incremental skew optimisation:
ccopt_skew_opt -effort high
```

**Warning:** Useful skew helps setup but worsens hold on those paths — the tool must simultaneously meet hold. Never apply useful skew manually without checking hold.

---

## Clock Gating and CTS Interaction

Integrated Clock Gate (ICG) cells sit in the clock tree path:

```
PLL → Buffer → ICG (latch + AND) → Leaf Buffer → FF
```

```tcl
# Tell CTS to treat ICG cells as transparent clock endpoints
# (CTS balances to the ICG output, not the FF directly)
set_ccopt_property -inst_types clock_gate {ICGX1 ICGX2 ICGX4}

# Report clock gating coverage
report_clock_gating -summary
```

**CTS rule:** Clock gates must be placed *before* leaf buffers — never after. The ICG latch captures the enable on the clock falling edge, so it must be in the tree above the final buffers.

---

## NDR — Non-Default Routing Rules for Clock Nets

Clock nets use wider wires and larger spacing to:
- Reduce resistance → lower RC delay
- Reduce coupling → lower noise / crosstalk-induced jitter

```tcl
# 2× width on M3/M4, 2× spacing around clock nets
add_ndr -name CLK_2W2S \
    -width  {M3 0.14  M4 0.14  M5 0.28} \
    -spacing {M3 0.14  M4 0.14  M5 0.28}

# Check NDR application
report_ndr -all
```

---

## Post-CTS Checklist

Before routing:

- [ ] Global skew < 50 ps (< 5% of clock period)
- [ ] Max insertion delay < 10% of clock period
- [ ] Zero max-cap violations on clock nets
- [ ] Zero max-tran violations on clock nets
- [ ] Propagated clocks set — no ideal clocks remaining
- [ ] Setup/hold pass with propagated clocks (may have post-route violations, but pre-route should be clean)
- [ ] Clock gating cells correctly placed in clock tree
- [ ] NDR rules applied to all clock nets

---

## Common CTS Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Using data cells (non-CK buffers) in clock tree | Duty-cycle distortion, extra jitter | Use only clock-specific buffer/inverter cells |
| Skipping NDR on clock nets | High jitter from crosstalk | Always apply 2W2S NDR to clock routing |
| Running STA with ideal clocks post-CTS | Optimistic results — real skew not seen | Switch to `set_propagated_clock` after CTS |
| Ignoring DRV violations on clock nets | Max-cap → slow rise/fall → jitter | Fix all clock DRV violations before routing |
| Not including ICG outputs as CTS endpoints | Unbalanced sub-trees | Register ICG cells with CTS tool |

---

## What's Next

- **[VLSI Floorplanning]({{ '/blog/2026/05/17/vlsi-floorplanning/' | relative_url }})** — the step before CTS: place macros and build the power grid
- **[Power Analysis in ASIC Design]({{ '/blog/2026/05/17/power-analysis-asic/' | relative_url }})** — clock tree typically consumes 30–50% of total chip power
- **[SDC Timing Constraints]({{ '/blog/2026/05/17/sdc-timing-constraints/' | relative_url }})** — `set_clock_uncertainty` models pre-CTS skew budget
