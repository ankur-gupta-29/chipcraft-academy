"""
cocotb testbench for alu.v
Tests all 10 ALU operations including edge cases.
"""

import cocotb
from cocotb.triggers import Timer

# ALU control codes — must match alu.v localparam values
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


def to_signed32(val: int) -> int:
    val = int(val) & 0xFFFFFFFF
    return val - 0x100000000 if val >= 0x80000000 else val


async def drive(dut, a: int, b: int, ctrl: int):
    dut.a.value        = a & 0xFFFFFFFF
    dut.b.value        = b & 0xFFFFFFFF
    dut.alu_ctrl.value = ctrl
    await Timer(1, units="ns")


# ── ADD ───────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_add_basic(dut):
    """10 + 20 = 30"""
    await drive(dut, 10, 20, ALU_ADD)
    assert int(dut.result.value) == 30
    assert int(dut.zero.value) == 0


@cocotb.test()
async def test_add_zero(dut):
    """0 + 0 = 0  (zero flag set)"""
    await drive(dut, 0, 0, ALU_ADD)
    assert int(dut.result.value) == 0
    assert int(dut.zero.value) == 1


@cocotb.test()
async def test_add_overflow(dut):
    """0xFFFFFFFF + 1 = 0x00000000 (32-bit wrap)"""
    await drive(dut, 0xFFFFFFFF, 1, ALU_ADD)
    assert int(dut.result.value) == 0


# ── SUB ───────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_sub_basic(dut):
    """20 - 10 = 10"""
    await drive(dut, 20, 10, ALU_SUB)
    assert int(dut.result.value) == 10
    assert int(dut.zero.value) == 0


@cocotb.test()
async def test_sub_equal(dut):
    """5 - 5 = 0  (zero flag set — used by BEQ)"""
    await drive(dut, 5, 5, ALU_SUB)
    assert int(dut.result.value) == 0
    assert int(dut.zero.value) == 1


@cocotb.test()
async def test_sub_negative(dut):
    """5 - 10 = -5 (0xFFFFFFFB)"""
    await drive(dut, 5, 10, ALU_SUB)
    assert to_signed32(dut.result.value) == -5


# ── AND / OR / XOR ────────────────────────────────────────────────────────────

@cocotb.test()
async def test_and(dut):
    """0xFF & 0x0F = 0x0F"""
    await drive(dut, 0xFF, 0x0F, ALU_AND)
    assert int(dut.result.value) == 0x0F


@cocotb.test()
async def test_or(dut):
    """0xF0 | 0x0F = 0xFF"""
    await drive(dut, 0xF0, 0x0F, ALU_OR)
    assert int(dut.result.value) == 0xFF


@cocotb.test()
async def test_xor(dut):
    """0xFF ^ 0xF0 = 0x0F"""
    await drive(dut, 0xFF, 0xF0, ALU_XOR)
    assert int(dut.result.value) == 0x0F


@cocotb.test()
async def test_xor_same(dut):
    """a ^ a = 0"""
    await drive(dut, 0xDEADBEEF, 0xDEADBEEF, ALU_XOR)
    assert int(dut.result.value) == 0
    assert int(dut.zero.value) == 1


# ── SLT (signed) ─────────────────────────────────────────────────────────────

@cocotb.test()
async def test_slt_true(dut):
    """5 < 10 (signed) = 1"""
    await drive(dut, 5, 10, ALU_SLT)
    assert int(dut.result.value) == 1


@cocotb.test()
async def test_slt_false(dut):
    """10 < 5 (signed) = 0"""
    await drive(dut, 10, 5, ALU_SLT)
    assert int(dut.result.value) == 0


@cocotb.test()
async def test_slt_negative(dut):
    """-1 < 1 (signed) = 1"""
    await drive(dut, 0xFFFFFFFF, 1, ALU_SLT)   # -1 signed
    assert int(dut.result.value) == 1


@cocotb.test()
async def test_slt_equal(dut):
    """5 < 5 (signed) = 0"""
    await drive(dut, 5, 5, ALU_SLT)
    assert int(dut.result.value) == 0


# ── SLTU (unsigned) ──────────────────────────────────────────────────────────

@cocotb.test()
async def test_sltu_unsigned_lt(dut):
    """1 < 0xFFFFFFFF (unsigned) = 1"""
    await drive(dut, 1, 0xFFFFFFFF, ALU_SLTU)
    assert int(dut.result.value) == 1


@cocotb.test()
async def test_sltu_unsigned_gt(dut):
    """0xFFFFFFFF < 1 (unsigned) = 0"""
    await drive(dut, 0xFFFFFFFF, 1, ALU_SLTU)
    assert int(dut.result.value) == 0


# ── Shifts ────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_sll(dut):
    """1 << 4 = 16"""
    await drive(dut, 1, 4, ALU_SLL)
    assert int(dut.result.value) == 16


@cocotb.test()
async def test_srl(dut):
    """0x80000000 >> 1 = 0x40000000 (logical, fills with 0)"""
    await drive(dut, 0x80000000, 1, ALU_SRL)
    assert int(dut.result.value) == 0x40000000


@cocotb.test()
async def test_sra_negative(dut):
    """0x80000000 >>> 1 = 0xC0000000 (arithmetic, fills with 1)"""
    await drive(dut, 0x80000000, 1, ALU_SRA)
    assert int(dut.result.value) == 0xC0000000


@cocotb.test()
async def test_sra_positive(dut):
    """16 >>> 2 = 4 (arithmetic, positive number same as SRL)"""
    await drive(dut, 16, 2, ALU_SRA)
    assert int(dut.result.value) == 4


@cocotb.test()
async def test_shift_uses_lower5_bits(dut):
    """Shift amount uses only b[4:0] — shift by 33 same as shift by 1"""
    await drive(dut, 0x1, 33, ALU_SLL)   # 33 & 0x1F = 1
    assert int(dut.result.value) == 2
