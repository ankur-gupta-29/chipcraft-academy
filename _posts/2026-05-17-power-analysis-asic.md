---
layout: post
title: "Power Analysis in ASIC Design — Dynamic, Static & Low-Power Techniques"
description: "Understand ASIC power: dynamic power (α·C·V²·f), static leakage, clock gating, multi-Vt, power domains, UPF basics, and IR drop — with practical Verilog and tool command examples."
date: 2026-05-17
category: ASIC Flow
tags: [power, asic, low-power, clock-gating, leakage, dynamic-power, upf, multi-vt, ir-drop, beginner]
---

Power is now the primary constraint in modern chip design — often more important than area or performance. A chip that meets timing but burns 5 W when the spec says 2 W will be re-spun. This guide covers how power is calculated, where it goes, and the techniques used in industry to reduce it.

---

## The Two Types of Power

### Dynamic Power — Charging and Discharging Wires

Every time a logic node switches, the parasitic capacitance on that wire charges or discharges through the power supply:

```
P_dynamic = α × C × V²DD × f

Where:
  α   = activity factor (fraction of clock cycles the node switches)
  C   = total node capacitance (wire + gate input + diffusion)
  VDD = supply voltage
  f   = clock frequency
```

**This is why voltage reduction is so powerful:** Halving VDD reduces dynamic power by **4×** (V² dependence).

| Lever | Effect on Power |
|-------|----------------|
| Halve voltage (VDD × 0.5) | Power × 0.25 (4× reduction) |
| Halve frequency | Power × 0.5 (2× reduction) |
| Halve capacitance | Power × 0.5 (smaller cells, less wire) |
| Halve activity | Power × 0.5 (clock gating, data encoding) |

### Static Power — Leakage Through Off Transistors

Even when a transistor is "off", sub-threshold leakage current flows from drain to source:

```
P_static = I_leak × VDD

I_leak increases exponentially with temperature and
decreases exponentially with threshold voltage (Vt).
```

In advanced nodes (7 nm, 5 nm), leakage can equal or exceed dynamic power.

---

## Where Does the Power Go?

Typical power breakdown for a mobile SoC:

| Component | Fraction |
|-----------|---------|
| Clock tree (clock buffers + FFs) | 25–40% |
| Datapath (adders, muxes, shifters) | 20–30% |
| Memory (SRAM read/write) | 15–25% |
| IO drivers | 5–15% |
| Leakage (all cells) | 10–20% |

**The clock tree is usually the biggest consumer** — it switches every cycle even when the datapath is idle. This is why clock gating gives such large savings.

---

## Technique 1 — Clock Gating

Disable the clock to a register (or block of registers) when the data isn't changing:

```verilog
// ❌ Without clock gating — flop switches every cycle
always @(posedge clk)
    if (load_en) data_reg <= data_in;

// ✓ With clock gating — clock only ticks when load_en = 1
// ICG = Integrated Clock Gate cell (latch + AND gate)

// RTL that synthesis tools can infer as a clock gate:
always @(posedge clk)
    if (load_en) data_reg <= data_in;
// With compile_ultra -gate_clock, DC automatically inserts ICG cells

// Or instantiate explicitly:
ICGX1 u_icg (
    .CLK (clk),
    .EN  (load_en),
    .SE  (scan_en),   // scan enable — bypass gate during test
    .GCLK(gated_clk)
);
always @(posedge gated_clk)
    data_reg <= data_in;
```

**Clock gating saves up to 40% of dynamic power** in typical designs.

**ICG cell internals** — why it's a latch, not just an AND gate:
```
         ┌──────┐
clk ─────┤ Latch├──┐
en ──────┤ (D)  │  └──AND──► gated_clk
scan_en─►└──────┘
```
The latch captures `en` on the clock falling edge, preventing glitches on `gated_clk`.

---

## Technique 2 — Multi-Threshold Voltage (Multi-Vt)

Technology libraries provide cells at different threshold voltages:

| Cell type | Vt | Speed | Leakage | Use for |
|-----------|----|----|---------|---------|
| HVT (High Vt) | High | Slow | Very low | Non-critical paths |
| SVT (Standard Vt) | Medium | Medium | Medium | General logic |
| LVT (Low Vt) | Low | Fast | High | Critical paths only |
| ULVT (Ultra-low) | Very low | Fastest | Very high | Only on the critical path |

**Multi-Vt strategy:**
```tcl
# Synthesis: use HVT by default, allow LVT on critical paths
set_attribute [get_lib_cells slow/HVT*] dont_use false
set_attribute [get_lib_cells slow/LVT*] dont_use true   # start with HVT only
compile_ultra
# Then selectively allow LVT for timing-critical paths:
set_attribute [get_lib_cells slow/LVT*] dont_use false
compile_ultra -incremental
```

After routing, run **Vt-swap** (replace HVT→LVT for timing, LVT→HVT for leakage) to optimise both simultaneously.

---

## Technique 3 — Power Domains and Voltage Islands

Different blocks can run at different voltages:

