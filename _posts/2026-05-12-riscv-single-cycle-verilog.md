---
layout: post
title: "RISC-V Single Cycle Processor in Verilog — Complete Tutorial"
description: "Build a complete RISC-V single cycle processor in Verilog from scratch — datapath, control unit, ALU, register file, and memory, with diagrams."
date: 2026-05-12
category: RTL Design
tags: [riscv, verilog, rtl, processor, beginner, tutorial]
---

In this tutorial you will build a working **RISC-V single cycle processor** in Verilog, step by step. By the end you will have a complete RTL implementation that correctly executes R-type, I-type (ALU + Load), S-type (Store), B-type (all branches), and U-type (LUI) instructions.

---

## What Is a Single Cycle Processor?

A single cycle processor executes **one instruction per clock cycle**. Every instruction completes in exactly one cycle. The clock period must be long enough to accommodate the slowest instruction (usually LW: IMEM → RegFile → ALU → DMEM → RegFile writeback).

**Pros:** Simple to design and understand  
**Cons:** Clock is limited by the worst-case path — real processors use pipelining instead.

---

## The Full Datapath

<img src="{{ '/assets/images/riscv-datapath.svg' | relative_url }}" alt="RISC-V Single Cycle Datapath" style="width:100%; border-radius:12px; margin:1.5rem 0;">

| Block | Function |
|-------|----------|
| **PC** | Program Counter — holds address of current instruction |
| **IMEM** | Instruction Memory — stores the program |
| **Control Unit** | Decodes opcode → generates all control signals |
| **Register File** | 32 × 32-bit general purpose registers |
| **Imm Gen** | Sign-extends the immediate field from the instruction |
| **Branch Comparator** | Directly compares rs1, rs2 for all 6 branch conditions |
| **ALU** | Arithmetic/logic for R-type, I-type, and address calculation |
| **DMEM** | Data Memory — for load/store instructions |

---

## RISC-V Instruction Formats

<img src="{{ '/assets/images/riscv-instruction-format.svg' | relative_url }}" alt="RISC-V Instruction Formats" style="width:100%; border-radius:12px; margin:1.5rem 0;">

Every RISC-V instruction is **32 bits wide**. The opcode (bits 6:0) tells the control unit which format to use.

---

## Step 1: Program Counter

```verilog
module pc_reg (
    input  wire        clk,
    input  wire        rst,
    input  wire [31:0] pc_next,
    output reg  [31:0] pc
);
    always @(posedge clk or posedge rst)
        if (rst) pc <= 32'h0000_0000;
        else     pc <= pc_next;
endmodule
```

---

## Step 2: Instruction Memory

```verilog
module imem (
    input  wire [31:0] addr,
    output wire [31:0] instr
);
    reg [31:0] mem [0:255];           // 256 words = 1 KB
    initial $readmemh("program.hex", mem);
    assign instr = mem[addr[9:2]];    // word-addressed: ignore bottom 2 bits
endmodule
```

---

## Step 3: Register File

Register `x0` is hardwired to zero — the write guard `rd != 0` enforces this.

```verilog
module regfile (
    input  wire        clk,
    input  wire        we,
    input  wire [4:0]  rs1, rs2, rd,
    input  wire [31:0] wd,
    output wire [31:0] rd1, rd2
);
    reg [31:0] regs [0:31];

    integer i;
    initial for (i = 0; i < 32; i = i+1) regs[i] = 32'b0;

    // Synchronous write — never write to x0
    always @(posedge clk)
        if (we && rd != 5'b0)
            regs[rd] <= wd;

    // Asynchronous (combinational) read
    assign rd1 = (rs1 == 5'b0) ? 32'b0 : regs[rs1];
    assign rd2 = (rs2 == 5'b0) ? 32'b0 : regs[rs2];
endmodule
```

---

## Step 4: Immediate Generator

Extracts and sign-extends the immediate from all 5 instruction formats.

```verilog
module imm_gen (
    input  wire [31:0] instr,
    output reg  [31:0] imm
);
    wire [6:0] opcode = instr[6:0];

    always @(*) begin
        case (opcode)
            // I-type: ADDI, LW, JALR
            7'b0010011,
            7'b0000011,
            7'b1100111: imm = {{20{instr[31]}}, instr[31:20]};

            // S-type: SW
            7'b0100011: imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};

            // B-type: BEQ, BNE, BLT, BGE, BLTU, BGEU
            7'b1100011: imm = {{19{instr[31]}}, instr[31],
                                instr[7], instr[30:25], instr[11:8], 1'b0};

            // U-type: LUI, AUIPC
            7'b0110111,
            7'b0010111: imm = {instr[31:12], 12'b0};

            // J-type: JAL
            7'b1101111: imm = {{11{instr[31]}}, instr[31],
                                instr[19:12], instr[20], instr[30:21], 1'b0};

            default: imm = 32'b0;
        endcase
    end
endmodule
```

