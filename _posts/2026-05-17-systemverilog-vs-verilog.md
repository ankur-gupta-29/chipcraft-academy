---
layout: post
title: "SystemVerilog vs Verilog — What's New and Why It Matters for RTL"
description: "A complete comparison of SystemVerilog vs Verilog for RTL design: the logic type, always_comb/always_ff, interfaces, packages, typedef enum, structs — and what's synthesis-safe vs simulation-only."
date: 2026-05-17
category: RTL Design
tags: [systemverilog, verilog, rtl, synthesis, logic, interface, package, typedef, enum, beginner]
---

If you learned Verilog first, SystemVerilog looks like Verilog with extra syntax sprinkled on top — and mostly, that's exactly what it is. SystemVerilog (IEEE 1800-2017) is a **strict superset** of Verilog (IEEE 1364-2005): any valid Verilog file is also valid SystemVerilog. But the additions make RTL code cleaner, safer, and easier to verify. This guide covers what matters for RTL synthesis.

---

## Why Upgrade from Verilog to SystemVerilog?

```verilog
// ❌ Verilog — confusing reg/wire split, no intent expressed
module alu (
    input  wire [31:0] a, b,
    input  wire [3:0]  alu_ctrl,
    output reg  [31:0] result   // reg doesn't mean register!
);
    always @(*) result = a + b;
endmodule
```

```systemverilog
// ✓ SystemVerilog — clearer intent, one type, better tool checking
module alu (
    input  logic [31:0] a, b,
    input  logic [3:0]  alu_ctrl,
    output logic [31:0] result
);
    always_comb result = a + b;
endmodule
```

---

## 1. `logic` — One Type to Rule Them All

In Verilog, you must choose `reg` or `wire` based on confusing rules (driven by `always` → `reg`; driven by `assign` or module output → `wire`). In SystemVerilog, `logic` works for both:

```verilog
// Verilog — two types with confusing rules
wire [7:0] bus_in;          // driven by assign or module port
reg  [7:0] data_reg;        // driven by always block
wire [7:0] data_out = ...;  // continuous assignment output
reg  [7:0] combo;           // but this is also combinational!
```

```systemverilog
// SystemVerilog — logic works everywhere
logic [7:0] bus_in;
logic [7:0] data_reg;
logic [7:0] data_out;
logic [7:0] combo;

assign data_out = bus_in;       // ✓ logic works here
always_comb combo = bus_in + 1; // ✓ and here
always_ff @(posedge clk)
    data_reg <= bus_in;         // ✓ and here too
```

> **Exception:** `wire` is still needed for multi-driver nets (tri-state buses, wired-OR). `logic` only allows one driver.

---

## 2. `always_comb`, `always_ff`, `always_latch`

These replacements for `always @(...)` add **tool-enforced intent checks**:

```verilog
// Verilog — no intent check
always @(posedge clk)           // is this really an FF? tool doesn't know
    data <= in;

always @(*)                     // missing a signal? tool won't always catch it
    out = a & b;
```

```systemverilog
// SystemVerilog — tool verifies intent

// always_ff: tool errors if it doesn't infer flip-flops
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 0;
    else        q <= d;
end

// always_comb: tool verifies purely combinational (no latches)
// automatically includes all inputs in sensitivity list
always_comb begin
    y = a & b & c;   // if you forget c in @(*), tool may not warn
end

// always_latch: tool verifies a latch is intended
always_latch begin
    if (en) q = d;
end
```

| Keyword | What tool checks |
|---------|-----------------|
| `always_ff` | Contains only sequential (FF) logic; has a clock edge |
| `always_comb` | Purely combinational; no latches; full sensitivity |
| `always_latch` | Level-sensitive latch; en signal controls latch |

---

## 3. `typedef` and `enum` — Named State Machines

Old Verilog state machines use parameters, which are just integers with no type safety:

```verilog
// Verilog — fragile parameter approach
parameter IDLE   = 2'b00,
          ACTIVE = 2'b01,
          DONE   = 2'b10,
          ERROR  = 2'b11;

reg [1:0] state;
always @(posedge clk)
    state <= IDLE;      // no type check: you could write state <= 4'b1111
```

