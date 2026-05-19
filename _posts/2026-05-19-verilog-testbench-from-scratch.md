---
layout: post
title: "Writing Verilog Testbenches from Scratch — Complete Beginner Guide"
description: "Learn to write self-checking Verilog and SystemVerilog testbenches from zero: clock generation, reset, stimulus, $monitor, VCD waveform dump, pass/fail reporting, and running with Icarus Verilog."
date: 2026-05-19
category: Verification
tags: [testbench, verilog, systemverilog, verification, simulation, icarus, beginner, iverilog]
image: testbench-structure.svg
---

Before you can verify any RTL design — whether it's a simple counter or a full CPU — you need a testbench. A testbench is a Verilog/SystemVerilog module that wraps your design, drives inputs, and checks that the outputs are correct. This guide builds one from scratch, step by step, with no prior verification knowledge required.

---

## What Is a Testbench?

A testbench is a **non-synthesisable** Verilog module that:
1. Instantiates your design (DUT — Design Under Test)
2. Generates a clock and reset
3. Applies stimulus (test inputs)
4. Checks outputs against expected values
5. Reports PASS or FAIL

<img src="{{ '/assets/images/testbench-structure.svg' | relative_url }}" alt="Testbench anatomy diagram" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

**Key difference from RTL:** Testbenches use simulation-only constructs — `initial` blocks, delays (`#`), `$display`, `$finish` — that cannot be synthesised into hardware.

---

## The DUT We'll Test

Let's write a testbench for a simple 4-bit up-counter with synchronous reset:

```verilog
// dut_counter.v — the design under test
module counter #(
    parameter WIDTH = 4
)(
    input  wire             clk,
    input  wire             rst_n,    // active-low synchronous reset
    input  wire             en,       // count enable
    output reg  [WIDTH-1:0] count
);
    always @(posedge clk) begin
        if (!rst_n)    count <= '0;
        else if (en)   count <= count + 1'b1;
    end
endmodule
```

---

## Step 1 — Timescale and Module Declaration

```verilog
// tb_counter.v — testbench for the counter
`timescale 1ns / 1ps   // time unit = 1 ns, precision = 1 ps

module tb_counter;      // no port list — testbenches have no ports
```

**`timescale` is mandatory.** Without it, delays like `#5` have no meaning. `1ns/1ps` means:
- `#5` = 5 nanoseconds
- `#0.001` = 1 picosecond (the finest resolution)

---

## Step 2 — Declare Signals

```verilog
// Signals connected to DUT
reg        clk;
reg        rst_n;
reg        en;
wire [3:0] count;   // output from DUT — must be wire

// Testbench bookkeeping
integer pass_count = 0;
integer fail_count = 0;
```

**Rule:** DUT inputs driven by the testbench are `reg`. DUT outputs received by the testbench are `wire`.

---

## Step 3 — Instantiate the DUT

```verilog
// Instantiate the design under test
counter #(
    .WIDTH(4)
) u_dut (
    .clk   (clk),
    .rst_n (rst_n),
    .en    (en),
    .count (count)
);
```

Always use **named port connections** (`.port(signal)`) — never positional. Named connections catch port order mistakes at compile time.

---

## Step 4 — Generate the Clock

```verilog
// Clock generation — 100 MHz (period = 10 ns)
initial clk = 1'b0;                  // initialise before the always block runs
always #5 clk = ~clk;                // toggle every 5 ns → 10 ns period
```

**How it works:**
- `initial clk = 0` sets the starting value
- `always #5 clk = ~clk` flips every 5 ns
- Result: 10 ns period = 100 MHz clock

For different frequencies:
```verilog
always #4   clk = ~clk;   // 125 MHz (8 ns period)
always #2   clk = ~clk;   // 250 MHz (4 ns period)
always #0.5 clk = ~clk;   // 1 GHz   (1 ns period) — needs 1ns/1ps timescale
```

---

## Step 5 — Apply Reset and Stimulus