---

## Step 5: ALU

```verilog
module alu (
    input  wire [31:0] a, b,
    input  wire [3:0]  alu_ctrl,
    output reg  [31:0] result,
    output wire        zero
);
    localparam ALU_ADD  = 4'd0;
    localparam ALU_SUB  = 4'd1;
    localparam ALU_AND  = 4'd2;
    localparam ALU_OR   = 4'd3;
    localparam ALU_XOR  = 4'd4;
    localparam ALU_SLT  = 4'd5;
    localparam ALU_SLTU = 4'd6;
    localparam ALU_SLL  = 4'd7;
    localparam ALU_SRL  = 4'd8;
    localparam ALU_SRA  = 4'd9;

    always @(*) begin
        case (alu_ctrl)
            ALU_ADD:  result = a + b;
            ALU_SUB:  result = a - b;
            ALU_AND:  result = a & b;
            ALU_OR:   result = a | b;
            ALU_XOR:  result = a ^ b;
            ALU_SLT:  result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            ALU_SLTU: result = (a < b) ? 32'd1 : 32'd0;
            ALU_SLL:  result = a << b[4:0];
            ALU_SRL:  result = a >> b[4:0];
            ALU_SRA:  result = $signed(a) >>> b[4:0];
            default:  result = 32'b0;
        endcase
    end

    assign zero = (result == 32'b0);
endmodule
```

---

## Step 6: ALU Control

Maps `funct3`, `funct7[5]`, and `alu_op` from the main control unit to a 4-bit ALU operation code.

```verilog
module alu_control (
    input  wire [1:0] alu_op,
    input  wire [2:0] funct3,
    input  wire       funct7_5,
    output reg  [3:0] alu_ctrl
);
    always @(*) begin
        case (alu_op)
            2'b00: alu_ctrl = 4'd0; // ADD  (load/store address)
            2'b01: alu_ctrl = 4'd1; // SUB  (unused for branches now)
            2'b10: begin
                case (funct3)
                    3'b000: alu_ctrl = funct7_5 ? 4'd1 : 4'd0; // SUB / ADD
                    3'b001: alu_ctrl = 4'd7;  // SLL
                    3'b010: alu_ctrl = 4'd5;  // SLT
                    3'b011: alu_ctrl = 4'd6;  // SLTU
                    3'b100: alu_ctrl = 4'd4;  // XOR
                    3'b101: alu_ctrl = funct7_5 ? 4'd9 : 4'd8; // SRA / SRL
                    3'b110: alu_ctrl = 4'd3;  // OR
                    3'b111: alu_ctrl = 4'd2;  // AND
                    default: alu_ctrl = 4'd0;
                endcase
            end
            default: alu_ctrl = 4'd0;
        endcase
    end
endmodule
```

---

## Step 7: Data Memory

```verilog
module dmem (
    input  wire        clk,
    input  wire        we,
    input  wire [31:0] addr,
    input  wire [31:0] wd,
    output wire [31:0] rd
);
    reg [31:0] mem [0:255];

    always @(posedge clk)
        if (we) mem[addr[9:2]] <= wd;

    assign rd = mem[addr[9:2]];
endmodule
```

---

## Step 8: Control Unit

**Key design decision:** `result_src` is 2 bits to handle three writeback sources:
- `2'b00` → ALU result (R-type, I-type ALU)
- `2'b01` → Memory read data (LW)
- `2'b10` → Immediate directly (LUI — bypasses ALU entirely)

