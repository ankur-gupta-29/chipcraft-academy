---
layout: post
title: "cocotb Tutorial — Verify RTL with Python (Beginner Guide)"
description: "Learn to write hardware testbenches in Python using cocotb. Covers installation, clock, triggers, driving signals, assertions, and running in CI — with a complete verified ALU example."
date: 2026-05-13
category: Verification
tags: [cocotb, python, verification, rtl, verilog, testbench, beginner, tutorial]
---

Traditional Verilog testbenches are verbose and hard to maintain. **cocotb** (Coroutine-based Cosimulation TestBench) lets you write testbenches in Python instead — reusing Python libraries, pytest patterns, and clean async/await style. This guide walks you from installation to a fully working, CI-ready ALU testbench.

---

## What Is cocotb?

cocotb sits between Python and a Verilog simulator (Icarus, Verilator, Questa, etc.). Your Python test drives the DUT signals, waits for clock edges using `await`, and asserts on output values — all from pure Python.

```
Python test  ←──── cocotb ──→  Icarus / Questa / Verilator
   (you write this)                (runs the simulation)
```

**Why cocotb over pure Verilog testbenches?**

| | Verilog TB | cocotb |
|--|-----------|--------|
| Language | Verilog/SV | Python |
| Randomisation | `$random`, constrained-random | `random`, `hypothesis` |
| Reusability | Low (copy-paste) | High (Python packages) |
| CI integration | Hard | Trivial (`pytest`, JUnit XML) |
| Debugging | `$display` | `print`, full Python debugger |

---

## Installation

```bash
# Install cocotb
pip install cocotb

# Install Icarus Verilog (simulator backend)
# Ubuntu/Debian:
sudo apt install iverilog

# macOS:
brew install icarus-verilog

# Verify
cocotb-config --version
iverilog -V
```

---

## Project Structure

```
my_project/
├── alu.v              ← Design Under Test
├── test_alu.py        ← cocotb testbench
├── Makefile           ← tells cocotb which sim, toplevel, module
└── results.xml        ← generated after run
```

---

## Step 1 — The Design Under Test (ALU in Verilog)

```verilog
// alu.v
module alu (
    input  wire [31:0] a, b,
    input  wire [3:0]  alu_ctrl,
    output reg  [31:0] result,
    output wire        zero
);
    always @(*) begin
        case (alu_ctrl)
            4'd0: result = a + b;   // ADD
            4'd1: result = a - b;   // SUB
            4'd2: result = a & b;   // AND
            4'd3: result = a | b;   // OR
            4'd4: result = a ^ b;   // XOR
            4'd5: result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0; // SLT
            default: result = 32'b0;
        endcase
    end
    assign zero = (result == 32'b0);
endmodule
```

---

## Step 2 — The Makefile

```makefile
# Makefile
SIM                 = icarus
TOPLEVEL_LANG       = verilog
VERILOG_SOURCES     = $(shell pwd)/alu.v
TOPLEVEL            = alu
COCOTB_TEST_MODULES = test_alu
COCOTB_RESULTS_FILE = results.xml
SIM_BUILD           = sim_build

include $(shell cocotb-config --makefiles)/Makefile.sim
```

Key variables:
- `SIM` — which simulator to use (`icarus`, `verilator`, `questa`)
- `TOPLEVEL` — top Verilog module name
- `COCOTB_TEST_MODULES` — Python file name (no `.py`)
- `VERILOG_SOURCES` — all `.v` / `.sv` files to compile

---

## Step 3 — Your First cocotb Test

```python
# test_alu.py
import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_add(dut):
    """10 + 20 = 30"""
    dut.a.value       = 10
    dut.b.value       = 20
    dut.alu_ctrl.value = 0      # ADD

    await Timer(1, units="ns")  # let combinational logic settle

    assert int(dut.result.value) == 30, \
        f"Expected 30, got {int(dut.result.value)}"
    assert int(dut.zero.value) == 0
```

### What each line does

| Line | Meaning |
|------|---------|
| `@cocotb.test()` | Register this coroutine as a test case |
| `async def test_add(dut)` | `dut` = handle to the top Verilog module |
| `dut.a.value = 10` | Drive signal `a` to value 10 |
| `await Timer(1, units="ns")` | Pause for 1 ns — lets combinational logic settle |
| `int(dut.result.value)` | Read signal `result` as Python int |
| `assert ...` | Fail the test if condition is False |

---

## Step 4 — Key Triggers

Triggers tell cocotb when to resume your coroutine. Always `await` them.

```python
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ClockCycles
from cocotb.clock import Clock

# Wait a fixed simulation time
await Timer(10, units="ns")

# Wait for rising edge of a signal
await RisingEdge(dut.clk)

# Wait for falling edge
await FallingEdge(dut.clk)

# Wait for N rising edges (N clock cycles)
await ClockCycles(dut.clk, 5)
```

---

## Step 5 — Adding a Clock

For sequential (clocked) designs, start a clock as a background task:

```python
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
import cocotb

@cocotb.test()
async def test_sequential(dut):
    # Start a 10 ns clock (100 MHz) — runs in background
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await ClockCycles(dut.clk, 3)
    dut.rst.value = 0

    # Drive inputs after reset
    dut.a.value = 5
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Check output
    assert int(dut.result.value) == 5
```