```verilog
initial begin
    // ── Waveform dump ──────────────────────────────────────────
    $dumpfile("wave.vcd");         // output file name
    $dumpvars(0, tb_counter);      // dump all signals in tb_counter and below

    // ── Initialise inputs ────────────────────────────────────────
    rst_n = 1'b0;
    en    = 1'b0;

    // ── Apply reset ───────────────────────────────────────────────
    @(posedge clk); #1;            // wait for rising edge + 1 ns (avoid setup)
    @(posedge clk); #1;
    rst_n = 1'b1;                  // release reset after 2 cycles

    // ── Test 1: count while en=1 ──────────────────────────────────
    en = 1'b1;
    repeat(6) @(posedge clk);     // let it count for 6 cycles

    // ── Test 2: hold while en=0 ───────────────────────────────────
    en = 1'b0;
    @(posedge clk); #1;

    // ── Test 3: re-enable and continue ───────────────────────────
    en = 1'b1;
    repeat(4) @(posedge clk);

    // ── Test 4: reset mid-count ───────────────────────────────────
    rst_n = 1'b0;
    @(posedge clk); #1;
    rst_n = 1'b1;
    en = 1'b1;
    repeat(3) @(posedge clk);

    // ── End of test ───────────────────────────────────────────────
    #10;
    $display("──────────────────────────────");
    $display("  Results: %0d PASS  %0d FAIL", pass_count, fail_count);
    if (fail_count == 0)
        $display("  STATUS: *** ALL TESTS PASSED ***");
    else
        $display("  STATUS: *** FAILED ***");
    $display("──────────────────────────────");
    $finish;
end
```

**Why `#1` after `@(posedge clk)`?**
Applying stimulus exactly at the clock edge creates a race condition in simulation — the FF and the testbench both see the signal at time=0. Adding `#1` (1 ps shift) ensures the signal is stable before the next edge.

---

## Step 6 — Self-Checking Monitor

The simplest way to check outputs: use `$monitor` to print every time a signal changes, and an `always` block to check expected values.

```verilog
// ── $monitor: print whenever any listed signal changes ─────────────
initial begin
    $monitor("T=%0t | clk=%b rst_n=%b en=%b | count=%0d",
             $time, clk, rst_n, en, count);
end

// ── Self-checking: compare expected vs actual each clock cycle ────
reg [3:0] expected_count;

always @(posedge clk) begin
    #2;  // small delay so DUT output has settled

    if (!rst_n) begin
        expected_count = 4'd0;
    end else if (en) begin
        expected_count = expected_count + 1;
    end
    // else: hold — expected_count doesn't change

    // Check output
    if (count !== expected_count) begin
        $error("FAIL at T=%0t: expected count=%0d, got count=%0d",
               $time, expected_count, count);
        fail_count = fail_count + 1;
    end else begin
        pass_count = pass_count + 1;
    end
end
```

**`!==` vs `!=`:** Use `!==` for 4-state comparison. `!==` returns true if the signals differ including X or Z states. `!=` treats X as don't-care — you can miss X-propagation bugs.

---

## Step 7 — Close the Module

```verilog
endmodule
```

---

## Complete Testbench

```verilog
`timescale 1ns / 1ps

module tb_counter;

    // ── Signals ────────────────────────────────────────────────────
    reg        clk;
    reg        rst_n;
    reg        en;
    wire [3:0] count;

    integer pass_count = 0;
    integer fail_count = 0;

    // ── DUT Instantiation ──────────────────────────────────────────
    counter #(.WIDTH(4)) u_dut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .count (count)
    );

    // ── Clock ──────────────────────────────────────────────────────
    initial clk = 0;
    always  #5 clk = ~clk;

    // ── Self-checker ───────────────────────────────────────────────
    reg [3:0] expected_count = 0;

    always @(posedge clk) begin
        #2;
        if (!rst_n)      expected_count = 4'd0;
        else if (en)     expected_count = expected_count + 1;

        if (count !== expected_count) begin
            $error("FAIL T=%0t: expected=%0d actual=%0d", $time, expected_count, count);
            fail_count = fail_count + 1;
        end else begin
            pass_count = pass_count + 1;
        end
    end

    // ── Stimulus ───────────────────────────────────────────────────
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_counter);

        rst_n = 0; en = 0;
        @(posedge clk); #1;
        @(posedge clk); #1;
        rst_n = 1;

        // Count up 6 cycles
        en = 1; repeat(6) @(posedge clk);

        // Pause 2 cycles
        en = 0; repeat(2) @(posedge clk);

        // Resume counting 5 cycles
        en = 1; repeat(5) @(posedge clk);

        // Mid-count reset
        rst_n = 0; @(posedge clk); #1; rst_n = 1;
        repeat(3) @(posedge clk);

        #10;
        $display("PASS=%0d  FAIL=%0d", pass_count, fail_count);
        if (fail_count == 0) $display("*** ALL TESTS PASSED ***");
        else                 $display("*** %0d TEST(S) FAILED ***", fail_count);
        $finish;
    end