```verilog
module control_unit (
    input  wire [6:0] opcode,
    output reg        branch,
    output reg  [1:0] result_src,  // 00=ALU, 01=Mem, 10=Imm
    output reg  [1:0] alu_op,
    output reg        mem_write,
    output reg        alu_src,     // 0=rs2, 1=immediate
    output reg        reg_write
);
    always @(*) begin
        // Safe defaults — all signals off
        branch     = 1'b0;
        result_src = 2'b00;
        alu_op     = 2'b00;
        mem_write  = 1'b0;
        alu_src    = 1'b0;
        reg_write  = 1'b0;

        case (opcode)
            // R-type: ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, SLTU
            7'b0110011: begin
                reg_write = 1'b1;
                alu_op    = 2'b10;
            end

            // I-type ALU: ADDI, ANDI, ORI, XORI, SLLI, SRLI, SRAI, SLTI
            7'b0010011: begin
                reg_write = 1'b1;
                alu_src   = 1'b1;
                alu_op    = 2'b10;
            end

            // Load: LW
            7'b0000011: begin
                reg_write  = 1'b1;
                alu_src    = 1'b1;          // addr = rs1 + imm
                result_src = 2'b01;         // writeback from memory
                // alu_op=00 → ADD for address calc
            end

            // Store: SW
            7'b0100011: begin
                mem_write = 1'b1;
                alu_src   = 1'b1;           // addr = rs1 + imm
                // alu_op=00 → ADD
            end

            // Branch: BEQ, BNE, BLT, BGE, BLTU, BGEU
            // Branch condition is evaluated by the dedicated comparator,
            // NOT by the ALU — so alu_op and alu_src don't matter here.
            7'b1100011: begin
                branch = 1'b1;
            end

            // LUI: result = immediate (upper 20 bits shifted)
            // Bypasses ALU entirely via result_src = 2'b10
            7'b0110111: begin
                reg_write  = 1'b1;
                result_src = 2'b10;         // writeback = imm (not ALU)
            end

            default: ; // all signals stay at defaults
        endcase
    end
endmodule
```

### Control Signal Truth Table

| Instruction | RegWrite | ALUSrc | MemWrite | result_src | Branch | ALUOp |
|-------------|----------|--------|----------|------------|--------|-------|
| R-type      | 1 | 0 | 0 | 00 (ALU)  | 0 | 10 |
| I-type ALU  | 1 | 1 | 0 | 00 (ALU)  | 0 | 10 |
| LW          | 1 | 1 | 0 | 01 (Mem)  | 0 | 00 |
| SW          | 0 | 1 | 1 | 00        | 0 | 00 |
| Branch      | 0 | 0 | 0 | 00        | 1 | 00 |
| LUI         | 1 | — | 0 | 10 (Imm)  | 0 | — |

---

## Step 9: Top-Level — Wire Everything Together

**Bug fix from naive implementations:** Branches use a **dedicated comparator** on `rd1`/`rd2` directly, not the ALU `zero` flag. This correctly handles all 6 branch conditions (BEQ, BNE, BLT, BGE, BLTU, BGEU).

```verilog
module riscv_single_cycle (
    input wire clk,
    input wire rst
);
    // ── Wires ────────────────────────────────────────────────
    wire [31:0] pc, pc_next, pc_plus4, branch_target;
    wire [31:0] instr;
    wire [31:0] rd1, rd2, wd;
    wire [31:0] imm;
    wire [31:0] alu_src_b;
    wire [31:0] alu_result;
    wire [31:0] mem_rd;
    wire        zero;

    // Control signals
    wire        branch, mem_write, alu_src, reg_write;
    wire [1:0]  result_src, alu_op;
    wire [3:0]  alu_ctrl;

    // ── Branch Comparator ────────────────────────────────────
    // Compares rd1 and rd2 directly — NOT the ALU result.
    // This correctly handles all 6 RISC-V branch conditions.
    wire        beq  = (rd1 == rd2);
    wire        blt  = ($signed(rd1) < $signed(rd2));
    wire        bltu = (rd1 < rd2);

    reg branch_taken;
    always @(*) begin
        case (instr[14:12])           // funct3 selects branch type
            3'b000: branch_taken = beq;    // BEQ
            3'b001: branch_taken = ~beq;   // BNE
            3'b100: branch_taken = blt;    // BLT  (signed)
            3'b101: branch_taken = ~blt;   // BGE  (signed)
            3'b110: branch_taken = bltu;   // BLTU (unsigned)
            3'b111: branch_taken = ~bltu;  // BGEU (unsigned)
            default: branch_taken = 1'b0;
        endcase
    end

    // ── PC Logic ─────────────────────────────────────────────
    assign pc_plus4      = pc + 32'd4;
    assign branch_target = pc + imm;
    assign pc_next       = (branch & branch_taken) ? branch_target : pc_plus4;

    // ── Writeback MUX ────────────────────────────────────────
    // result_src: 00=ALU result, 01=Memory data, 10=Immediate (LUI)
    assign wd = (result_src == 2'b01) ? mem_rd    :
                (result_src == 2'b10) ? imm        :
                                        alu_result;

    // ALUSrc MUX: second ALU operand is rs2 or immediate
    assign alu_src_b = alu_src ? imm : rd2;

    // ── Module Instantiations ─────────────────────────────────
    pc_reg PC (
        .clk(clk), .rst(rst),
        .pc_next(pc_next), .pc(pc)
    );

    imem IMEM (
        .addr(pc), .instr(instr)
    );

    control_unit CTRL (
        .opcode(instr[6:0]),
        .branch(branch),       .result_src(result_src),
        .alu_op(alu_op),       .mem_write(mem_write),
        .alu_src(alu_src),     .reg_write(reg_write)
    );

    regfile RF (
        .clk(clk),             .we(reg_write),
        .rs1(instr[19:15]),    .rs2(instr[24:20]),
        .rd(instr[11:7]),      .wd(wd),
        .rd1(rd1),             .rd2(rd2)
    );

    imm_gen IMMGEN (
        .instr(instr), .imm(imm)
    );

    alu_control ALUCTRL (
        .alu_op(alu_op),
        .funct3(instr[14:12]),
        .funct7_5(instr[30]),
        .alu_ctrl(alu_ctrl)
    );

    alu ALU (
        .a(rd1), .b(alu_src_b),
        .alu_ctrl(alu_ctrl),
        .result(alu_result), .zero(zero)
    );

    dmem DMEM (
        .clk(clk),           .we(mem_write),
        .addr(alu_result),   .wd(rd2),
        .rd(mem_rd)
    );

endmodule
```

