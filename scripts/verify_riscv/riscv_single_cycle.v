// ── PC Register ───────────────────────────────────────────────────────────────
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

// ── Instruction Memory ────────────────────────────────────────────────────────
module imem (
    input  wire [31:0] addr,
    output wire [31:0] instr
);
    reg [31:0] mem [0:255];
    initial $readmemh("program.hex", mem);
    assign instr = mem[addr[9:2]];
endmodule

// ── Register File ─────────────────────────────────────────────────────────────
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

    always @(posedge clk)
        if (we && rd != 5'b0) regs[rd] <= wd;

    assign rd1 = (rs1 == 5'b0) ? 32'b0 : regs[rs1];
    assign rd2 = (rs2 == 5'b0) ? 32'b0 : regs[rs2];
endmodule

// ── Immediate Generator ───────────────────────────────────────────────────────
module imm_gen (
    input  wire [31:0] instr,
    output reg  [31:0] imm
);
    wire [6:0] opcode = instr[6:0];
    always @(*) begin
        case (opcode)
            7'b0010011,
            7'b0000011,
            7'b1100111: imm = {{20{instr[31]}}, instr[31:20]};
            7'b0100011: imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};
            7'b1100011: imm = {{19{instr[31]}}, instr[31],
                                instr[7], instr[30:25], instr[11:8], 1'b0};
            7'b0110111,
            7'b0010111: imm = {instr[31:12], 12'b0};
            7'b1101111: imm = {{11{instr[31]}}, instr[31],
                                instr[19:12], instr[20], instr[30:21], 1'b0};
            default:    imm = 32'b0;
        endcase
    end
endmodule

// ── ALU ───────────────────────────────────────────────────────────────────────
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

// ── ALU Control ───────────────────────────────────────────────────────────────
module alu_control (
    input  wire [1:0] alu_op,
    input  wire [2:0] funct3,
    input  wire       funct7_5,
    output reg  [3:0] alu_ctrl
);
    always @(*) begin
        case (alu_op)
            2'b00: alu_ctrl = 4'd0;
            2'b01: alu_ctrl = 4'd1;
            2'b10: begin
                case (funct3)
                    3'b000: alu_ctrl = funct7_5 ? 4'd1 : 4'd0;
                    3'b001: alu_ctrl = 4'd7;
                    3'b010: alu_ctrl = 4'd5;
                    3'b011: alu_ctrl = 4'd6;
                    3'b100: alu_ctrl = 4'd4;
                    3'b101: alu_ctrl = funct7_5 ? 4'd9 : 4'd8;
                    3'b110: alu_ctrl = 4'd3;
                    3'b111: alu_ctrl = 4'd2;
                    default: alu_ctrl = 4'd0;
                endcase
            end
            default: alu_ctrl = 4'd0;
        endcase
    end
endmodule

// ── Data Memory ───────────────────────────────────────────────────────────────
module dmem (
    input  wire        clk,
    input  wire        we,
    input  wire [31:0] addr,
    input  wire [31:0] wd,
    output wire [31:0] rd
);
    reg [31:0] mem [0:255];
    integer j;
    initial for (j = 0; j < 256; j = j+1) mem[j] = 32'b0;

    always @(posedge clk)
        if (we) mem[addr[9:2]] <= wd;

    assign rd = mem[addr[9:2]];
endmodule

// ── Control Unit ──────────────────────────────────────────────────────────────
module control_unit (
    input  wire [6:0] opcode,
    output reg        branch,
    output reg  [1:0] result_src,
    output reg  [1:0] alu_op,
    output reg        mem_write,
    output reg        alu_src,
    output reg        reg_write
);
    always @(*) begin
        branch     = 1'b0;
        result_src = 2'b00;
        alu_op     = 2'b00;
        mem_write  = 1'b0;
        alu_src    = 1'b0;
        reg_write  = 1'b0;

        case (opcode)
            7'b0110011: begin               // R-type
                reg_write = 1'b1;
                alu_op    = 2'b10;
            end
            7'b0010011: begin               // I-type ALU
                reg_write = 1'b1;
                alu_src   = 1'b1;
                alu_op    = 2'b10;
            end
            7'b0000011: begin               // Load (LW)
                reg_write  = 1'b1;
                alu_src    = 1'b1;
                result_src = 2'b01;
            end
            7'b0100011: begin               // Store (SW)
                mem_write = 1'b1;
                alu_src   = 1'b1;
            end
            7'b1100011: begin               // Branch
                branch = 1'b1;
            end
            7'b0110111: begin               // LUI
                reg_write  = 1'b1;
                result_src = 2'b10;
            end
            default: ;
        endcase
    end
endmodule

// ── Top Level ─────────────────────────────────────────────────────────────────
module riscv_single_cycle (
    input wire clk,
    input wire rst
);
    wire [31:0] pc, pc_next, pc_plus4, branch_target;
    wire [31:0] instr;
    wire [31:0] rd1, rd2, wd;
    wire [31:0] imm;
    wire [31:0] alu_src_b;
    wire [31:0] alu_result;
    wire [31:0] mem_rd;
    wire        zero;

    wire        branch, mem_write, alu_src, reg_write;
    wire [1:0]  result_src, alu_op;
    wire [3:0]  alu_ctrl;

    // Branch comparator: evaluates rd1 vs rd2 directly for all 6 conditions
    wire beq  = (rd1 == rd2);
    wire blt  = ($signed(rd1) < $signed(rd2));
    wire bltu = (rd1 < rd2);

    reg branch_taken;
    always @(*) begin
        case (instr[14:12])
            3'b000: branch_taken = beq;
            3'b001: branch_taken = ~beq;
            3'b100: branch_taken = blt;
            3'b101: branch_taken = ~blt;
            3'b110: branch_taken = bltu;
            3'b111: branch_taken = ~bltu;
            default: branch_taken = 1'b0;
        endcase
    end

    assign pc_plus4      = pc + 32'd4;
    assign branch_target = pc + imm;
    assign pc_next       = (branch & branch_taken) ? branch_target : pc_plus4;

    // Writeback MUX: 00=ALU, 01=Mem data (LW), 10=Immediate (LUI)
    assign wd = (result_src == 2'b01) ? mem_rd :
                (result_src == 2'b10) ? imm    :
                                        alu_result;

    assign alu_src_b = alu_src ? imm : rd2;

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