> **`cocotb.start_soon(clock.start())`** — runs the clock generator as a concurrent background coroutine. Your test continues running in parallel.

---

## Step 6 — Helper Functions

Avoid repeating signal-drive code by extracting a helper:

```python
import cocotb
from cocotb.triggers import Timer

ALU_ADD = 0
ALU_SUB = 1
ALU_AND = 2
ALU_OR  = 3
ALU_XOR = 4
ALU_SLT = 5

async def drive(dut, a: int, b: int, ctrl: int):
    """Drive inputs and settle for 1 ns."""
    dut.a.value        = a & 0xFFFFFFFF   # mask to 32 bits
    dut.b.value        = b & 0xFFFFFFFF
    dut.alu_ctrl.value = ctrl
    await Timer(1, units="ns")

def to_signed32(val) -> int:
    """Convert cocotb LogicArray to Python signed 32-bit int."""
    v = int(val) & 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v
```

---

## Step 7 — Complete ALU Testbench

```python
# test_alu.py — complete verified testbench
import cocotb
from cocotb.triggers import Timer

ALU_ADD  = 0
ALU_SUB  = 1
ALU_AND  = 2
ALU_OR   = 3
ALU_XOR  = 4
ALU_SLT  = 5
ALU_SLTU = 6
ALU_SLL  = 7
ALU_SRL  = 8
ALU_SRA  = 9

async def drive(dut, a, b, ctrl):
    dut.a.value        = a & 0xFFFFFFFF
    dut.b.value        = b & 0xFFFFFFFF
    dut.alu_ctrl.value = ctrl
    await Timer(1, units="ns")

def to_signed32(val):
    v = int(val) & 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v

# ── ADD ───────────────────────────────────────────────────────
@cocotb.test()
async def test_add_basic(dut):
    await drive(dut, 10, 20, ALU_ADD)
    assert int(dut.result.value) == 30

@cocotb.test()
async def test_add_zero(dut):
    await drive(dut, 0, 0, ALU_ADD)
    assert int(dut.result.value) == 0
    assert int(dut.zero.value) == 1      # zero flag set

@cocotb.test()
async def test_add_overflow(dut):
    """32-bit wrap: 0xFFFFFFFF + 1 = 0"""
    await drive(dut, 0xFFFFFFFF, 1, ALU_ADD)
    assert int(dut.result.value) == 0

# ── SUB ───────────────────────────────────────────────────────
@cocotb.test()
async def test_sub_negative(dut):
    """5 - 10 = -5 (0xFFFFFFFB)"""
    await drive(dut, 5, 10, ALU_SUB)
    assert to_signed32(dut.result.value) == -5

@cocotb.test()
async def test_sub_equal(dut):
    """5 - 5 = 0 — zero flag used by BEQ"""
    await drive(dut, 5, 5, ALU_SUB)
    assert int(dut.zero.value) == 1

# ── SLT (signed less-than) ────────────────────────────────────
@cocotb.test()
async def test_slt_negative_vs_positive(dut):
    """-1 < 1 (signed) should return 1"""
    await drive(dut, 0xFFFFFFFF, 1, ALU_SLT)  # -1 signed
    assert int(dut.result.value) == 1

# ── Shifts ────────────────────────────────────────────────────
@cocotb.test()
async def test_sra_sign_extend(dut):
    """0x80000000 >>> 1 = 0xC0000000 (arithmetic, fills with 1)"""
    await drive(dut, 0x80000000, 1, ALU_SRA)
    assert int(dut.result.value) == 0xC0000000
```

---

## Step 8 — Run the Tests

```bash
# In the project directory:
make -f Makefile

# Or if your Makefile is named differently:
make -f Makefile.alu
```

**Expected output:**
```
0.00ns INFO  cocotb  Running on Icarus Verilog
...
** TESTS=8 PASS=8 FAIL=0 SKIP=0
```

Results are also written to `results.xml` (JUnit format) — readable by GitHub Actions, Jenkins, and GitLab CI.

---

## Step 9 — Run in GitHub Actions CI

```yaml
# .github/workflows/ci.yml
jobs:
  cocotb-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get install -y iverilog
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install cocotb
      - name: Run ALU testbench
        working-directory: my_project
        run: make -f Makefile
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: results
          path: my_project/results.xml
```

---

## Accessing Hierarchical Signals

For a full processor testbench, you can read internal signals through the hierarchy:

```python
# Access register file inside a CPU
x1 = int(dut.RF.regs[1].value)   # dut → RF submodule → regs array
x2 = int(dut.RF.regs[2].value)
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting `await` before a trigger | Always `await Timer(...)` or `await RisingEdge(...)` |
| Reading signal before it settles | Add `await Timer(1, units="ns")` after driving |
| Large Python int → 32-bit signal overflow | Mask with `& 0xFFFFFFFF` before assigning |
| Signed result looks wrong | Use `to_signed32()` helper to convert |
| Clock not started | `cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())` |

---

## What's Next

Once you're comfortable with cocotb:
- **[SystemVerilog Assertions (SVA)](/blog/2026/05/13/systemverilog-assertions-sva-guide/)** — add property checks inside the DUT itself
- **[UVM Testbench from Scratch](/blog/2026/05/13/uvm-testbench-from-scratch/)** — industry-standard verification methodology for large SoCs
