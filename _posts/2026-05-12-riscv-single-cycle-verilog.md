---
layout: post
title: "RISC-V Single Cycle Processor in Verilog — Complete Tutorial"
description: "Build a complete RISC-V single cycle processor in Verilog from scratch — datapath, control unit, ALU, register file, and memory, with diagrams."
date: 2026-05-12
category: RTL Design
tags: [riscv, verilog, rtl, processor, beginner, tutorial]
---

In this tutorial you will build a working **RISC-V single cycle processor** in Verilog, step by step. By the end you will have a complete RTL implementation that can execute R-type, I-type, S-type, B-type, and U-type instructions — the core of the RV32I base instruction set.

This is one of the best learning projects for RTL design because it touches every major concept: combinational logic, sequential logic, FSMs, memory, and control signals.

---

## What Is a Single Cycle Processor?

A single cycle processor executes **one instruction per clock cycle**. Every instruction — whether it is an ADD or a memory LOAD — completes in exactly one cycle. The clock period must be long enough to accommodate the slowest instruction (usually a load: IMEM → RegFile → ALU → DMEM → RegFile).

**Pros:** Simple to design and understand  
**Cons:** Slow — clock limited by worst-case path. Real processors use pipelining to fix this.

---

## The Full Datapath

<img src="{{ '/assets/images/riscv-datapath.svg' | relative_url }}" alt="RISC-V Single Cycle Datapath" style="width:100%; border-radius:12px; margin:1.5rem 0;">

The datapath has 7 major components:

| Block | Function |
|-------|----------|
| **PC** | Program Counter — holds address of current instruction |
| **IMEM** | Instruction Memory — stores the program |
| **Control Unit** | Decodes opcode → generates all control signals |
| **Register File** | 32 × 32-bit general purpose registers |
| **Imm Gen** | Sign-extends the immediate field from the instruction |
| **ALU** | Performs arithmetic and logic operations |
| **DMEM** | Data Memory — for load/store instructions |

---

## RISC-V Instruction Formats

<img src="{{ '/assets/images/riscv-instruction-format.svg' | relative_url }}" alt="RISC-V Instruction Formats" style="width:100%; border-radius:12px; margin:1.5rem 0;">

Every RISC-V instruction is **32 bits wide**. The format determines where the fields sit:

- **R-type** — register-register operations (ADD, SUB, AND, OR, XOR, SLT)
- **I-type** — immediate operations and loads (ADDI, LW, JALR)
- **S-type** — stores (SW, SB, SH)
- **B-type** — branches (BEQ, BNE, BLT, BGE)
- **U-type** — upper immediate (LUI, AUIPC)

The **opcode** field (bits 6:0) tells the control unit which format and operation it is.

---

## Step 1: Program Counter

The PC register holds the address of the current instruction. Each cycle it updates to either `PC+4` (next instruction) or a branch/jump target.

```verilog
module pc_reg (
    input  wire        clk,
    input  wire        rst,
    input  wire [31:0] pc_next,
    output reg  [31:0] pc
);
    always @(posedge clk or posedge rst) begin
        if (rst) pc <= 32'h0000_0000;
        else     pc <= pc_next;
    end
endmodule
```

---

## Step 2: Instruction Memory

A simple read-only memory initialised from a hex file. In simulation we load a program into it.

```verilog
module imem (
    input  wire [31:0] addr,
    output wire [31:0] instr
);
    reg [31:0] mem [0:255];   // 256 words = 1KB

    initial $readmemh("program.hex", mem);

    assign instr = mem[addr[9:2]]; // word-addressed (ignore bottom 2 bits)
endmodule
```

---

## Step 3: Register File

32 registers, each 32 bits wide. Register x0 is hardwired to zero. We read two registers (rs1, rs2) and write one (rd) every cycle.

```verilog
module regfile (
    input  wire        clk,
    input  wire        we,          // write enable (RegWrite)
    input  wire [4:0]  rs1, rs2,    // source register addresses
    input  wire [4:0]  rd,          // destination register address
    input  wire [31:0] wd,          // write data
    output wire [31:0] rd1, rd2     // read data outputs
);
    reg [31:0] regs [0:31];

    integer i;
    initial for (i = 0; i < 32; i = i+1) regs[i] = 32'b0;

    // Synchronous write
    always @(posedge clk)
        if (we && rd != 5'b0)       // never write to x0
            regs[rd] <= wd;

    // Asynchronous read (combinational)
    assign rd1 = (rs1 == 5'b0) ? 32'b0 : regs[rs1];
    assign rd2 = (rs2 == 5'b0) ? 32'b0 : regs[rs2];
endmodule
```

