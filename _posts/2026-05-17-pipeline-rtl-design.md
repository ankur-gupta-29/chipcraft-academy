---
layout: post
title: "Pipelining in RTL Design — Build & Verify a 4-Stage Pipeline in Verilog"
description: "Master RTL pipelining: why pipeline, data hazards, stall logic, forwarding, a complete 4-stage ALU pipeline in Verilog, and a cocotb testbench to verify it — with timing diagrams."
date: 2026-05-17
category: RTL Design
tags: [pipeline, verilog, rtl, hazard, stall, forwarding, cocotb, synthesis, beginner]
---

A 50 MHz design can often become 200 MHz just by adding pipeline registers — without changing any logic. Pipelining is the single most powerful RTL throughput technique. This guide builds a complete 4-stage ALU pipeline in Verilog, covers all three hazard types, and includes a verified cocotb testbench.

---

## Why Pipeline?

The critical path (longest combinational delay) limits clock frequency. Pipelining cuts the critical path by inserting flip-flops mid-way, creating shorter stages that each run faster.

```
Without pipeline — 40 ns critical path → 25 MHz max:
  Input → [Stage A 15ns] → [Stage B 15ns] → [Stage C 10ns] → Output
                                 40 ns total

With 3-stage pipeline — 15 ns per stage → 66 MHz max:
  Input → [FF] → [Stage A 15ns] → [FF] → [Stage B 15ns] → [FF] → [Stage C 10ns] → [FF] → Output
                  Stage 1                  Stage 2                  Stage 3
  Throughput: 1 result per cycle (after 3-cycle latency)
```

**Trade-off:** Latency increases (3 cycles to first result), but throughput increases (1 result per cycle after that).

---

## 4-Stage ALU Pipeline

Our pipeline:

| Stage | Name | What happens |
|-------|------|-------------|
| 1 | **IF** (Instruction Fetch) | Latch opcode, operands A and B |
| 2 | **DE** (Decode/Register) | Decode opcode, select operation |
| 3 | **EX** (Execute) | Perform the ALU operation |
| 4 | **WB** (Write-Back) | Output result, update valid flag |

```
Cycle:     1    2    3    4    5    6
Instr 1:  [IF] [DE] [EX] [WB]
Instr 2:       [IF] [DE] [EX] [WB]
Instr 3:            [IF] [DE] [EX] [WB]
```

Full throughput from cycle 4 onward: one result per cycle.

---

## Complete Pipeline Verilog

