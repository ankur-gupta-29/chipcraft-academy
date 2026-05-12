// Testbench: verifies imm_gen for all 5 instruction formats
// Checks bit counts AND actual sign-extension values
module tb_imm_gen;
    reg  [31:0] instr;
    wire [31:0] imm;
    integer errors = 0;

    imm_gen uut (.instr(instr), .imm(imm));

    task check;
        input [31:0] got;
        input [31:0] expected;
        input [127:0] label;
        begin
            if (got !== expected) begin
                $display("FAIL [%0s]: got=%08h expected=%08h", label, got, expected);
                errors = errors + 1;
            end else
                $display("PASS [%0s]: imm=%08h", label, got);
        end
    endtask

    initial begin
        // ── I-type: ADDI x1, x0, 10  (imm=10=0x00A) ──────────────
        // instr = imm[11:0] | rs1 | funct3 | rd | opcode
        // imm=0x00A(12b), rs1=0, funct3=0, rd=1, opcode=0010011
        instr = 32'b000000001010_00000_000_00001_0010011; #1;
        check(imm, 32'h0000_000A, "ADDI x1,x0,10");

        // ── I-type: ADDI with negative imm (-1 = 0xFFF) ───────────
        instr = 32'b111111111111_00000_000_00001_0010011; #1;
        check(imm, 32'hFFFF_FFFF, "ADDI x1,x0,-1");

        // ── S-type: SW x3, 4(x0)  (imm=4=0x004) ──────────────────
        // S-type: instr[31:25]=imm[11:5], instr[11:7]=imm[4:0]
        // imm=4 → imm[11:5]=0000000, imm[4:0]=00100
        instr = 32'b0000000_00011_00000_010_00100_0100011; #1;
        check(imm, 32'h0000_0004, "SW x3,4(x0)");

        // ── S-type: negative offset SW x3,-4(x0) (imm=-4=0xFFC) ──
        // imm=-4=0xFFC → imm[11:5]=1111111, imm[4:0]=11100
        instr = 32'b1111111_00011_00000_010_11100_0100011; #1;
        check(imm, 32'hFFFF_FFFC, "SW x3,-4(x0)");

        // ── B-type: BEQ, offset=+8 ────────────────────────────────
        // imm=8 → imm[12]=0,imm[11]=0,imm[10:5]=000000,imm[4:1]=0100
        // instr[31]=imm[12]=0, instr[7]=imm[11]=0
        // instr[30:25]=imm[10:5]=000000, instr[11:8]=imm[4:1]=0100
        instr = 32'b0_000000_00000_00000_000_0100_0_1100011; #1;
        check(imm, 32'h0000_0008, "BEQ offset=+8");

        // ── U-type: LUI x1, 0x12345 ───────────────────────────────
        // imm = {0x12345, 12'b0} = 0x12345000
        instr = 32'b00010010001101000101_00001_0110111; #1;
        check(imm, 32'h1234_5000, "LUI 0x12345");

        // ── J-type: JAL offset=+4 ─────────────────────────────────
        // imm=4 → imm[20]=0,imm[19:12]=0,imm[11]=0,imm[10:1]=0000000010
        // instr[31]=0, instr[19:12]=00000000, instr[20]=0, instr[30:21]=0000000010
        instr = 32'b0_0000000010_0_00000000_00001_1101111; #1;
        check(imm, 32'h0000_0004, "JAL offset=+4");

        $display("──────────────────────────────");
        if (errors == 0)
            $display("ALL TESTS PASSED ✓ (%0d checks)", 7);
        else
            $display("FAILED: %0d error(s)", errors);
        $finish;
    end
endmodule