```
┌─────────────────────────────────┐
│         SoC Top Level           │
│  ┌──────────┐  ┌─────────────┐  │
│  │ CPU Core │  │ Always-On   │  │
│  │ 0.9V     │  │ Block 1.0V  │  │
│  │ (can be  │  │ (RTC, PMU,  │  │
│  │  gated)  │  │  wakeup)    │  │
│  └──────────┘  └─────────────┘  │
│  ┌──────────────────────────┐   │
│  │ SRAM  0.85V (retention)  │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

When the CPU is idle, its power domain is **shut down** (power gated) — leakage drops to near zero.

---

## Technique 4 — Power Gating (MTCMOS)

Power gating uses high-Vt "header" (PMOS) or "footer" (NMOS) switches to disconnect a block from VDD or VSS when idle:

```verilog
// UPF (Unified Power Format) — describes power intent
// Always-on domain (never powered off)
create_power_domain PDaon \
    -elements {u_pmu u_rtc}

// CPU domain (can be shut off)
create_power_domain PDcpu \
    -elements {u_cpu}

// Power switch for CPU domain
create_power_switch PSW_CPU \
    -domain PDcpu \
    -output_supply_port {vdd VDD_CPU} \
    -input_supply_port  {vin VDD_AON} \
    -control_port       {en cpu_pwr_en} \
    -on_state           {on vin {en}}

// Isolation cells: prevent floating outputs from off domain driving on-domain inputs
set_isolation ISO_CPU \
    -domain PDcpu \
    -isolation_power_net  VDD_AON \
    -isolation_ground_net VSS \
    -clamp_value          0 \
    -applies_to           outputs

// Retention registers: save state before power-off
set_retention RET_CPU \
    -domain PDcpu \
    -retention_power_net VDD_AON
```

**Power gating savings:** 90–99% reduction in leakage for the gated domain.

---

## Technique 5 — Dynamic Voltage and Frequency Scaling (DVFS)

Run at the minimum voltage and frequency needed for the current workload:

| Mode | VDD | Frequency | Power |
|------|-----|-----------|-------|
| High performance | 1.0V | 2 GHz | 3.0 W |
| Normal | 0.85V | 1.5 GHz | 1.4 W |
| Low power | 0.7V | 800 MHz | 0.5 W |
| Deep sleep | 0.5V | 0 MHz | 0.05 W |

DVFS is controlled by the PMIC (Power Management IC) based on OS workload signals.

---

## Technique 6 — Operand Isolation

Prevent switching in downstream logic when the result isn't needed:

```verilog
// ❌ Without isolation — multiply always switches
assign product = a * b;
always @(posedge clk)
    if (mul_en) result <= product;

// ✓ With operand isolation — inputs gated when not computing
wire [31:0] a_gated = mul_en ? a : '0;
wire [31:0] b_gated = mul_en ? b : '0;
assign product = a_gated * b_gated;   // zero inputs → zero activity → zero power
```

---

## Power Estimation in Design Compiler

```tcl
# After synthesis, get power estimate (without switching activity)
report_power

# Better: provide switching activity from simulation
read_saif -input sim.saif -instance_name u_core/u_alu
report_power -analysis_effort high

# Or annotate with VCD
read_vcd sim.vcd -strip_path tb/u_dut
report_power
```

**Report output (example):**
```
                 Int Power   Switch Power  Leak Power   Total
                 (mW)        (mW)          (μW)         (mW)
─────────────────────────────────────────────────────────────
u_alu             0.432        0.218         12.4        0.662
u_regfile         0.318        0.142          9.8        0.470
u_clk_tree        1.240        0.820          2.1        2.062
─────────────────────────────────────────────────────────────
Total             2.880        1.864         42.1        4.786
```

---

## IR Drop — Power Grid Resistance

As current flows through metal wires from the pad to the cells, there's a resistive voltage drop:

```
V_cell = VDD - (I × R_grid)
```

If IR drop is too high, cells see lower VDD → they run slower → timing violations at sign-off (even though they met timing with full VDD).

**IR drop analysis:**
```tcl
# Innovus post-route IR drop (static)
set_analysis_mode -analysisType onChipVariation
report_power_domain -type IR -threshold 5  # flag nets with >5mV drop

# Dynamic IR drop (more accurate — needs switching activity)
rail_analyze -type dynamic -power_db power.db
```

**Fixing IR drop:**
- Widen power stripes
- Add more power vias
- Move high-current macros closer to power pads
- Add decap (decoupling capacitor) cells near switching logic

---

## Low-Power Checklist

Before tape-out:

- [ ] Clock gating inserted on all register banks (≥ 4 FFs)
- [ ] Multi-Vt: HVT on >50% of non-critical cells
- [ ] Power domains defined in UPF; isolation cells inserted
- [ ] Retention registers on all state that must survive power-down
- [ ] IR drop analysis run; all domains < 3% VDD drop
- [ ] SAIF/VCD-based power report: total within budget
- [ ] `set_max_dynamic_power` constraint met
- [ ] Leakage within package thermal budget

---

## What's Next

- **[VLSI Floorplanning]({% post_url 2026-05-17-vlsi-floorplanning %})** — design the power grid that delivers current to all cells
- **[RTL Synthesis with Design Compiler]({% post_url 2026-05-17-synopsys-design-compiler %})** — enable `compile_ultra -gate_clock` for automatic clock gating insertion
- **[SDC Timing Constraints]({% post_url 2026-05-17-sdc-timing-constraints %})** — timing constraints also constrain power via `set_max_dynamic_power`