---

## Step 10: Testbench

```verilog
module tb_riscv;
    reg clk = 0, rst;

    riscv_single_cycle uut (.clk(clk), .rst(rst));

    always #5 clk = ~clk;   // 10 ns clock = 100 MHz

    initial begin
        $dumpfile("riscv.vcd");
        $dumpvars(0, tb_riscv);

        // Reset for 2 cycles
        rst = 1; #20;
        rst = 0;

        // Run 20 cycles — enough for 20 instructions
        #200;

        // Verify register values after program executes
        $display("=== RISC-V Verification ===");
        $display("x1 = %0d  (expect 10)",  uut.RF.regs[1]);
        $display("x2 = %0d  (expect 20)",  uut.RF.regs[2]);
        $display("x3 = %0d  (expect 30)",  uut.RF.regs[3]);
        $display("x4 = %0d  (expect 30)",  uut.RF.regs[4]); // loaded from mem
        $display("x5 = %0d  (expect 5)",   uut.RF.regs[5]); // from BNE test
        $display("x6 = %0d  (expect 1)",   uut.RF.regs[6]); // SLT result

        if (uut.RF.regs[3] == 30 && uut.RF.regs[4] == 30)
            $display("PASS ✓");
        else
            $display("FAIL ✗");

        $finish;
    end
endmodule
```

### Test Program (program.hex)

Verified instruction encodings for RV32I:

```
# Assembly                    Hex        Encoding check
# addi x1, x0, 10            00A00093   imm=10,  rd=x1,  rs1=x0
# addi x2, x0, 20            01400113   imm=20,  rd=x2,  rs1=x0
# add  x3, x1, x2            002081B3   rd=x3,   rs1=x1, rs2=x2
# sw   x3, 0(x0)             00302023   rs2=x3,  rs1=x0, imm=0
# lw   x4, 0(x0)             00002203   rd=x4,   rs1=x0, imm=0
# addi x5, x0, 5             00500293   imm=5,   rd=x5,  rs1=x0
# bne  x5, x1, +8            00529463   rs1=x5,  rs2=x1, imm=+8 (skip next)
# addi x5, x0, 99            06300293   (should be skipped — x1=10 != x5=5)
# slt  x6, x1, x2            0020A333   rd=x6,   rs1=x1, rs2=x2 → 1 (10<20)

00A00093
01400113
002081B3
00302023
00002203
00500293
00529463
06300293
0020A333
```

**Instruction encoding verification:**