---

## Step 4: Immediate Generator

Extracts and sign-extends the immediate value from the instruction based on its format.

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

            // S-type: SW, SB
            7'b0100011: imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};

            // B-type: BEQ, BNE, BLT, BGE
            7'b1100011: imm = {{19{instr[31]}}, instr[31],
                                instr[7], instr[30:25], instr[11:8], 1'b0};

            // U-type: LUI, AUIPC
            7'b0110111,
            7'b0010111: imm = {instr[31:12], 12'b0};

            // J-type: JAL
            7'b1101111: imm = {{11{instr[31]}}, instr[31],
                                instr[19:12], instr[20], instr[30:21], 1'b0};

            default:    imm = 32'b0;
        endcase
    end
endmodule
```

---

## Step 5: ALU

The ALU performs all arithmetic and logic operations. It also produces a `zero` flag used for branch decisions.

```verilog
module alu (
    input  wire [31:0] a, b,
    input  wire [3:0]  alu_ctrl,
    output reg  [31:0] result,
    output wire        zero
);
    // ALU control codes
    localparam ALU_ADD  = 4'b0000;
    localparam ALU_SUB  = 4'b0001;
    localparam ALU_AND  = 4'b0010;
    localparam ALU_OR   = 4'b0011;
    localparam ALU_XOR  = 4'b0100;
    localparam ALU_SLT  = 4'b0101;  // set less than (signed)
    localparam ALU_SLTU = 4'b0110;  // set less than (unsigned)
    localparam ALU_SLL  = 4'b0111;  // shift left logical
    localparam ALU_SRL  = 4'b1000;  // shift right logical
    localparam ALU_SRA  = 4'b1001;  // shift right arithmetic

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

A small decoder that maps `funct3`, `funct7`, and `alu_op` (from the main control) to the 4-bit ALU control code.

```verilog
module alu_control (
    input  wire [1:0] alu_op,
    input  wire [2:0] funct3,
    input  wire       funct7_5,   // instr[30]
    output reg  [3:0] alu_ctrl
);
    always @(*) begin
        case (alu_op)
            2'b00: alu_ctrl = 4'b0000; // ADD (for loads/stores)
            2'b01: alu_ctrl = 4'b0001; // SUB (for branches)
            2'b10: begin               // R-type / I-type
                case (funct3)
                    3'b000: alu_ctrl = (funct7_5) ? 4'b0001 : 4'b0000; // SUB/ADD
                    3'b001: alu_ctrl = 4'b0111; // SLL
                    3'b010: alu_ctrl = 4'b0101; // SLT
                    3'b011: alu_ctrl = 4'b0110; // SLTU
                    3'b100: alu_ctrl = 4'b0100; // XOR
                    3'b101: alu_ctrl = (funct7_5) ? 4'b1001 : 4'b1000; // SRA/SRL
                    3'b110: alu_ctrl = 4'b0011; // OR
                    3'b111: alu_ctrl = 4'b0010; // AND
                    default: alu_ctrl = 4'b0000;
                endcase
            end
            default: alu_ctrl = 4'b0000;
        endcase
    end
endmodule
```

---

## Step 7: Data Memory

A synchronous write, asynchronous read memory for loads and stores.

```verilog
module dmem (
    input  wire        clk,
    input  wire        we,          // MemWrite
    input  wire [31:0] addr,
    input  wire [31:0] wd,          // write data (for SW)
    output wire [31:0] rd           // read data  (for LW)
);
    reg [31:0] mem [0:255];

    always @(posedge clk)
        if (we) mem[addr[9:2]] <= wd;

    assign rd = mem[addr[9:2]];
endmodule
```

---

## Step 8: Control Unit

The control unit decodes the opcode and generates all datapath control signals. This is the brain of the processor.

