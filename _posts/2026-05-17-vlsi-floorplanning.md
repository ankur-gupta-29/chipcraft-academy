---
layout: post
title: "VLSI Floorplanning — Concepts, Techniques & Trade-offs"
description: "Learn VLSI floorplanning: die size, core utilisation, macro placement, power stripes, pin assignment, and floorplan quality metrics — with practical guidance for Innovus and ICC2."
date: 2026-05-17
category: ASIC Flow
tags: [floorplanning, vlsi, asic, innovus, icc2, macro-placement, power, pnr, physical-design]
image: /assets/images/floorplan-diagram.svg
---

After synthesis, the gate netlist is a flat list of cells with no physical location. Floorplanning gives each major block a home on the chip and sets up the power infrastructure. A good floorplan makes everything downstream (placement, routing, timing closure) easier. A bad floorplan can make closure impossible regardless of how good the later steps are.

---

## What Is Floorplanning?

Floorplanning determines:
1. **Die size** — total chip area
2. **Core area** — where standard cells and macros go (inside the IO ring)
3. **Macro placement** — where large blocks (SRAMs, IP cores, PHYs) are placed
4. **Power grid** — VDD/VSS stripes and rings
5. **Pin assignment** — where top-level signal pins land on the die boundary

<img src="{{ '/assets/images/floorplan-diagram.svg' | relative_url }}" alt="VLSI SoC floorplan showing core area, macros, and IO ring" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

---

## Die Size and Utilisation

**Core utilisation** is the fraction of the core area occupied by cells:

```
Utilisation = (Cell area) / (Core area) × 100%
```

| Utilisation | Effect |
|------------|--------|
| < 50% | Wasteful — die too large, routing trivial |
| 60–70% | Typical target — good routing room |
| 75–80% | Aggressive — routing congestion likely |
| > 85% | Very difficult to close timing and DRC |

```tcl
# Innovus: set up floorplan with 70% utilisation, 2μm margins
floorPlan -site CoreSite \
          -utilization 0.70 \
          -aspectRatio 1.0 \
          -coreMarginsBy io \
          -ioMargins {5 5 5 5}
```

**Aspect ratio:** Width/Height. 1.0 = square. Long thin die increases wire lengths on one axis.

---

## The IO Ring

The IO ring surrounds the core area and contains:
- **Signal pads** — data, address, control I/Os
- **Power pads** — VDD and VSS bumps/pads distributed around the perimeter
- **Corner cells** — fill corners between IO rows
- **IO filler cells** — fill gaps between signal pads

```tcl
# Innovus: add IO pads from pad library
loadIoFile design.io       # .io file specifies pad placement
addIoPad -inst pad_clk -side bottom -location 350
addIoPad -inst pad_data0 -side left -location 100
```

For flip-chip designs (BGA), IO pads are replaced by **bumps** over the entire die area — the IO ring concept doesn't apply.

---

## Macro Placement Guidelines

Macros are large hard IP blocks (SRAMs, PLLs, USB PHYs, DDR controllers). Their placement dominates the floorplan quality.

**Golden rules:**

| Rule | Reason |
|------|--------|
| Place macros against die edges or in corners | Leaves contiguous standard-cell area in the middle |
| Keep SRAMs on the same side as the blocks that access them | Short routing between SRAM ports and logic |
| Align macro data bus to standard-cell rows | Reduces routing detours |
| Leave a halo (keepout) around each macro | Physical DRC clearances; routing channel |
| Place PLL away from switching logic | Reduces noise coupling into PLL supply |
| Keep clock source central | Minimises clock tree length, reduces skew |

```tcl
# Innovus: place macro with keepout
placeInstance u_sram_0 100 100 R0      # x y orientation
setPlaceBlockage -type hardMacro \
    -inst u_sram_0 \
    -margin 5                           # 5μm halo all sides
```

---

## Power Planning

