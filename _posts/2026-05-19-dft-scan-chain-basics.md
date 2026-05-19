---
layout: post
title: "Design for Test (DFT) & Scan Chains — ASIC Testability Guide"
description: "Understand DFT fundamentals: why chips need scan test, scan flip-flop internals, scan chain insertion with Design Compiler, ATPG fault models, stuck-at coverage targets, JTAG basics, and test compression."
date: 2026-05-19
category: ASIC Flow
tags: [dft, scan, atpg, jtag, testability, design-compiler, asic, tapeout, intermediate]
image: scan-chain-diagram.svg
---

You've designed your ASIC, verified it in simulation, and it passed every testbench. But once it's packaged in plastic, you can't probe any internal wire. How do you know if the manufactured chip works? **Design for Test (DFT)** solves this by adding test infrastructure to the chip before tapeout, allowing factory test equipment to detect manufacturing defects.

---

## Why DFT Is Non-Negotiable

Without DFT:
- A defective chip looks identical to a good one from the outside
- You can only test a handful of pins — completely missing internal logic
- Yield loss is invisible — you ship defective chips to customers

With DFT (scan test):
- Every flip-flop in the design is observable and controllable
- Test patterns can detect > 99% of manufacturing defects
- Typical stuck-at fault coverage target: **≥ 97–99%** for tapeout sign-off

---

## Fault Models — What Are We Testing For?

| Fault Model | Description | How detected |
|-------------|-------------|-------------|
| **Stuck-at-0 (SA0)** | Node permanently stuck at logic 0 | Apply pattern where node should be 1; observe wrong output |
| **Stuck-at-1 (SA1)** | Node permanently stuck at logic 1 | Apply pattern where node should be 0; observe wrong output |
| **Transition fault** | Node slow-to-rise or slow-to-fall | Apply at-speed patterns and check timing |
| **Bridging fault** | Two nets shorted together | Functional coverage with certain patterns |
| **Open fault** | Net broken — floating | Similar to stuck-at or transition |

Stuck-at faults are the primary industry standard. Transition faults are added for advanced nodes where delay defects are common.

---

## The Scan Flip-Flop (SFF)

A standard flip-flop has one data input D. A **scan flip-flop** adds a 2-to-1 MUX before D, controlled by a **scan enable (SE)** signal:

<img src="{{ '/assets/images/scan-chain-diagram.svg' | relative_url }}" alt="Scan flip-flop and scan chain diagram" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

```
SE = 0 (Functional mode):  FF captures D input  — normal chip operation
SE = 1 (Scan/shift mode):  FF captures SI input — test data shifts through
```

In Verilog, a scan FF looks like:

```verilog
// Scan flip-flop model (for understanding — library cell in real design)
module scan_dff (
    input  wire clk,
    input  wire d,      // functional data
    input  wire si,     // scan in (from previous FF's Q)
    input  wire se,     // scan enable
    output reg  q,      // output (also drives next FF's SI)
    output wire so      // scan out (same as q)
);
    always @(posedge clk)
        q <= se ? si : d;   // MUX: select scan or functional input

    assign so = q;
endmodule
```

The synthesis tool automatically replaces all standard FFs with SFFs during DFT insertion — you don't instantiate SFFs manually in RTL.

---

## Scan Chain — Connecting FFs into a Shift Register

All scan FFs are chained together: the Q output of each FF connects to the SI (scan input) of the next:

```
SCAN_IN → [SFF₁ Q→SI] → [SFF₂ Q→SI] → [SFF₃ Q→SI] → ... → [SFFₙ] → SCAN_OUT
```

This turns the entire flip-flop array into one long shift register that is:
- **Accessible** via only 2 pins: SCAN_IN and SCAN_OUT
- **Controllable** — you can shift any test pattern into any FF
- **Observable** — you can shift out every FF's state and inspect it

### The 3-Phase Test Sequence

```
Phase 1 — Shift-in  (SE=1, N clock cycles):
    Shift the test pattern (N bits) into the scan chain serially via SCAN_IN
    This loads specific values into every FF in the design

Phase 2 — Capture   (SE=0, 1 clock cycle):
    Apply one functional clock cycle — combinational logic operates normally
    Each FF captures the result of the logic connected to its D input

Phase 3 — Shift-out (SE=1, N clock cycles):
    Shift all FF contents out via SCAN_OUT
    Compare against expected response — any mismatch = defect detected
```

**Example:** A design with 10,000 FFs in a single chain needs 10,000 clock cycles to shift in and 10,000 more to shift out — 20,001 cycles total per pattern.

---

## DFT Insertion with Design Compiler

Design Compiler automates scan chain insertion. The flow runs after logic synthesis:

```tcl
# ── Step 1: Define scan configuration ────────────────────────────
set_scan_configuration \
    -chain_count 4 \          ;# 4 scan chains (4 SCAN_IN/OUT pin pairs)
    -style multiplexed_flip_flop  ;# use MUX-D scan FF style

# ── Step 2: Specify which pins are scan I/O ───────────────────────
set_dft_signal -view existing_dft \
    -type ScanClock -timing {45 55} [get_ports clk]

set_dft_signal -view spec \
    -type ScanEnable -active_state 1 [get_ports scan_en]

set_dft_signal -view spec \
    -type ScanDataIn  [get_ports {scan_in[*]}]

set_dft_signal -view spec \
    -type ScanDataOut [get_ports {scan_out[*]}]

# ── Step 3: Preview the DFT insertion ─────────────────────────────
preview_dft -show all

# ── Step 4: Insert scan chains ────────────────────────────────────
insert_dft

# ── Step 5: Verify and report ─────────────────────────────────────
report_scan_path -view existing_dft -chain all
dft_drc             ;# DFT design rule check

# ── Step 6: Write out DFT netlist ─────────────────────────────────
write -format verilog -hierarchy \
      -output outputs/design_with_dft.v
write_test_protocol -output outputs/scan.spf   ;# scan protocol file for ATPG
```