```verilog
// pipeline_alu.v — 4-stage pipelined ALU
module pipeline_alu #(
    parameter DATA_W = 32,
    parameter CTRL_W = 4
)(
    input  wire                clk, rst_n,
    // Stage 1 inputs
    input  wire [DATA_W-1:0]   s1_a, s1_b,
    input  wire [CTRL_W-1:0]   s1_ctrl,
    input  wire                s1_valid,
    // Stage 4 outputs
    output reg  [DATA_W-1:0]   wb_result,
    output reg                 wb_zero,
    output reg                 wb_valid
);

    // ── Stage pipeline registers ─────────────────────────────────
    // Stage 1→2 (IF→DE)
    reg [DATA_W-1:0] s2_a, s2_b;
    reg [CTRL_W-1:0] s2_ctrl;
    reg              s2_valid;

    // Stage 2→3 (DE→EX)
    reg [DATA_W-1:0] s3_a, s3_b;
    reg [CTRL_W-1:0] s3_ctrl;
    reg              s3_valid;

    // Stage 3→4 (EX→WB)
    reg [DATA_W-1:0] s4_result;
    reg              s4_zero, s4_valid;

    // ── Stage 1→2 register (IF stage latch) ─────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s2_a <= 0; s2_b <= 0; s2_ctrl <= 0; s2_valid <= 0;
        end else begin
            s2_a     <= s1_a;
            s2_b     <= s1_b;
            s2_ctrl  <= s1_ctrl;
            s2_valid <= s1_valid;
        end
    end

    // ── Stage 2→3 register (DE stage — decode happens here) ─────
    reg [DATA_W-1:0] de_a, de_b;
    reg [CTRL_W-1:0] de_ctrl;

    always @(*) begin
        // Decode: pass-through for simple ALU, but here you'd
        // do immediate sign-extension, register file read, etc.
        de_a    = s2_a;
        de_b    = s2_b;
        de_ctrl = s2_ctrl;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s3_a <= 0; s3_b <= 0; s3_ctrl <= 0; s3_valid <= 0;
        end else begin
            s3_a     <= de_a;
            s3_b     <= de_b;
            s3_ctrl  <= de_ctrl;
            s3_valid <= s2_valid;
        end
    end

    // ── Stage 3 (EX) — ALU operation ────────────────────────────
    reg [DATA_W-1:0] ex_result;
    reg              ex_zero;

    always @(*) begin
        ex_result = '0;
        case (s3_ctrl)
            4'd0: ex_result = s3_a + s3_b;                                  // ADD
            4'd1: ex_result = s3_a - s3_b;                                  // SUB
            4'd2: ex_result = s3_a & s3_b;                                  // AND
            4'd3: ex_result = s3_a | s3_b;                                  // OR
            4'd4: ex_result = s3_a ^ s3_b;                                  // XOR
            4'd5: ex_result = ($signed(s3_a) < $signed(s3_b)) ? 32'd1 : 0; // SLT
            default: ex_result = '0;
        endcase
        ex_zero = (ex_result == '0);
    end

    // ── Stage 3→4 register (EX→WB) ──────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s4_result <= 0; s4_zero <= 0; s4_valid <= 0;
        end else begin
            s4_result <= ex_result;
            s4_zero   <= ex_zero;
            s4_valid  <= s3_valid;
        end
    end

    // ── Stage 4 (WB) — write-back ───────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wb_result <= 0; wb_zero <= 0; wb_valid <= 0;
        end else begin
            wb_result <= s4_result;
            wb_zero   <= s4_zero;
            wb_valid  <= s4_valid;
        end
    end

endmodule
```

---

## The Three Hazard Types

### 1. Structural Hazard
Two instructions need the **same hardware resource** in the same cycle. Solution: replicate resources or stall.

### 2. Data Hazard — RAW (Read After Write)

Instruction 2 reads a result that instruction 1 hasn't written yet:

```
Cycle:    1    2    3    4    5
ADD r1←a+b:  [IF] [DE] [EX] [WB]
SUB r2←r1-c:      [IF] [DE] [EX]  ← r1 not ready until WB of ADD!
```

**Solution A — Stall (insert bubbles):**

```verilog
// Stall controller — freeze stages when hazard detected
always @(*) begin
    stall = (s2_valid && s3_valid &&
             s2_rd == s3_rs);   // dest of stage3 == src of stage2
end

// Stall pipeline registers
always @(posedge clk) begin
    if (!stall) begin
        s3_a     <= de_a;
        s3_b     <= de_b;
        s3_valid <= s2_valid;
    end else begin
        s3_valid <= 0;    // insert bubble (NOP)
    end
end
```

**Solution B — Forwarding (bypass):**
Forward the EX result directly to the EX stage input — no stall needed:

```verilog
// Forwarding mux for operand A
always @(*) begin
    // Forward from EX stage if destination matches
    if (s3_valid && s3_rd == s2_rs1)
        fwd_a = ex_result;   // forward from EX output
    // Forward from WB stage
    else if (s4_valid && s4_rd == s2_rs1)
        fwd_a = wb_result;   // forward from WB output
    else
        fwd_a = s3_a;        // no hazard, use register value
end
```

### 3. Control Hazard — Branch

When a branch instruction is in EX, the PC decision is made 2 cycles after fetch. In the meantime, 2 wrong instructions have been fetched.

**Solution — Flush (kill wrong instructions):**

```verilog
// Flush stages 1 and 2 when branch resolves
always @(posedge clk) begin
    if (branch_taken) begin
        s2_valid <= 0;   // kill IF stage
        s3_valid <= 0;   // kill DE stage
    end
end
```