A robust power grid is set up during floorplanning. If the grid is too weak, IR drop violations kill timing at sign-off (cells run slowly when Vdd sags).

### Power Rings

Run wide VDD/VSS rings around the core area:

```tcl
# Add core power rings
addRing \
    -nets {VDD VSS} \
    -width 8 \
    -spacing 2 \
    -layer {top M8 bottom M8 left M9 right M9}
```

### Power Stripes

Vertical/horizontal stripes through the core supply power to standard cells:

```tcl
# Add VDD/VSS metal stripes on M8 (vertical)
addStripe \
    -nets {VDD VSS} \
    -layer M8 \
    -width 4 \
    -spacing 2 \
    -pitch 50 \           # one VDD+VSS pair every 50μm
    -start_from left \
    -stop_before_boundary
```

### Standard Cell Rails

The bottom metal (M1) standard cell power rails are part of the standard cell itself. They connect to the stripes through M2–M7 vias.

### IR Drop Rule of Thumb

```
IR drop budget = 3% of VDD
At 1V, allow max 30 mV drop

Check with: report_power_domain -type IR
```

---

## Pin Assignment

Top-level pins connect the core logic to the IO pads:

```tcl
# Assign pin location and layer
setPinAssignMode -pinEditInBatch true
editPin -pin clk     -side Bottom -layer M4 -offset 200
editPin -pin rst_n   -side Bottom -layer M4 -offset 220
editPin -pin data_in -side Left   -layer M4 -offset {100 120 140 160}
```

**Pin assignment best practices:**
- Group related signals (address bus, data bus) on the same side
- Place high-frequency pins (clk) away from noisy power pads
- Leave routing channels between macro ports and pins

---

## Floorplan Quality Metrics

After placing the floorplan, check these before proceeding to placement:

| Metric | How to check | Target |
|--------|-------------|--------|
| Utilisation | `report_floorplan` | 60–75% |
| Estimated congestion | `congestionMap` | No hotspots |
| IR drop estimate | `report_power` (pre-route) | < 3% VDD |
| Timing (estimated) | `report_timing` (with ideal clocks) | No large violations |
| Macro overlap | `checkFloorplan` | Zero overlaps |
| Macro channel width | Visual inspection | ≥ 10× min metal pitch |

```tcl
# Innovus: full floorplan check
checkFloorplan
reportFloorplan
congestionMap -global
```

---

## Floorplan in the ASIC Flow

```
Synthesis (DC/Genus)
       ↓
Floorplan (Innovus/ICC2)   ← you are here
       ↓
Power Planning
       ↓
Standard Cell Placement
       ↓
Clock Tree Synthesis (CTS)
       ↓
Routing
       ↓
Timing Sign-off (PrimeTime)
       ↓
GDSII Export (Calibre DRC/LVS)
```

---

## Common Floorplan Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Macros scattered in core centre | Fragments standard-cell area | Push macros to edges/corners |
| No macro halo | DRC violations at macro boundary | Add 5–10μm keepout |
| Under-utilisation (40%) | Die too large — expensive | Increase density or reduce die |
| Over-utilisation (>80%) | Routing congestion, timing closure fails | Enlarge die or reduce cell count |
| Weak power grid (narrow stripes) | High IR drop → slow cells → timing violations | Widen stripes, increase density |
| No pin grouping | Long routing detours | Group functional buses on same die side |

---

## What's Next

- **[RTL Synthesis with Design Compiler]({{ site.baseurl }}{% post_url 2026-05-17-synopsys-design-compiler %})** — the step before floorplanning
- **[Power Analysis in ASIC Design]({{ site.baseurl }}{% post_url 2026-05-17-power-analysis-asic %})** — quantify the power budget your grid must supply
- **[Cadence Virtuoso & Innovus Shortcuts]({{ site.baseurl }}{% post_url 2026-05-13-cadence-virtuoso-innovus-shortcuts %})** — keyboard shortcuts for faster floorplan editing in Innovus