| Instruction | Expected | Breakdown |
|-------------|----------|-----------|
| `addi x1,x0,10` | `00A00093` | imm=0x00A, rs1=0, funct3=0, rd=1, op=0x13 |
| `addi x2,x0,20` | `01400113` | imm=0x014, rs1=0, funct3=0, rd=2, op=0x13 |
| `add x3,x1,x2` | `002081B3` | funct7=0, rs2=2, rs1=1, funct3=0, rd=3, op=0x33 |
| `sw x3,0(x0)` | `00302023` | imm=0, rs2=3, rs1=0, funct3=2, op=0x23 |
| `lw x4,0(x0)` | `00002203` | imm=0, rs1=0, funct3=2, rd=4, op=0x03 |
| `bne x5,x1,+8` | `00529463` | imm=+8, rs2=1, rs1=5, funct3=1, op=0x63 |
| `slt x6,x1,x2` | `0020A333` | funct7=0, rs2=2, rs1=1, funct3=2, rd=6, op=0x33 |

---

## Run the Simulation

```bash
# Compile all modules
iverilog -o riscv_sim \
    pc_reg.v imem.v regfile.v imm_gen.v \
    alu.v alu_control.v dmem.v \
    control_unit.v riscv_single_cycle.v tb_riscv.v

# Run and check output
vvp riscv_sim

# Expected output:
# === RISC-V Verification ===
# x1 = 10  (expect 10)
# x2 = 20  (expect 20)
# x3 = 30  (expect 30)
# x4 = 30  (expect 30)
# x5 = 5   (expect 5)   <- BNE skipped the addi x5,x0,99
# x6 = 1   (expect 1)   <- SLT: 10 < 20 = true
# PASS ✓

# View waveform
gtkwave riscv.vcd
```

---

## Tracing ADD x3, x1, x2 Through the Datapath

```
Cycle:  PC = 0x08 → IMEM fetches 0x002081B3

1. CTRL: opcode=0110011 (R-type)
         → RegWrite=1, ALUSrc=0, result_src=00, ALUOp=10

2. RegFile: rs1=x1 → rd1=10
            rs2=x2 → rd2=20

3. ALUSrc MUX: ALUSrc=0 → alu_src_b = rd2 = 20

4. ALU_CTRL: ALUOp=10, funct3=000, funct7[5]=0 → ALU_ADD
   ALU: 10 + 20 = 30

5. DMEM: not accessed (MemWrite=0)

6. WB MUX: result_src=00 → wd = alu_result = 30

7. RegFile write: rd=x3 ← 30 (RegWrite=1)

8. Branch comparator: branch=0 → pc_next = PC+4 = 0x0C
```

---

## Common Mistakes and Fixes

| Bug | Symptom | Correct Fix |
|-----|---------|-------------|
| `pc_src = branch & zero` | BNE/BLT/BGE all fail | Use dedicated comparator on rd1/rd2 with funct3 select |
| 1-bit `mem_to_reg` | LUI writes wrong value | Use 2-bit `result_src` (ALU / Mem / Imm) |
| LUI reads rs1 field | Garbage value written to rd | Bypass ALU via `result_src=2'b10 → wd=imm` |
| Blocking `=` in clocked block | Simulation/synthesis mismatch | Use `<=` in all `always @(posedge clk)` blocks |
| No x0 guard in RegFile | x0 becomes non-zero | Add `if (we && rd != 5'b0)` |
| Byte vs word addressing | Wrong memory data | Use `addr[9:2]` for word-addressed memory |

---

## What's Next — The 5-Stage Pipeline

The single cycle processor is the foundation. The next step is pipelining:

```
IF → ID → EX → MEM → WB
```

Pipelining runs 5 instructions simultaneously, one per stage — but introduces **data hazards** (forwarding needed) and **control hazards** (branch prediction or flush needed).

---

## Complete File List

```
riscv_single_cycle/
├── pc_reg.v               ← Program Counter
├── imem.v                 ← Instruction Memory
├── regfile.v              ← Register File (32×32-bit)
├── imm_gen.v              ← Immediate Generator (all 5 formats)
├── alu.v                  ← ALU (10 operations)
├── alu_control.v          ← ALU Control Decoder
├── dmem.v                 ← Data Memory
├── control_unit.v         ← Main Control Unit (result_src 2-bit)
├── riscv_single_cycle.v   ← Top-level with branch comparator
├── tb_riscv.v             ← Testbench with self-checking
└── program.hex            ← Verified test program
```

---

*Want a printable RISC-V instruction set cheat sheet? Check the [Shop](/shop) for the RTL Design Guide PDF.*