---

## Stall + Bubble Example

```verilog
// pipeline_alu_stall.v — adds hazard detection
module pipeline_alu_stall (
    input  wire        clk, rst_n,
    input  wire [31:0] s1_a, s1_b,
    input  wire [3:0]  s1_ctrl,
    input  wire [4:0]  s1_rd, s1_rs1, s1_rs2,  // register indices
    input  wire        s1_valid,
    output reg  [31:0] wb_result,
    output reg         wb_valid
);
    // ... (pipeline registers as before) ...

    // Hazard detection
    wire raw_hazard = s3_valid && s2_valid &&
                     (s3_rd != 0) &&
                     ((s3_rd == s2_rs1) || (s3_rd == s2_rs2));

    // Stall control
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s3_valid <= 0;
        end else if (raw_hazard) begin
            // Freeze s2, inject bubble into s3
            s3_valid <= 0;       // bubble
            // s2 registers hold (don't update) — achieved by not
            // writing them this cycle (use enable signal in practice)
        end else begin
            s3_valid <= s2_valid;
            // ... normal pipeline advance
        end
    end
endmodule
```

---

## cocotb Testbench

```python
# test_pipeline.py — verify 4-cycle latency and throughput
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

PIPELINE_DEPTH = 4

@cocotb.test()
async def test_pipeline_latency(dut):
    """First result appears exactly PIPELINE_DEPTH cycles after input."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value  = 0
    dut.s1_valid.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value  = 1
    await RisingEdge(dut.clk)

    # Drive ADD(10, 20) = 30
    dut.s1_a.value    = 10
    dut.s1_b.value    = 20
    dut.s1_ctrl.value = 0      # ADD
    dut.s1_valid.value = 1
    await RisingEdge(dut.clk)
    dut.s1_valid.value = 0     # only one instruction

    # Wait PIPELINE_DEPTH cycles for result
    await ClockCycles(dut.clk, PIPELINE_DEPTH)

    assert int(dut.wb_valid.value) == 1, "wb_valid not set"
    assert int(dut.wb_result.value) == 30, \
        f"Expected 30, got {int(dut.wb_result.value)}"

@cocotb.test()
async def test_pipeline_throughput(dut):
    """Back-to-back instructions produce results every cycle."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Send 4 ADD instructions back-to-back
    ops = [(1, 2), (3, 4), (5, 6), (7, 8)]
    for a, b in ops:
        dut.s1_a.value     = a
        dut.s1_b.value     = b
        dut.s1_ctrl.value  = 0
        dut.s1_valid.value = 1
        await RisingEdge(dut.clk)

    dut.s1_valid.value = 0

    # Collect 4 results — one per cycle
    expected = [a + b for a, b in ops]
    results  = []
    for _ in range(PIPELINE_DEPTH + len(ops)):
        await RisingEdge(dut.clk)
        if int(dut.wb_valid.value):
            results.append(int(dut.wb_result.value))

    assert results == expected, f"Expected {expected}, got {results}"
```

---

## Pipeline Design Rules

| Rule | Reason |
|------|--------|
| Every path between pipeline registers must meet Tclk | STA ensures this |
| All control signals travel with the data | Keep opcode, valid bit alongside operands |
| Default `valid=0` on reset | Prevent spurious outputs at startup |
| Flush on reset | Reset valid bits in all stages |
| Never skip a stage | Every stage must register its inputs |
| Balance stage delays | Unbalanced stages waste clock margin |

---

## What's Next

- **[SystemVerilog vs Verilog]({{ site.baseurl }}{% post_url 2026-05-17-systemverilog-vs-verilog %})** — use `always_ff` and `always_comb` for cleaner pipeline stage coding
- **[Setup & Hold Time — STA]({{ site.baseurl }}{% post_url 2026-05-17-setup-hold-time-sta %})** — understand why each pipeline stage must meet timing
- **[FSM Design in Verilog]({{ site.baseurl }}{% post_url 2026-05-17-fsm-design-verilog %})** — combine FSM state machines with pipelines for control logic
