---
layout: post
title: "Functional Coverage in SystemVerilog — Complete Guide with Examples"
description: "Master SystemVerilog functional coverage: covergroups, coverpoints, bins, cross coverage, transition coverage, and integrating coverage into UVM — with verified ALU examples and coverage closure tips."
date: 2026-05-13
category: Verification
tags: [coverage, systemverilog, uvm, verification, covergroup, coverpoint, bins, functional-coverage, beginner]
---

Running a testbench for hours means nothing if it never exercises the corner cases that matter. **Functional coverage** is the mechanism that answers: *"What have my tests actually exercised?"* This guide covers every SystemVerilog coverage construct, from basic coverpoints to cross-coverage and UVM integration, using our ALU as the running example.

---

## Code Coverage vs Functional Coverage

These are often confused:

| | Code Coverage | Functional Coverage |
|--|--------------|---------------------|
| What it measures | Which lines/branches of RTL were executed | Which *meaningful scenarios* were exercised |
| Who defines it | Simulator (automatic) | Verification engineer (intentional) |
| Can miss bugs? | Yes — wrong code can be fully covered | Yes — but *you* decide what matters |
| Example gap | 95% line coverage, never tested overflow | 0 hits on `overflow_bin` → clearly untested |
| Tool | `vcs -cm line+branch` | `covergroup` in SystemVerilog |

**Both are needed.** Code coverage finds dead code; functional coverage ensures your specification is exercised.

---

## Covergroup Basics

```systemverilog
// Standalone covergroup — instantiated manually
covergroup alu_cg;
    cp_ctrl: coverpoint alu_ctrl {
        bins add  = {0};
        bins sub  = {1};
        bins and_ = {2};
        bins or_  = {3};
        bins xor_ = {4};
        bins slt  = {5};
        bins illegal = {[6:15]};
    }
endgroup

// Instantiate and sample
alu_cg cg = new();

always @(posedge clk) begin
    cg.sample();    // sample all coverpoints at this moment
end
```

After simulation, the simulator reports hit percentages per bin.

---

## Coverpoints — Sampling One Variable

A **coverpoint** defines which values of a signal you care about:

```systemverilog
covergroup alu_full_cg @(posedge clk);  // sample on rising clock edge

    // Simple value bins
    cp_ctrl: coverpoint alu_ctrl {
        bins add  = {4'd0};
        bins sub  = {4'd1};
        bins bitwise = {4'd2, 4'd3, 4'd4};  // AND, OR, XOR in one bin
        bins slt  = {4'd5};
        bins other = default;               // everything not listed above
    }

    // Range bins
    cp_a: coverpoint a {
        bins zero     = {32'd0};
        bins small    = {[32'd1 : 32'd127]};
        bins positive = {[32'd128 : 32'h7FFF_FFFF]};
        bins neg_msb  = {[32'h8000_0000 : 32'hFFFF_FFFE]};
        bins all_ones = {32'hFFFF_FFFF};
    }

    // Auto-bins: simulator creates N equally-spaced bins automatically
    cp_b_auto: coverpoint b {
        // Creates 8 auto-bins spanning the full [0:2^32-1] range
        option.auto_bin_max = 8;
    }

endgroup
```

---

## Transition Coverage

Track sequences of values — useful for protocol state machines:

```systemverilog
covergroup ctrl_transition_cg @(posedge clk);
    cp_ctrl_trans: coverpoint alu_ctrl {
        // ADD followed by SUB
        bins add_then_sub  = (4'd0 => 4'd1);

        // ADD or SUB followed by any bitwise op
        bins arith_to_bits = (4'd0, 4'd1 => 4'd2, 4'd3, 4'd4);

        // Three-step sequence
        bins add_sub_slt   = (4'd0 => 4'd1 => 4'd5);
    }
endgroup
```

---

## Cross Coverage — Combining Two Coverpoints

Cross coverage measures combinations of values across multiple signals. This catches *interaction bugs* that individual coverpoints miss:

```systemverilog
covergroup alu_cross_cg @(posedge clk);

    cp_ctrl: coverpoint alu_ctrl {
        bins add = {4'd0}; bins sub = {4'd1}; bins slt = {4'd5};
    }

    cp_a_sign: coverpoint a[31] {   // MSB = sign bit
        bins positive = {1'b0};
        bins negative = {1'b1};
    }

    cp_b_sign: coverpoint b[31] {
        bins positive = {1'b0};
        bins negative = {1'b1};
    }

    // Cross: every combination of ctrl × a_sign × b_sign
    // 3 ctrl bins × 2 a-sign bins × 2 b-sign bins = 12 cross bins
    cx_ctrl_signs: cross cp_ctrl, cp_a_sign, cp_b_sign;

    // Cross with ignored bins
    cx_add_operands: cross cp_ctrl, cp_a_sign {
        // Don't care about non-ADD with negative
        ignore_bins non_add_neg = binsof(cp_ctrl) intersect {4'd1, 4'd5}
                                  && binsof(cp_a_sign.negative);
    }

endgroup
```

---

## Covergroup Options

