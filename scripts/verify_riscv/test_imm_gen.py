"""
cocotb testbench for imm_gen.v
Tests all 5 RISC-V immediate formats with both positive and negative values.
"""

import cocotb
from cocotb.triggers import Timer


def to_signed32(val: int) -> int:
    """Convert raw 32-bit unsigned to Python signed int."""
    val = int(val) & 0xFFFFFFFF
    return val - 0x100000000 if val >= 0x80000000 else val


async def drive(dut, instr: int, delay_ns: int = 1):
    """Drive instruction and wait for combinational logic to settle."""
    dut.instr.value = instr & 0xFFFFFFFF
    await Timer(delay_ns, units="ns")


# ── I-type ────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_itype_positive(dut):
    """ADDI x1, x0, 10  →  imm = +10"""
    # imm[11:0]=10, rs1=x0, funct3=0, rd=x1, opcode=0010011
    await drive(dut, 0b000000001010_00000_000_00001_0010011)
    assert to_signed32(dut.imm.value) == 10, \
        f"I-type +10: got {to_signed32(dut.imm.value)}"


@cocotb.test()
async def test_itype_negative(dut):
    """ADDI x1, x0, -1  →  imm = -1  (0xFFFFFFFF)"""
    await drive(dut, 0b111111111111_00000_000_00001_0010011)
    assert to_signed32(dut.imm.value) == -1, \
        f"I-type -1: got {to_signed32(dut.imm.value)}"


@cocotb.test()
async def test_itype_large(dut):
    """ADDI x1, x0, 2047  →  imm = +2047  (max 12-bit positive)"""
    await drive(dut, 0b011111111111_00000_000_00001_0010011)
    assert to_signed32(dut.imm.value) == 2047, \
        f"I-type +2047: got {to_signed32(dut.imm.value)}"


@cocotb.test()
async def test_itype_min(dut):
    """ADDI x1, x0, -2048  →  imm = -2048  (min 12-bit negative)"""
    await drive(dut, 0b100000000000_00000_000_00001_0010011)
    assert to_signed32(dut.imm.value) == -2048, \
        f"I-type -2048: got {to_signed32(dut.imm.value)}"


# ── S-type ────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_stype_positive(dut):
    """SW x3, 4(x0)  →  imm = +4"""
    # imm=4: imm[11:5]=0000000, imm[4:0]=00100
    # instr[31:25]=0000000, rs2=x3, rs1=x0, funct3=010, instr[11:7]=00100
    await drive(dut, 0b0000000_00011_00000_010_00100_0100011)
    assert to_signed32(dut.imm.value) == 4, \
        f"S-type +4: got {to_signed32(dut.imm.value)}"


@cocotb.test()
async def test_stype_negative(dut):
    """SW x3, -4(x0)  →  imm = -4"""
    # imm=-4=0xFFC: imm[11:5]=1111111, imm[4:0]=11100
    await drive(dut, 0b1111111_00011_00000_010_11100_0100011)
    assert to_signed32(dut.imm.value) == -4, \
        f"S-type -4: got {to_signed32(dut.imm.value)}"


# ── B-type ────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_btype_positive(dut):
    """BEQ x0, x0, +8  →  imm = +8"""
    # imm=8: imm[12]=0,imm[11]=0,imm[10:5]=000000,imm[4:1]=0100,imm[0]=0
    # instr[31]=imm[12]=0, instr[7]=imm[11]=0
    # instr[30:25]=000000, instr[11:8]=0100
    await drive(dut, 0b0_000000_00000_00000_000_0100_0_1100011)
    assert to_signed32(dut.imm.value) == 8, \
        f"B-type +8: got {to_signed32(dut.imm.value)}"


@cocotb.test()
async def test_btype_negative(dut):
    """BEQ x0, x0, -8  →  imm = -8"""
    # -8 = 0b1111_1111_1000 → imm[4:1] = bits[4:1] of -8 = 1100 (NOT 1000)
    # imm[12]=1, imm[11]=1, imm[10:5]=111111, imm[4:1]=1100
    # instr[31]=1, instr[7]=1, instr[30:25]=111111, instr[11:8]=1100
    await drive(dut, 0b1_111111_00000_00000_000_1100_1_1100011)
    assert to_signed32(dut.imm.value) == -8, \
        f"B-type -8: got {to_signed32(dut.imm.value)}"


# ── U-type ────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_utype_lui(dut):
    """LUI x1, 0x12345  →  imm = 0x12345000"""
    # instr[31:12] = 0x12345 = 20'h12345
    # opcode for LUI = 0110111
    instr = (0x12345 << 12) | (1 << 7) | 0b0110111
    await drive(dut, instr)
    assert int(dut.imm.value) == 0x12345000, \
        f"U-type LUI: got {hex(int(dut.imm.value))}"


@cocotb.test()
async def test_utype_negative_upper(dut):
    """LUI x1, 0x80000  →  imm = 0x80000000"""
    instr = (0x80000 << 12) | (1 << 7) | 0b0110111
    await drive(dut, instr)
    assert int(dut.imm.value) == 0x80000000, \
        f"U-type 0x80000: got {hex(int(dut.imm.value))}"


# ── J-type ────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_jtype_positive(dut):
    """JAL x1, +4  →  imm = +4"""
    # imm=4: imm[20]=0,imm[19:12]=00000000,imm[11]=0,imm[10:1]=0000000010
    # instr[31]=0, instr[19:12]=00000000, instr[20]=0, instr[30:21]=0000000010
    await drive(dut, 0b0_0000000010_0_00000000_00001_1101111)
    assert to_signed32(dut.imm.value) == 4, \
        f"J-type +4: got {to_signed32(dut.imm.value)}"


@cocotb.test()
async def test_jtype_negative(dut):
    """JAL x1, -4  →  imm = -4"""
    # imm=-4 (21-bit signed): imm[20]=1, all ones except imm[10:1]=1111111110
    # instr[31]=1(imm20), instr[30:21]=1111111110(imm10:1)
    # instr[20]=1(imm11), instr[19:12]=11111111(imm19:12)
    await drive(dut, 0b1_1111111110_1_11111111_00001_1101111)
    assert to_signed32(dut.imm.value) == -4, \
        f"J-type -4: got {to_signed32(dut.imm.value)}"


# ── Edge case ─────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_default_zero(dut):
    """Unknown opcode  →  imm = 0"""
    await drive(dut, 0x00000000)   # opcode=0000000 (undefined)
    assert int(dut.imm.value) == 0, \
        f"Default: got {int(dut.imm.value)}"
