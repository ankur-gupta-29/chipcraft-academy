---
layout: post
title: "How to Start Learning RTL Design from Zero"
description: "A concrete, step-by-step learning plan for complete beginners starting RTL design with no prior hardware experience."
date: 2026-05-10
category: RTL Design
tags: [rtl, verilog, beginner, learning-path]
---

You've decided to learn RTL design. Maybe you want to break into the semiconductor industry, maybe you're curious how hardware works at a deep level, or maybe you just want to understand what your chip actually does.

This article gives you a concrete plan — not vague advice, but specific things to do in a specific order.

---

## Before You Start: Mindset Shift

RTL design is **not** the same as software programming. A few things to internalize early:

1. **Concurrency is the default.** In hardware, everything runs simultaneously. Unlike a CPU executing instructions one by one, your Verilog modules run in parallel.

2. **You're describing hardware, not writing instructions.** When you write `assign out = a & b;`, you're not telling a processor to AND two registers — you're *instantiating a logic gate*.

3. **Simulation is your main feedback tool.** You can't print to a console from hardware. You write testbenches that drive inputs and check outputs.

4. **Synthesis has constraints software doesn't.** Not all valid Verilog simulates and synthesizes correctly. Some constructs (like loops with non-constant bounds) don't map to real hardware.

---

## Phase 1: Digital Logic Fundamentals (1–2 weeks)

Before writing a single line of Verilog, make sure you understand:

- **Binary arithmetic** — how numbers are represented in bits
- **Logic gates** — AND, OR, NOT, XOR and their truth tables
- **Combinational circuits** — multiplexers, decoders, adders
- **Sequential circuits** — flip-flops (D, JK), latches
- **Finite State Machines (FSMs)** — Mealy vs Moore machines
- **Clock and timing** — what a clock signal does, setup/hold time

**Resources:**
- *Digital Design and Computer Architecture* (Harris & Harris) — Chapters 1–3
- Ben Eater's YouTube series on building an 8-bit computer (visual and excellent)
- Any "Digital Logic" textbook introductory chapters

---

## Phase 2: Verilog Basics (2–4 weeks)

Now pick up Verilog. Work through [HDLBits](https://hdlbits.01xz.net) from the beginning. It covers:

- Module ports and instantiation
- `assign` for combinational logic
- `always @(*)` and `always @(posedge clk)` blocks
- `if/else` and `case` statements
- Parameters and generate blocks
- Finite State Machines in Verilog

**Target:** Complete all HDLBits exercises through the FSM section. This will take 15–30 hours.

### Key Verilog concepts to understand deeply:

```verilog
// Combinational: runs whenever inputs change
always @(*) begin
  case (sel)
    2'b00: out = a;
    2'b01: out = b;
    default: out = 0;
  endcase
end

// Sequential: runs on clock edge
always @(posedge clk or posedge rst) begin
  if (rst)
    count <= 0;
  else
    count <= count + 1;
end
```

**Key distinction:** `=` (blocking assignment) vs `<=` (non-blocking assignment). Get this wrong and your simulation and synthesis will disagree. Rule: use `<=` in `always @(posedge clk)` blocks, use `=` in combinational blocks.

---

## Phase 3: Simulation & Testbenches (2–3 weeks)

A design you can't test is worthless. Learn to write testbenches.

Here is the design under test (DUT) and its testbench together:

```verilog
// ── Design Under Test ──────────────────────────────────────
module adder (
  input  [7:0] a, b,
  output [8:0] sum
);
  assign sum = a + b;
endmodule

// ── Testbench ──────────────────────────────────────────────
module tb_adder;
  reg  [7:0] a, b;
  wire [8:0] sum;

  adder uut (.a(a), .b(b), .sum(sum));

  initial begin
    $dumpfile("out.vcd");
    $dumpvars(0, tb_adder);

    a = 8'd10; b = 8'd20; #10;
    $display("10+20=%0d (expect 30)", sum);

    a = 8'd255; b = 8'd1; #10;
    $display("255+1=%0d (expect 256)", sum);

    $finish;
  end
endmodule
```

**Tools to use:**
- [EDA Playground](https://edaplayground.com) — browser-based, zero setup
- Or locally: `iverilog` + `vvp` + `gtkwave` (all free)

**What to practice:**
- Write testbenches for each HDLBits problem you solved
- Check outputs with `$display` and `$monitor`
- View waveforms in GTKWave — being able to read waveforms is a core skill

---

## Phase 4: RTL Design Patterns (3–4 weeks)

Now learn how real RTL is structured. Key patterns:

### Synchronous Reset Convention
Always use synchronous reset (unless you have good reason not to):
```verilog
always @(posedge clk) begin
  if (rst) state <= IDLE;
  else     state <= next_state;
end
```

### Two-Process FSM Style
Separate your state register from your combinational next-state logic:
```verilog
// Process 1: state register
always @(posedge clk) state <= next_state;

// Process 2: next state + output logic
always @(*) begin
  next_state = state;  // default: stay in current state
  out = 0;
  case (state)
    IDLE: if (start) next_state = ACTIVE;
    ACTIVE: begin
      out = 1;
      if (done) next_state = IDLE;
    end
  endcase
end
```

### Pipelining
Break long combinational paths across multiple clock cycles:
```verilog
// Stage 1
always @(posedge clk) pipe1 <= a * b;
// Stage 2
always @(posedge clk) result <= pipe1 + c;
```

**Projects to build:**
1. 8-bit ALU (add, sub, AND, OR, XOR, shift)
2. UART transmitter (serial communication)
3. Traffic light controller (FSM)
4. Simple FIFO (synchronous, parameterized depth)

---

## Phase 5: Synthesis Awareness (ongoing)

Once you're writing RTL fluently, start thinking about synthesis:

- **Combinational loops are forbidden** — every feedback path must go through a register
- **Latches are usually bugs** — if your `always @(*)` block doesn't assign a signal in every branch, you'll infer a latch
- **Unintended clock gating** — be careful with `if` conditions on clock signals
- **Resource inference** — `*` infers a multiplier, `>>` infers a shifter — know what hardware you're generating

**Free synthesis tool:** [Yosys](https://yosyshq.net/yosys/) — synthesize your Verilog and see the gate-level netlist.

---

## Checklist: Am I Ready for Intermediate RTL?

- [ ] I can write any combinational circuit in Verilog without looking up syntax
- [ ] I can implement a Mealy and Moore FSM from a state diagram
- [ ] I understand blocking vs non-blocking assignment
- [ ] I can write a basic testbench with stimulus and checking
- [ ] I can read GTKWave waveforms and trace a bug to its source
- [ ] I know when I'm accidentally inferring a latch
- [ ] I've built at least 2 non-trivial projects (UART, ALU, FIFO, etc.)

If you can check all these boxes, you're ready for SystemVerilog, UVM verification, and deeper ASIC concepts.

---

## The Fastest Path (Summary)

| Week | Focus |
|------|-------|
| 1–2 | Digital logic fundamentals (not Verilog yet) |
| 3–6 | HDLBits — all exercises |
| 7–8 | EDA Playground — write testbenches |
| 9–12 | Build 3 projects: ALU, UART, FSM |
| 13+ | Synthesis, SystemVerilog, UVM |

---

*Need the right courses to go alongside this plan? See the [Courses page](/courses) for my top picks.*
