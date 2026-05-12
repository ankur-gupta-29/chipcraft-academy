"""
cocotb testbench for riscv_single_cycle.v

Runs a 9-instruction RV32I program and verifies all register results:
  addi x1,x0,10   → x1 = 10
  addi x2,x0,20   → x2 = 20
  add  x3,x1,x2   → x3 = 30
  sw   x3,0(x0)   → mem[0] = 30
  lw   x4,0(x0)   → x4 = 30 (round-trip through data memory)
  addi x5,x0,5    → x5 = 5
  bne  x5,x1,+8   → branch taken (5 ≠ 10), skip next instruction
  addi x5,x0,99   → SKIPPED, x5 stays 5
  slt  x6,x1,x2   → x6 = 1  (10 < 20 signed)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def run_cycles(dut, n: int):
    for _ in range(n):
        await RisingEdge(dut.clk)


def read_reg(dut, idx: int) -> int:
    """Read register x{idx} from the register file hierarchy."""
    return int(dut.RF.regs[idx].value)


@cocotb.test()
async def test_riscv_program(dut):
    """Full integration test: run program, verify all target registers."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Hold reset for 3 cycles so PC and registers initialise cleanly
    dut.rst.value = 1
    await run_cycles(dut, 3)
    dut.rst.value = 0

    # 20 cycles is more than enough for 8 active instructions
    await run_cycles(dut, 20)
    await Timer(1, units="ns")   # let combinational paths settle

    x1 = read_reg(dut, 1)
    x2 = read_reg(dut, 2)
    x3 = read_reg(dut, 3)
    x4 = read_reg(dut, 4)
    x5 = read_reg(dut, 5)
    x6 = read_reg(dut, 6)

    assert x1 == 10, f"x1={x1}, expected 10  (addi x1,x0,10)"
    assert x2 == 20, f"x2={x2}, expected 20  (addi x2,x0,20)"
    assert x3 == 30, f"x3={x3}, expected 30  (add x3,x1,x2)"
    assert x4 == 30, f"x4={x4}, expected 30  (lw x4,0(x0) — round-trip via SW)"
    assert x5 ==  5, f"x5={x5}, expected 5   (BNE taken — addi x5,x0,99 skipped)"
    assert x6 ==  1, f"x6={x6}, expected 1   (slt x6,x1,x2: 10<20=true)"
