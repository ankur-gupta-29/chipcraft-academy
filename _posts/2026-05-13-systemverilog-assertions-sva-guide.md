---
layout: post
title: "SystemVerilog Assertions (SVA) — Complete Beginner Guide"
description: "Master SystemVerilog Assertions (SVA): immediate vs concurrent assertions, sequences, properties, temporal operators ##n, |-> |=>, $rose/$fell/$past, repetition, and coverage directives — with verified examples."
date: 2026-05-13
category: Verification
tags: [sva, systemverilog, assertions, verification, rtl, property, sequence, formal, beginner]
---

Assertions are executable specification — they describe *what the design must always do* and automatically flag violations during simulation or formal verification. This guide covers every SVA construct you need, from your first `assert` statement to multi-cycle temporal properties, with examples verified against the SystemVerilog LRM and industry sources.

---

## Why Assertions?

Without assertions, a bug surfaces as a wrong output *somewhere* — you observe a symptom far from the root cause. An assertion fires *at the moment the protocol is violated*, pointing directly to the bug.

| | Testbench checks | Assertions |
|--|-----------------|------------|
| Location | End of test | Inline with RTL |
| Fires when | You write a check | Continuously, every cycle |
| Root-cause distance | Often far | At the violation |
| Formal verification | No | Yes (property-based) |
| Simulator overhead | Low | Low–Medium |

SVA assertions also work with **formal property verification** tools (Cadence JasperGold, Synopsys VC Formal) — no simulation required.

---

## Two Types: Immediate vs Concurrent

### Immediate Assertions — Procedural, Single Cycle

Immediate assertions work inside `always`, `initial`, or `task` blocks. They check a condition *right now*, with no notion of time or clock edges.

```systemverilog
always @(posedge clk) begin
    // Check: data_valid must never be X or Z
    assert (data_valid !== 1'bx)
        else $error("data_valid is X at time %0t", $time);

    // Check: if ack, req must also be high
    assert (ack |-> req)
        else $fatal(2, "ACK without REQ — protocol violation");
end
```

Severity levels:
| Keyword | Behaviour |
|---------|-----------|
| `$info` | Print message, continue |
| `$warning` | Print warning, continue |
| `$error` | Print error, increment error count, continue |
| `$fatal` | Print message, terminate simulation |

---

### Concurrent Assertions — Temporal, Multi-Cycle

Concurrent assertions run *in parallel* with your design. They use a clock to sample signals and can span many cycles using temporal operators.

```systemverilog
// Basic concurrent assertion — fires every rising edge
assert property (@(posedge clk) req |-> ack);

// Full syntax: named property + assertion
property p_req_ack;
    @(posedge clk)
    disable iff (rst)        // suppress during reset
    req |-> ##[1:4] ack;     // if req, ack must arrive within 1–4 cycles
endproperty

a_req_ack: assert property (p_req_ack)
    else $error("REQ raised but ACK did not arrive within 4 cycles");
```

Key differences from immediate assertions:

| | Immediate | Concurrent |
|--|-----------|------------|
| Clock | None (event-driven) | Explicit (`@(posedge clk)`) |
| Sampling | Current value | Clocked — avoids glitches |
| Multi-cycle | No | Yes (`##n`, `[*n]`) |
| `disable iff` | No | Yes |
| Formal tools | No | Yes |

---

## The Concurrent Assertion Syntax

```systemverilog
[label:] assert property ([clocking_event] [disable iff (expr)] property_expr)
    [pass_statement]
    [else fail_statement];
```

The clocking event can be placed in the `property` definition or in the `assert` itself:

```systemverilog
// Option 1: clock in property
property p_stable;
    @(posedge clk) disable iff (rst)
    $stable(data);
endproperty
assert property (p_stable);

// Option 2: clock in assert
property p_stable2;
    disable iff (rst) $stable(data);
endproperty
assert property (@(posedge clk) p_stable2);
```

---

## Temporal Operators

### `##n` — Fixed Delay

```systemverilog
// req is followed by ack exactly 2 cycles later
req |-> ##2 ack

// req is followed by ack 1 to 4 cycles later
req |-> ##[1:4] ack

// req is followed by ack 2 or more cycles later (no upper bound)
req |-> ##[2:$] ack
```

### `|->` vs `|=>` — Implication

```systemverilog
// |-> (overlapping): antecedent ends at cycle N, consequent starts at cycle N
req |-> ack          // if req at cycle N, ack must be high at cycle N too

// |=> (non-overlapping): consequent starts at cycle N+1
req |=> ack          // if req at cycle N, ack must be high at cycle N+1
// equivalent to:
req |-> ##1 ack
```