```systemverilog
covergroup alu_cg @(posedge clk);
    option.per_instance  = 1;   // separate stats per instance (not merged)
    option.goal          = 90;  // declare "closed" at 90% (not 100%)
    option.comment       = "ALU operation coverage";

    cp_ctrl: coverpoint alu_ctrl {
        option.at_least = 5;    // each bin needs ≥5 hits to be "covered"
    }
endgroup
```

---

## Embedded Covergroup in a Class

For UVM, embed the covergroup inside a class so it travels with the object:

```systemverilog
class alu_coverage extends uvm_subscriber #(alu_seq_item);
    `uvm_component_utils(alu_coverage)

    alu_seq_item item;

    covergroup alu_op_cg;
        cp_ctrl: coverpoint item.alu_ctrl {
            bins add  = {4'd0};
            bins sub  = {4'd1};
            bins and_ = {4'd2};
            bins or_  = {4'd3};
            bins xor_ = {4'd4};
            bins slt  = {4'd5};
        }

        cp_a_zero: coverpoint (item.a == 0) {
            bins zero     = {1};
            bins non_zero = {0};
        }

        cp_b_zero: coverpoint (item.b == 0) {
            bins zero     = {1};
            bins non_zero = {0};
        }

        cp_result_zero: coverpoint item.zero {
            bins is_zero  = {1};
            bins not_zero = {0};
        }

        // Cross: each operation with zero and non-zero operands
        cx_op_a: cross cp_ctrl, cp_a_zero;
        cx_op_b: cross cp_ctrl, cp_b_zero;

    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        alu_op_cg = new();    // instantiate covergroup
    endfunction

    // Called by monitor's analysis port
    function void write(alu_seq_item t);
        item = t;
        alu_op_cg.sample();   // sample every time a transaction arrives
    endfunction
endclass
```

### Wiring the Coverage Collector into UVM Environment

```systemverilog
// In alu_env.sv — add coverage alongside scoreboard
class alu_env extends uvm_env;
    alu_agent      agent;
    alu_scoreboard scoreboard;
    alu_coverage   coverage;   // ← add this

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        agent      = alu_agent     ::type_id::create("agent",      this);
        scoreboard = alu_scoreboard::type_id::create("scoreboard", this);
        coverage   = alu_coverage  ::type_id::create("coverage",   this); // ← add
    endfunction

    function void connect_phase(uvm_phase phase);
        agent.ap.connect(scoreboard.analysis_export);
        agent.ap.connect(coverage.analysis_export);  // ← connect
    endfunction
endclass
```

The monitor's analysis port now fans out to *both* the scoreboard and the coverage collector — no code changes to either component.

---

## Querying Coverage Programmatically

```systemverilog
// Get overall coverage percentage
real cov_pct;
cov_pct = alu_op_cg.get_coverage();
`uvm_info("COV", $sformatf("Overall ALU coverage: %.1f%%", cov_pct), UVM_NONE)

// Get per-coverpoint coverage
real ctrl_cov = alu_op_cg.cp_ctrl.get_coverage();

// Simulation-end report in report_phase
function void report_phase(uvm_phase phase);
    real cov = alu_op_cg.get_coverage();
    `uvm_info("COV", $sformatf("Final coverage: %.1f%%", cov), UVM_NONE)
    if (cov < 90.0)
        `uvm_warning("COV", "Coverage below 90% — add more tests")
endfunction
```

---

## Coverage-Driven Verification — The Loop

The goal of functional coverage is to *close* it — drive it to 100% (or your target) before signoff:

```
1. Write covergroups  →  define what matters
2. Run random tests   →  collect coverage
3. Check report       →  find uncovered bins
4. Add directed tests →  target uncovered corners
5. Repeat             →  until coverage is closed
```

```systemverilog
// Example: after random tests, SLT with negative operands isn't hit
// Add a directed sequence targeting that cross bin:
class alu_slt_neg_seq extends uvm_sequence #(alu_seq_item);
    `uvm_object_utils(alu_slt_neg_seq)

    task body();
        alu_seq_item item;
        repeat (10) begin
            item = alu_seq_item::type_id::create("slt_neg");
            start_item(item);
            item.alu_ctrl = 4'd5;             // SLT
            item.a        = $urandom_range(32'h80000000, 32'hFFFFFFFF);  // negative
            item.b        = $urandom_range(32'h00000001, 32'h7FFFFFFF);  // positive
            finish_item(item);
        end
    endtask
endclass
```

---

## Full ALU Covergroup — All Corner Cases

This is what a production-quality coverage plan looks like for a 32-bit ALU:

```systemverilog
covergroup alu_full_coverage_cg @(posedge clk);
    option.comment = "Full ALU functional coverage";

    //-- Operation type
    cp_op: coverpoint alu_ctrl {
        bins add     = {4'd0};
        bins sub     = {4'd1};
        bins and_op  = {4'd2};
        bins or_op   = {4'd3};
        bins xor_op  = {4'd4};
        bins slt_op  = {4'd5};
        bins illegal = default;
    }

    //-- Operand A sign
    cp_a_sign: coverpoint a[31] {
        bins pos = {0}; bins neg = {1};
    }

    //-- Operand B sign
    cp_b_sign: coverpoint b[31] {
        bins pos = {0}; bins neg = {1};
    }

    //-- Operand A special values
    cp_a_special: coverpoint a {
        bins zero     = {32'd0};
        bins all_ones = {32'hFFFFFFFF};
        bins msb_only = {32'h80000000};
        bins lsb_only = {32'h00000001};
        bins others   = default;
    }

    //-- Result special values
    cp_result_zero: coverpoint zero {
        bins is_zero  = {1};
        bins not_zero = {0};
    }

    //-- 32-bit ADD overflow: 0xFFFFFFFF + n (wraps to 0)
    cp_add_overflow: coverpoint (alu_ctrl == 4'd0 && a == 32'hFFFFFFFF) {
        bins overflow     = {1};
        bins no_overflow  = {0};
    }

    //-- SUB underflow: smaller - larger = negative
    cp_sub_neg: coverpoint (alu_ctrl == 4'd1 && $signed(a) < $signed(b)) {
        bins underflow    = {1};
        bins no_underflow = {0};
    }

    //-- SLT: signed negative < positive  (key corner case)
    cp_slt_neg_pos: coverpoint
        (alu_ctrl == 4'd5 && a[31] && !b[31]) {
        bins neg_lt_pos = {1};
        bins others     = {0};
    }

    //-- Cross: every op with every sign combination
    cx_op_signs: cross cp_op, cp_a_sign, cp_b_sign {
        // Illegal ops don't need sign coverage
        ignore_bins illegal_x = binsof(cp_op.illegal);
    }

endgroup
```

---

## Reading the Coverage Report

After simulation, open the coverage database:

```bash
# Cadence Xcelium — open coverage GUI
imc -load cov_work/scope/snaps/default

# VCS — generate HTML report
urg -dir simv.vdb -report coverage_report

# ModelSim/Questa
vsim -c -coverage -do "coverage report -detail; quit"
```

A typical HTML report shows:

```
Covergroup        | Coverage | Bins Hit | Total Bins
------------------|----------|----------|------------
alu_full_cg       |  87.5%   |   21     |    24
  cp_op           | 100.0%   |    7     |     7
  cp_a_sign       | 100.0%   |    2     |     2
  cp_slt_neg_pos  |   0.0%   |    0     |     1   ← NOT HIT
  cx_op_signs     |  83.3%   |   20     |    24
```

Zero-hit bins point directly to the next test you should write.

---

## Assertion Coverage vs Functional Coverage

| | `cover property` (SVA) | `covergroup` |
|--|------------------------|--------------|
| What it tracks | Did a temporal sequence happen? | Did a signal take a value? |
| Granularity | Event/sequence in time | Point-in-time value |
| Formal tools | Yes | No |
| Example | "Was there ever a burst of 4 valid beats?" | "Was alu_ctrl ever 0 AND a was 0?" |

Use both: SVA cover properties for temporal/protocol coverage, covergroups for data-value coverage.

```systemverilog
// SVA: cover the scenario where result overflows to zero
cover property (@(posedge clk)
    (alu_ctrl == 4'd0 && a == 32'hFFFFFFFF) |=> (result == 32'd0));

// Covergroup: cover all operations with max input values
cp_a_max: coverpoint (a == 32'hFFFFFFFF) { bins max = {1}; bins other = {0}; }
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Sampling before signals settle | Use `@(posedge clk)` in covergroup, not `@*` |
| No `bins` defined | Simulator uses auto-bins — add explicit bins for meaningful coverage |
| `default` bin not added | Unconstrained values silently lumped together — add `bins illegal = default` |
| Coverage always 100% | Check that `sample()` is actually called / covergroup clock event fires |
| Cross coverage explosion | Large crosses create N×M bins — ignore meaningless combinations with `ignore_bins` |
| Forgetting `option.per_instance = 1` | Multiple instances share one count — hide bugs where only one instance was exercised |

---

## Coverage Closure Checklist

Before tape-out, verify:

- [ ] All explicit bins have ≥ `option.at_least` hits (typically 5–10)
- [ ] All cross-coverage bins hit (or explicitly `ignore_bins`)
- [ ] Transition coverage for all state-machine arcs
- [ ] Zero-bin report reviewed — all zeros are either intentional ignores or new tests
- [ ] Code coverage ≥ 95% (line + branch + toggle)
- [ ] SVA cover properties all have non-zero hit counts
- [ ] Directed tests written and reviewed for every manually excluded bin

---

## What's Next

- **[SystemVerilog Assertions (SVA)]({{ site.baseurl }}{% post_url 2026-05-13-systemverilog-assertions-sva-guide %})** — add `cover property` directives alongside your covergroups
- **[UVM Testbench from Scratch]({{ site.baseurl }}{% post_url 2026-05-13-uvm-testbench-from-scratch %})** — build the environment this coverage collector plugs into
- **[cocotb Python Verification]({{ site.baseurl }}{% post_url 2026-05-13-cocotb-python-rtl-verification-tutorial %})** — lightweight Python alternative with `hypothesis` for property-based testing