---

## ATPG — Automatic Test Pattern Generation

ATPG software (Synopsys TetraMAX, Siemens Tessent) reads the DFT netlist and automatically generates test patterns that can detect stuck-at faults:

```
Input:  Gate-level netlist with scan chains + scan protocol file
Output: Test patterns (ATPG patterns) + fault coverage report

Algorithm:
1. List all possible stuck-at faults (SA0 + SA1 on every node)
2. For each fault, find a pattern that: 
   a) Activates the fault (excite the node to opposite value)
   b) Propagates the effect to a scan FF output (observe it)
3. Compact patterns (many faults covered per pattern)
```

```bash
# TetraMAX ATPG run
tmax design_with_dft.v -scan
run_atpg -mode stuck           # stuck-at fault coverage
report_summaries faults        # fault coverage report
write_patterns patterns.stil   # test patterns for ATE
```

**Example ATPG report:**
```
Fault Coverage Summary
──────────────────────────────────────────────────
Total faults:         184,320
Detected faults:      183,140   (99.36%)
Possibly detected:        840
Undetectable:             240
Aborted:                  100
──────────────────────────────────────────────────
Stuck-at coverage:    99.36%  ✓ (target: 99%)
Pattern count:          1,248
Test time @ 100 MHz:   24.9 ms
```

---

## Scan Chain Length Trade-offs

| Chain length | Pins needed | Shift time | Test time |
|-------------|------------|------------|-----------|
| 1 long chain (all FFs) | 2 pins | N cycles | Very long |
| 4 chains (FFs/4 each) | 8 pins | N/4 cycles | 4× faster |
| 16 chains | 32 pins | N/16 cycles | 16× faster |
| Compressed (EDT) | 4 pins effective | Very short | 100× faster |

**Typical target:** Use enough chains so test time < 1 second at ATE speed (typically 50–200 MHz). A 10M-FF design with 1 chain at 100 MHz would take 100 seconds — too slow. 100 chains reduces it to 1 second.

---

## Test Compression (EDT / Tessent)

Modern chips have 10–100 million FFs. Even with 100 scan chains, test time can be minutes. **Compression logic** multiplexes many virtual chains onto a few physical pins:

```
Without compression: 100 scan chains = 200 I/O pins
With EDT compression: 100 virtual chains → 4 physical pins (25× fewer pins)
                      Pattern count also reduced → 10-100× faster test

Compression ratio = Virtual chains / Physical channels
                  = 100 / 4 = 25× (typical: 10–100×)
```

```tcl
# Enable compression in Design Compiler DFT
set_scan_compression_configuration \
    -chain_count 100 \         ;# 100 virtual chains
    -compressed_chain_count 4  ;# 4 physical scan I/O pairs

insert_dft
```

---

## JTAG — Boundary Scan (IEEE 1149.1)

JTAG (Joint Test Action Group) is a 4-wire serial interface for board-level test and debugging, standardised as IEEE 1149.1:

| Pin | Function |
|-----|---------|
| **TCK** | Test Clock — drives all JTAG operations |
| **TMS** | Test Mode Select — controls the TAP state machine |
| **TDI** | Test Data In — serial input |
| **TDO** | Test Data Out — serial output |
| **TRST** | Test Reset (optional) — asynchronous reset of TAP |

JTAG uses a **TAP (Test Access Port) controller** — a 16-state state machine that TMS controls:

```
Reset → Run-Test/Idle → Shift-DR → Capture-DR → ...
```

**Boundary Scan:** Scan cells around every I/O pad allow testing of board-level connections (solder joints, shorts, opens) without physical probing.

**JTAG in modern chips:** Also used as a debug port (JTAG-DP in ARM CoreSight), firmware download interface, and production programming port.

---

## DFT Checklist Before Tapeout

- [ ] Scan insertion complete — all FFs are scannable
- [ ] `dft_drc` passes with zero errors
- [ ] Scan chain count and length balanced
- [ ] ATPG patterns generated — stuck-at coverage ≥ 97%
- [ ] Transition fault coverage ≥ 90% (advanced nodes)
- [ ] Scan enable (`scan_en`) timing verified — no setup violations in shift mode
- [ ] Scan clock meets ATE timing constraints
- [ ] JTAG TAP controller included and verified
- [ ] Test protocol file (`.spf` or `.stil`) delivered with GDSII

---

## Common DFT Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Asynchronous resets in scan path | Scan shift corrupted if reset fires | Add scan-enable override on async resets |
| Gated clocks not test-mode aware | FFs downstream of gate never shift | Add `scan_en` bypass around all clock gates |
| Tri-state buses in scan path | Contention during scan shift | Add test-mode control to tri-state enables |
| Forgetting TRST pin | JTAG TAP stuck in unknown state after power-on | Always include TRST or power-on reset for TAP |
| Running ATPG before `dft_drc` passes | Patterns generated for broken scan structure | Fix all `dft_drc` errors first |

---

## What's Next

- **[RTL Synthesis with Design Compiler]({{ '/blog/2026/05/17/synopsys-design-compiler/' | relative_url }})** — DFT insertion happens after logic synthesis in DC
- **[VLSI Floorplanning]({{ '/blog/2026/05/17/vlsi-floorplanning/' | relative_url }})** — scan I/O pins must be assigned during pin planning
- **[Timing Closure Techniques]({{ '/blog/2026/05/19/timing-closure-techniques/' | relative_url }})** — scan path timing must also meet setup/hold in shift mode