Think of `|->` as "simultaneously" and `|=>` as "next cycle":

```
Cycle:    0   1   2   3
req:      0   1   0   0
ack:      0   1   0   0    ← |->  passes (ack at same cycle as req)
ack:      0   0   1   0    ← |=> passes (ack one cycle after req)
```

---

## System Functions for Signal Edges

| Function | Meaning |
|----------|---------|
| `$rose(sig)` | True when `sig` transitions `0→1` (or X/Z→1) |
| `$fell(sig)` | True when `sig` transitions `1→0` (or X/Z→0) |
| `$stable(sig)` | True when `sig` did **not** change from previous clock |
| `$past(sig, n)` | Value of `sig` n clocks ago (default n=1) |
| `$isunknown(sig)` | True if any bit of `sig` is X or Z |
| `$onehot(sig)` | True if exactly one bit is 1 |
| `$onehot0(sig)` | True if at most one bit is 1 (all-zero allowed) |
| `$countones(sig)` | Number of 1-bits in `sig` |

```systemverilog
// After reset falls, valid must not assert for at least 3 cycles
property p_valid_after_rst;
    @(posedge clk)
    $fell(rst) |-> ##[1:3] !valid;
endproperty
assert property (p_valid_after_rst);

// Data must be stable while valid is high
property p_data_stable;
    @(posedge clk) disable iff (rst)
    valid && !$rose(valid) |-> $stable(data);
endproperty
assert property (p_data_stable);

// Check for X-propagation on output
always @(posedge clk) begin
    assert (!$isunknown(result))
        else $error("result is X/Z at %0t", $time);
end
```

---

## Sequences

A `sequence` is a named temporal expression — a reusable building block for properties.

```systemverilog
// A sequence that matches: req high, then ack within 1-3 cycles
sequence s_req_ack;
    req ##[1:3] ack;
endsequence

// Use in a property
property p_handshake;
    @(posedge clk) disable iff (rst)
    req |-> s_req_ack;
endproperty

// Sequences can take arguments
sequence s_pulse(sig, min_len, max_len);
    sig ##[min_len:max_len] !sig;
endsequence
```

### Repetition Operators

```systemverilog
// Consecutive repetition [*n]: sig is high for exactly n consecutive cycles
sig [*3]          // sig ##0 sig ##0 sig

// Consecutive range [*m:n]
sig [*2:5]        // sig high for 2 to 5 consecutive cycles

// Non-consecutive repetition [=n]: sig is high n times (not necessarily consecutive)
sig [=3]          // sig occurs exactly 3 times, gaps allowed

// Go-to repetition [->n]: sig high n times, last occurrence at end of match
sig [->2]         // matches second occurrence at end point
```

```systemverilog
// Example: burst of exactly 4 valid data beats
property p_burst4;
    @(posedge clk) disable iff (rst)
    $rose(burst_start) |-> valid [*4] ##1 !valid;
endproperty
assert property (p_burst4);
```

---

## `disable iff` — Suppressing During Reset

Without `disable iff`, assertions fire during reset when signals are in unknown or reset state, flooding the log with false violations.

```systemverilog
property p_no_error;
    @(posedge clk)
    disable iff (rst || !enable)   // suppress when rst OR enable is low
    valid |-> !error_out;
endproperty
assert property (p_no_error);
```

> **LRM note:** `disable iff` uses *synchronous* evaluation at the clock edge — it checks `rst` at the same sampled time as the antecedent, so a synchronous reset works correctly.

---

## Coverage Directives

Assertions check for *bad* behaviour. **Cover properties** check that *good* scenarios actually happen — they ensure your testbench exercises the design, not just that it doesn't break.

```systemverilog
// Assert: this must never happen
assert property (@(posedge clk) !(read && write))
    else $error("Simultaneous read and write");

// Cover: ensure this scenario is exercised (zero hits = test gap)
cover property (@(posedge clk) req ##2 ack);
cover property (@(posedge clk) $rose(burst_start) ##[1:10] $fell(burst_start));
```

After simulation, simulators report hit counts for cover properties. Uncovered properties indicate missing test scenarios.

---

## Binding Assertions to Modules

Instead of editing RTL to add assertions (risky), use `bind` to attach assertions externally:

```systemverilog
// alu_assertions.sv — assertion module
module alu_assertions (
    input logic        clk,
    input logic [31:0] a, b, result,
    input logic [3:0]  alu_ctrl
);
    // Result must never be X
    always @(posedge clk)
        assert (!$isunknown(result))
            else $error("ALU result is X, ctrl=%0d", alu_ctrl);

    // ADD must give correct sum (lower 32 bits)
    property p_add_correct;
        @(posedge clk)
        (alu_ctrl == 4'd0) |-> (result == a + b);
    endproperty
    assert property (p_add_correct)
        else $error("ADD incorrect: %0d + %0d = %0d (expected %0d)",
                    a, b, result, a+b);
endmodule

// tb_top.sv — bind without touching alu.v
bind alu alu_assertions u_alu_assert (
    .clk      (1'b0),   // combinational ALU — tie clk to 0 or use TB clk
    .a        (a),
    .b        (b),
    .result   (result),
    .alu_ctrl (alu_ctrl)
);
```

`bind` keeps assertions separate from the synthesisable RTL — same approach used in industry checker libraries.

---

## Complete SVA Example — AXI-Lite Write Channel

This shows SVA applied to a real protocol snippet (AXI-Lite write address channel):

```systemverilog
module axi_lite_assertions (
    input logic        clk, rst_n,
    input logic        awvalid, awready,
    input logic        wvalid,  wready,
    input logic        bvalid,  bready
);

    // Once AWVALID asserts, it must not deassert until AWREADY
    property p_awvalid_stable;
        @(posedge clk) disable iff (!rst_n)
        $rose(awvalid) |->
            awvalid throughout (##[1:$] awready);
    endproperty
    p_awvalid_stable_chk: assert property (p_awvalid_stable)
        else $error("AWVALID dropped before AWREADY");

    // After write address accepted (AWVALID && AWREADY), 
    // write data must arrive within 16 cycles
    property p_wdata_follows_awaddr;
        @(posedge clk) disable iff (!rst_n)
        (awvalid && awready) |-> ##[0:16] (wvalid && wready);
    endproperty
    p_wdata_chk: assert property (p_wdata_follows_awaddr)
        else $error("Write data did not follow address within 16 cycles");

    // Write response must follow write data within 4 cycles
    property p_bresp_follows_wdata;
        @(posedge clk) disable iff (!rst_n)
        (wvalid && wready) |-> ##[1:4] bvalid;
    endproperty
    p_bresp_chk: assert property (p_bresp_follows_wdata)
        else $error("BVALID did not appear within 4 cycles of WVALID+WREADY");

    // Coverage: both channels accept in same cycle (zero-latency path)
    cov_simultaneous: cover property (
        @(posedge clk) (awvalid && awready) && (wvalid && wready));

endmodule
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using immediate assertion for multi-cycle check | Use concurrent assertion with `##n` |
| Forgetting `disable iff (rst)` | Add it — avoids hundreds of false failures at reset |
| Using `\|->` when you mean "next cycle" | Use `\|=>` (or `\|-> ##1`) |
| `$rose(sig)` fires on X→1 | Guard with `!$isunknown(sig)` if needed |
| Assertion clock mismatch with design | Ensure `@(posedge clk)` matches DUT clock domain |
| No cover properties | Add `cover property` for every major handshake scenario |

---

## Running SVA in Simulation

Assertions are compiled alongside RTL in any SystemVerilog simulator:

```bash
# Icarus Verilog (basic SVA subset)
iverilog -g2012 -o sim dut.sv assertions.sv tb.sv && ./sim

# Cadence Xcelium
xrun -sv dut.sv assertions.sv tb.sv

# Synopsys VCS
vcs -sverilog dut.sv assertions.sv tb.sv -o sim && ./sim

# Check assertion results
grep "ASSERT\|FATAL\|ERROR" simulation.log | sort | uniq -c
```

For **formal verification** (exhaustive, no testbench needed):
```tcl
# JasperGold / VC Formal — read RTL and prove all properties
read_file -type sv [list dut.sv assertions.sv]
compile -d dut
prove -property {a_req_ack p_awvalid_stable_chk}
```

---

## What's Next

- **[UVM Testbench from Scratch]({{ '/blog/2026/05/13/uvm-testbench-from-scratch/' | relative_url }})** — build a full UVM environment with driver, monitor, and scoreboard
- **[Functional Coverage in SystemVerilog]({{ '/blog/2026/05/13/functional-coverage-systemverilog/' | relative_url }})** — covergroups and coverpoints to measure what your tests exercise
- **[cocotb Python Verification]({{ '/blog/2026/05/13/cocotb-python-rtl-verification-tutorial/' | relative_url }})** — write testbenches in Python instead of SystemVerilog