```systemverilog
// SystemVerilog — enum with type safety
typedef enum logic [1:0] {
    IDLE   = 2'b00,
    ACTIVE = 2'b01,
    DONE   = 2'b10,
    ERROR  = 2'b11
} state_t;

state_t state, next_state;   // type-safe: can only hold enum values

always_ff @(posedge clk or posedge rst) begin
    if (rst) state <= IDLE;
    else     state <= next_state;
end

always_comb begin
    next_state = IDLE;
    unique case (state)    // 'unique' warns if overlap or gap
        IDLE:   next_state = req ? ACTIVE : IDLE;
        ACTIVE: next_state = DONE;
        DONE:   next_state = IDLE;
        ERROR:  next_state = IDLE;
    endcase
end
```

> **`unique case`** is SV's replacement for `full_case parallel_case` pragmas — it's part of the language standard and has defined simulation and synthesis semantics.

---

## 4. `struct` — Group Related Signals

```systemverilog
// Pack an AXI-Lite address channel into a struct
typedef struct packed {
    logic [31:0] addr;
    logic [2:0]  prot;
    logic        valid;
    logic        ready;
} axi_aw_t;

// Use it in a module port
module axi_master (
    output axi_aw_t aw_chan,
    ...
);
    always_comb begin
        aw_chan.addr  = target_addr;
        aw_chan.valid = 1'b1;
        aw_chan.prot  = 3'b000;
    end
endmodule
```

`packed` struct: all bits are adjacent in memory → can treat the whole struct as a bit vector. **Synthesisable.** Use `unpacked` structs only in testbenches.

---

## 5. Interfaces — Bundle Signals Between Modules

Without interfaces, connecting an ALU to a testbench requires listing every port in every module. Interfaces bundle the signals:

```systemverilog
// alu_if.sv — define the interface once
interface alu_if (input logic clk);
    logic [31:0] a, b, result;
    logic [3:0]  alu_ctrl;
    logic        zero;

    // modport: defines which direction each module drives
    modport dut_mp  (input a, b, alu_ctrl, output result, zero);
    modport tb_mp   (output a, b, alu_ctrl, input result, zero);
endinterface

// alu.sv — uses the interface
module alu (alu_if.dut_mp port);
    always_comb begin
        case (port.alu_ctrl)
            4'd0: port.result = port.a + port.b;
            4'd1: port.result = port.a - port.b;
            default: port.result = '0;
        endcase
    end
    assign port.zero = (port.result == '0);
endmodule

// tb_top.sv — connect everything
module tb_top;
    logic clk;
    alu_if dut_if(.clk(clk));     // one line instead of 5 ports
    alu dut(.port(dut_if.dut_mp));
endmodule
```

---

## 6. `package` — Share Types Across Files

```systemverilog
// alu_pkg.sv — define once, import everywhere
package alu_pkg;

    // ALU operations
    typedef enum logic [3:0] {
        ALU_ADD  = 4'd0,
        ALU_SUB  = 4'd1,
        ALU_AND  = 4'd2,
        ALU_OR   = 4'd3,
        ALU_XOR  = 4'd4,
        ALU_SLT  = 4'd5
    } alu_op_t;

    // Bus widths
    parameter DATA_W = 32;
    parameter CTRL_W = 4;

    // Helper function
    function automatic logic is_arithmetic(alu_op_t op);
        return (op == ALU_ADD || op == ALU_SUB);
    endfunction

endpackage

// alu.sv — import the package
import alu_pkg::*;

module alu (
    input  logic [DATA_W-1:0] a, b,
    input  alu_op_t           alu_ctrl,
    output logic [DATA_W-1:0] result
);
    always_comb begin
        unique case (alu_ctrl)
            ALU_ADD: result = a + b;
            ALU_SUB: result = a - b;
            ALU_AND: result = a & b;
            ALU_OR:  result = a | b;
            ALU_XOR: result = a ^ b;
            ALU_SLT: result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            default: result = '0;
        endcase
    end
endmodule
```