```verilog
module control_unit (
    input  wire [6:0] opcode,
    output reg        branch,
    output reg        mem_read,
    output reg        mem_to_reg,
    output reg [1:0]  alu_op,
    output reg        mem_write,
    output reg        alu_src,
    output reg        reg_write
);
    always @(*) begin
        // defaults
        {branch, mem_read, mem_to_reg, mem_write, alu_src, reg_write} = 6'b0;
        alu_op = 2'b00;

        case (opcode)
            // R-type: ADD, SUB, AND, OR, XOR, SLT ...
            7'b0110011: begin
                reg_write = 1; alu_op = 2'b10;
            end
            // I-type ALU: ADDI, ANDI, ORI, XORI, SLTI ...
            7'b0010011: begin
                reg_write = 1; alu_src = 1; alu_op = 2'b10;
            end
            // Load: LW
            7'b0000011: begin
                mem_read = 1; mem_to_reg = 1;
                reg_write = 1; alu_src  = 1; alu_op = 2'b00;
            end
            // Store: SW
            7'b0100011: begin
                mem_write = 1; alu_src = 1; alu_op = 2'b00;
            end
            // Branch: BEQ, BNE, BLT, BGE
            7'b1100011: begin
                branch = 1; alu_op = 2'b01;
            end
            // LUI
            7'b0110111: begin
                reg_write = 1; alu_src = 1;
            end
        endcase
    end
endmodule
```

### Control Signal Truth Table

| Instruction | RegWrite | ALUSrc | MemWrite | MemRead | MemToReg | Branch | ALUOp |
|-------------|----------|--------|----------|---------|----------|--------|-------|
| R-type      | 1 | 0 | 0 | 0 | 0 | 0 | 10 |
| I-type ALU  | 1 | 1 | 0 | 0 | 0 | 0 | 10 |
| LW          | 1 | 1 | 0 | 1 | 1 | 0 | 00 |
| SW          | 0 | 1 | 1 | 0 | 0 | 0 | 00 |
| BEQ/BNE     | 0 | 0 | 0 | 0 | 0 | 1 | 01 |
| LUI         | 1 | 1 | 0 | 0 | 0 | 0 | 00 |

---

## Step 9: Top-Level — Wire Everything Together

```verilog
module riscv_single_cycle (
    input wire clk,
    input wire rst
);
    // ----- Internal wires -----
    wire [31:0] pc, pc_next, pc_plus4, branch_target;
    wire [31:0] instr;
    wire [31:0] rd1, rd2, wd;
    wire [31:0] imm;
    wire [31:0] alu_src_b;
    wire [31:0] alu_result;
    wire [31:0] mem_rd;
    wire        zero;

    // Control signals
    wire        branch, mem_read, mem_to_reg;
    wire        mem_write, alu_src, reg_write;
    wire [1:0]  alu_op;
    wire [3:0]  alu_ctrl;
    wire        pc_src;

    // ----- PC logic -----
    assign pc_plus4      = pc + 32'd4;
    assign branch_target = pc + imm;
    assign pc_src        = branch & zero;          // BEQ uses zero flag
    assign pc_next       = pc_src ? branch_target : pc_plus4;

    // ----- Module instantiations -----
    pc_reg PC (
        .clk(clk), .rst(rst),
        .pc_next(pc_next), .pc(pc)
    );

    imem IMEM (
        .addr(pc), .instr(instr)
    );

    control_unit CTRL (
        .opcode(instr[6:0]),
        .branch(branch), .mem_read(mem_read),
        .mem_to_reg(mem_to_reg), .alu_op(alu_op),
        .mem_write(mem_write), .alu_src(alu_src),
        .reg_write(reg_write)
    );

    regfile RF (
        .clk(clk), .we(reg_write),
        .rs1(instr[19:15]), .rs2(instr[24:20]),
        .rd(instr[11:7]),   .wd(wd),
        .rd1(rd1),          .rd2(rd2)
    );

    imm_gen IMMGEN (
        .instr(instr), .imm(imm)
    );

    // ALUSrc MUX: choose register or immediate as second ALU operand
    assign alu_src_b = alu_src ? imm : rd2;

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
        .clk(clk), .we(mem_write),
        .addr(alu_result), .wd(rd2),
        .rd(mem_rd)
    );

    // WB MUX: choose memory data or ALU result to write back
    assign wd = mem_to_reg ? mem_rd : alu_result;

endmodule
```

---

## Step 10: Testbench

Write a testbench that loads a small program and checks register values.