endmodule
```

---

## Run with Icarus Verilog (Free)

Icarus Verilog (`iverilog`) is a free, open-source Verilog simulator. Install it and run:

```bash
# Install (Ubuntu/WSL)
sudo apt install iverilog gtkwave

# Install (macOS)
brew install icarus-verilog gtkwave

# Compile and simulate
iverilog -o sim.out tb_counter.v dut_counter.v
vvp sim.out

# View waveforms (opens GTKWave)
gtkwave wave.vcd &
```

**Expected output:**
```
T=0 | clk=0 rst_n=0 en=0 | count=0
T=5 | clk=1 rst_n=0 en=0 | count=0
T=10 | clk=0 rst_n=0 en=0 | count=0
T=21 | clk=1 rst_n=1 en=0 | count=0
T=31 | clk=1 rst_n=1 en=1 | count=1
T=41 | clk=1 rst_n=1 en=1 | count=2
...
PASS=16  FAIL=0
*** ALL TESTS PASSED ***
```

---

## Useful System Tasks Reference

| Task | Purpose | Example |
|------|---------|---------|
| `$display` | Print once when executed | `$display("count=%0d", count)` |
| `$monitor` | Print whenever any argument changes | `$monitor("T=%0t count=%0d", $time, count)` |
| `$strobe` | Print at end of current time step | `$strobe("final value=%0d", x)` |
| `$error` | Print error (increments error count) | `$error("Mismatch at T=%0t", $time)` |
| `$fatal` | Print and immediately stop | `$fatal(1, "Unexpected X on output")` |
| `$time` | Current simulation time (integer) | `$display("T=%0d", $time)` |
| `$realtime` | Current simulation time (real) | `$display("T=%0.3f", $realtime)` |
| `$finish` | End simulation | `$finish` |
| `$stop` | Pause simulation (interactive) | `$stop` |
| `$dumpfile` | Set VCD output file | `$dumpfile("wave.vcd")` |
| `$dumpvars` | Dump signal hierarchy | `$dumpvars(0, tb)` |
| `$random` | Pseudo-random integer | `data = $random % 256` |

---

## Common Testbench Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Missing `timescale | Compilation warning, wrong delays | Add `` `timescale 1ns/1ps `` at top |
| DUT output declared as `reg` | Compile error: multiple drivers | Declare DUT outputs as `wire` |
| Applying stimulus exactly at clock edge | Race condition — results non-deterministic | Always apply stimulus `#1` after `@(posedge clk)` |
| Using `!=` instead of `!==` | X/Z values pass checks silently | Use `!==` for strict 4-state comparison |
| No `$finish` | Simulation runs forever | Always call `$finish` at end |
| Forgetting `$dumpfile` before `$dumpvars` | Empty or no VCD file | Always call `$dumpfile` first |
| Not initialising `clk` before `always` block | Clock starts at X | `initial clk = 0;` before the always |

---

## Scaling Up — Tasks and Functions

For larger designs, organise stimulus into reusable tasks:

```verilog
// Task: apply n clock cycles with enable
task automatic count_cycles(input integer n, input logic enable);
    en = enable;
    repeat(n) @(posedge clk);
    #1;
endtask

// Task: apply and check reset
task automatic apply_reset(input integer cycles);
    rst_n = 0;
    repeat(cycles) @(posedge clk);
    #1;
    rst_n = 1;
endtask

// Use in initial block:
initial begin
    apply_reset(2);
    count_cycles(8, 1'b1);     // count 8 cycles enabled
    count_cycles(3, 1'b0);     // hold 3 cycles disabled
    apply_reset(1);            // mid-count reset
    count_cycles(4, 1'b1);
    $finish;
end
```

---

## What's Next

- **[SystemVerilog Assertions (SVA)]({{ '/blog/2026/05/13/systemverilog-assertions-sva-guide/' | relative_url }})** — add automatic property checks inside your testbench
- **[Functional Coverage in SystemVerilog]({{ '/blog/2026/05/13/functional-coverage-systemverilog/' | relative_url }})** — measure how thoroughly your tests exercise the design
- **[cocotb — Python-Based RTL Verification]({{ '/blog/2026/05/13/cocotb-python-rtl-verification-tutorial/' | relative_url }})** — write testbenches in Python instead of Verilog