---

## 7. `parameter` vs `localparam` vs `const`

| Keyword | Scope | Overridable from outside? | Use for |
|---------|-------|--------------------------|---------|
| `parameter` | Module | Yes (at instantiation) | Bus width, depth |
| `localparam` | Module | No | Internal constants |
| `const` (SV) | Always block / task | No | Compile-time constants in tasks |

```systemverilog
module fifo #(
    parameter  int DATA_W = 8,    // overridable width
    parameter  int DEPTH  = 16    // overridable depth
) (
    ...
);
    localparam int ADDR_W = $clog2(DEPTH);  // derived — not overridable
    const  logic [DATA_W-1:0] RESET_VAL = '0;
endmodule
```

---

## 8. Useful SV System Functions for RTL

| Function | Returns | Example |
|----------|---------|---------|
| `$clog2(N)` | Ceiling log2 — for address width | `$clog2(256)` → 8 |
| `$bits(T)` | Bit width of type T | `$bits(axi_aw_t)` → 36 |
| `$size(arr)` | Number of elements in array | `$size(mem)` |
| `$signed(x)` | Treat x as signed | `$signed(a) < $signed(b)` |
| `'0`, `'1`, `'x`, `'z` | Fill all bits with value | `result = '0` → 32'b0...0 |

---

## 9. What Is Synthesis-Safe vs Simulation-Only

**Synthesis-safe SystemVerilog** (use in RTL):

- `logic`, `wire`, `reg`
- `always_ff`, `always_comb`, `always_latch`
- `typedef enum`, `typedef struct packed`
- `package`, `import`
- `interface` and `modport`
- `unique case`, `priority case`
- `$clog2`, `$bits`, `$size`, `$signed`
- `generate if/for`

**Simulation-only** (testbench / UVM only, NOT synthesisable):

- `class`, `extends` (OOP)
- `rand`, `randc`, `randomize()`
- `mailbox`, `semaphore`, `event`
- `fork/join`, `fork/join_any`, `fork/join_none`
- `program`, `clocking` blocks (in testbench context)
- Concurrent `assert property` (runs in simulation; formal tools use it)
- `string` type, `$display` (simulation tasks)

---

## Quick Reference — Verilog to SystemVerilog

| Verilog | SystemVerilog equivalent |
|---------|--------------------------|
| `reg` / `wire` | `logic` |
| `always @(*)` | `always_comb` |
| `always @(posedge clk)` | `always_ff @(posedge clk ...)` |
| `parameter IDLE = 2'b00;` | `typedef enum logic [1:0] {IDLE} state_t;` |
| Manual port list | `interface` + `modport` |
| Repeated `define` in files | `package` + `import` |
| `$clog2()` (some tools) | `$clog2()` — standard in SV |
| `b'0 repeated` | `'0` fill syntax |
| `casex`, `casez` | `unique case` + `don't care` items |
| `input [7:0]` | `input logic [7:0]` |
| `{a, b, c}` concat | Same — unchanged |
| `generate ... endgenerate` | Same — unchanged |

---

## Common Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Using `reg` in SV module | Works but misses tool checks | Use `logic` |
| Using `always @(*)` | Works but misses intent check | Use `always_comb` |
| `typedef enum` without `logic` base | Simulator chooses width | Always specify: `typedef enum logic [1:0] {..} t` |
| `packed struct` with `unpacked` arrays inside | Not synthesisable | Keep packed structs purely bit-level |
| Importing package in wrong file order | Compile error | List packages before modules in compile order |
| Using `class` in RTL | Not synthesisable | Classes go in testbench/UVM only |

---

## What's Next

- **[FSM Design in Verilog]({% post_url 2026-05-17-fsm-design-verilog %})** — apply `typedef enum` and `always_comb` to real state machines
- **[Pipelining RTL Design]({% post_url 2026-05-17-pipeline-rtl-design %})** — use SV features to build a clean 4-stage pipeline
- **[Setup & Hold Time — STA]({% post_url 2026-05-17-setup-hold-time-sta %})** — understand why timing constraints apply to your SV registers