```verilog
module tb_riscv;
    reg clk, rst;

    riscv_single_cycle uut (.clk(clk), .rst(rst));

    // 10ns clock
    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("riscv.vcd");
        $dumpvars(0, tb_riscv);

        rst = 1; #12;
        rst = 0;

        // Run 50 cycles
        #500;

        // Check register x1 (should be 10 after ADDI x1, x0, 10)
        $display("x1 = %0d (expect 10)", uut.RF.regs[1]);
        // Check register x2 (should be 20 after ADDI x2, x0, 20)
        $display("x2 = %0d (expect 20)", uut.RF.regs[2]);
        // Check register x3 (should be 30 after ADD x3, x1, x2)
        $display("x3 = %0d (expect 30)", uut.RF.regs[3]);

        $finish;
    end
endmodule
```

### Sample Program (program.hex)

This program adds two numbers and stores the result in memory:

```
# Assembly:
# addi x1, x0, 10    # x1 = 10
# addi x2, x0, 20    # x2 = 20
# add  x3, x1, x2    # x3 = 30
# sw   x3, 0(x0)     # mem[0] = 30
# lw   x4, 0(x0)     # x4 = mem[0] = 30

# Hex encoding (RV32I):
00A00093   # addi x1, x0, 10
01400113   # addi x2, x0, 20
002081B3   # add  x3, x1, x2
00302023   # sw   x3, 0(x0)
00002203   # lw   x4, 0(x0)
```

Save this as `program.hex` and it will be loaded by `$readmemh`.

---

## How to Simulate

### Using Icarus Verilog (free):
```bash
# Compile
iverilog -o riscv_sim \
    riscv_single_cycle.v pc_reg.v imem.v regfile.v \
    imm_gen.v alu.v alu_control.v dmem.v \
    control_unit.v tb_riscv.v

# Run simulation
vvp riscv_sim

# View waveform
gtkwave riscv.vcd
```

### Using EDA Playground (browser, free):
1. Go to [edaplayground.com](https://edaplayground.com)
2. Paste each module into separate files
3. Select **Icarus Verilog** as the simulator
4. Click **Run**

---

## Instruction Execution — Step by Step

Let's trace `ADD x3, x1, x2` through the datapath:

```
1. PC = 0x08  →  IMEM fetches 0x002081B3

2. Control Unit sees opcode=0110011 (R-type):
   RegWrite=1, ALUSrc=0, MemWrite=0, MemToReg=0, ALUOp=10

3. Register File reads:
   rs1 = x1 = 10
   rs2 = x2 = 20

4. ALUSrc MUX: selects rs2 (ALUSrc=0) → ALU input B = 20

5. ALU Control: funct3=000, funct7[5]=0 → ALU_ADD
   ALU: 10 + 20 = 30, zero=0

6. DMEM: not accessed (MemWrite=0, MemRead=0)

7. WB MUX: selects ALU result (MemToReg=0) → WD = 30

8. Register File writes: rd=x3 ← 30 (RegWrite=1)

9. PC: branch=0, so pc_next = PC+4 = 0x0C
```

---

## Common Mistakes and Fixes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Writing to x0 in RegFile | x0 becomes non-zero | Add `if (rd != 0)` guard |
| Missing sign extension in ImmGen | Wrong branch targets | Check all immediate formats carefully |
| Using blocking `=` in sequential blocks | Race conditions | Use `<=` in `always @(posedge clk)` |
| Word vs byte addressing in memory | Wrong data read/written | Use `addr[9:2]` for word-addressed memory |
| ALUSrc MUX wrong way round | ALU always gets immediate | Check MUX select polarity |

---

## What's Next — Pipelining

The single cycle processor is the foundation. The natural next step is a **5-stage pipeline**:

```
IF  →  ID  →  EX  →  MEM  →  WB
```

Pipelining overlaps execution of multiple instructions, achieving near 1 instruction per cycle — but introduces **hazards** (data hazards, control hazards) that require forwarding and stalling logic.

Stay tuned for the pipeline tutorial.

---

## Complete File List

```
riscv_single_cycle/
├── pc_reg.v          ← Program Counter
├── imem.v            ← Instruction Memory
├── regfile.v         ← Register File (32×32)
├── imm_gen.v         ← Immediate Generator
├── alu.v             ← ALU (10 operations)
├── alu_control.v     ← ALU Control Decoder
├── dmem.v            ← Data Memory
├── control_unit.v    ← Main Control Unit
├── riscv_single_cycle.v  ← Top-level (wires everything)
├── tb_riscv.v        ← Testbench
└── program.hex       ← Test program
```

---

*Want a printable RISC-V instruction set cheat sheet? Check the [Shop](/shop) for the RTL Design Guide PDF.*
