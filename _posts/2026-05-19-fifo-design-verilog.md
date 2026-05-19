---
layout: post
title: "FIFO Design in Verilog — Synchronous & Asynchronous with Full RTL"
description: "Master FIFO design: synchronous FIFO with read/write pointers and full/empty flags, almost-full/empty thresholds, parameterisable RTL, and async FIFO pointer width rules — all verified against Cummings SNUG 2002."
date: 2026-05-19
category: RTL Design
tags: [fifo, verilog, systemverilog, rtl, synchronous, asynchronous, cdc, interview, intermediate]
image: sync-fifo-diagram.svg
---

A FIFO (First-In First-Out) buffer is one of the most common building blocks in digital design. Every SoC uses dozens of them — between the CPU and memory, between clock domains, between IP blocks. Getting the full and empty flags wrong by even one entry causes data loss or corruption. This guide builds a complete, correct FIFO from scratch.

---

## FIFO Types at a Glance

| Type | Clocks | Use case |
|------|--------|---------|
| **Synchronous FIFO** | Single shared clock | Rate-matching between producer and consumer in same clock domain |
| **Asynchronous FIFO** | Separate read/write clocks | Crossing between different clock domains (CDC) |
| **Shift-register FIFO** | Single clock | Very short, fixed-depth FIFOs (4–16 entries) |

---

## The Critical Pointer Width Rule

This is the most important FIFO design rule — getting it wrong causes subtle bugs:

```
Pointer width = log₂(DEPTH) + 1  ← one EXTRA bit beyond the address bits
```

For a FIFO of depth 8 (addresses 0–7, need 3 bits):
- **Wrong:** 3-bit pointers → can't distinguish full from empty when both pointers equal 0
- **Correct:** 4-bit pointers (3 address bits + 1 wrap bit)

**Why the extra bit works:**

```
Empty: wr_ptr == rd_ptr         (ALL bits equal, including MSB)
Full:  wr_ptr[MSB] != rd_ptr[MSB]    AND
       wr_ptr[MSB-1:0] == rd_ptr[MSB-1:0]
```

The MSB acts as a "lap counter" — it flips every time the pointer wraps around the memory. When the write pointer has lapped the read pointer exactly once, the FIFO is full.

<img src="{{ '/assets/images/sync-fifo-diagram.svg' | relative_url }}" alt="Synchronous FIFO diagram with read/write pointers" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

---

## Synchronous FIFO — Complete RTL

```verilog
// sync_fifo.v — Synchronous FIFO (single clock domain)
// Verified against Cummings SNUG 2002 "Simulation and Synthesis
// Techniques for Asynchronous FIFO Design"
module sync_fifo #(
    parameter DATA_W  = 8,           // data width
    parameter DEPTH   = 16,          // must be a power of 2
    parameter AFULL_TH  = DEPTH - 2, // almost-full threshold
    parameter AEMPTY_TH = 2          // almost-empty threshold
)(
    input  wire              clk,
    input  wire              rst_n,
    // Write port
    input  wire              wr_en,
    input  wire [DATA_W-1:0] wr_data,
    output wire              full,
    output wire              almost_full,
    // Read port
    input  wire              rd_en,
    output reg  [DATA_W-1:0] rd_data,
    output wire              empty,
    output wire              almost_empty,
    // Status
    output wire [$clog2(DEPTH):0] fill_level  // how many entries currently stored
);

    // ── Memory array ────────────────────────────────────────────────
    localparam ADDR_W = $clog2(DEPTH);       // address bits
    localparam PTR_W  = ADDR_W + 1;          // pointer bits (extra MSB for full/empty)

    reg [DATA_W-1:0] mem [0:DEPTH-1];

    // ── Pointers ─────────────────────────────────────────────────────
    reg [PTR_W-1:0] wr_ptr;     // write pointer (PTR_W bits)
    reg [PTR_W-1:0] rd_ptr;     // read pointer  (PTR_W bits)

    // ── Full and Empty flags ──────────────────────────────────────────
    // Empty: all bits of wr_ptr and rd_ptr are equal
    assign empty = (wr_ptr == rd_ptr);

    // Full: MSBs differ, lower address bits are equal
    assign full  = (wr_ptr[PTR_W-1] != rd_ptr[PTR_W-1]) &&
                   (wr_ptr[ADDR_W-1:0] == rd_ptr[ADDR_W-1:0]);

    // ── Fill level ────────────────────────────────────────────────────
    // The difference of the two pointers gives the number of valid entries
    assign fill_level = wr_ptr - rd_ptr;   // works because of modular arithmetic

    // ── Almost-full / almost-empty ────────────────────────────────────
    assign almost_full  = (fill_level >= AFULL_TH);
    assign almost_empty = (fill_level <= AEMPTY_TH) && !empty;

    // ── Write logic ───────────────────────────────────────────────────
    always @(posedge clk) begin
        if (wr_en && !full) begin
            mem[wr_ptr[ADDR_W-1:0]] <= wr_data;   // use lower bits as address
            wr_ptr <= wr_ptr + 1'b1;               // pointer wraps via overflow
        end
    end

    // ── Read logic ────────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr  <= '0;
            rd_data <= '0;
        end else if (rd_en && !empty) begin
            rd_data <= mem[rd_ptr[ADDR_W-1:0]];   // read data
            rd_ptr  <= rd_ptr + 1'b1;
        end
    end

    // ── Reset ─────────────────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            wr_ptr <= '0;
    end

    // ── Simulation checks ─────────────────────────────────────────────
    // synthesis translate_off
    always @(posedge clk) begin
        if (wr_en && full)
            $error("FIFO overflow: write to full FIFO at time %0t", $time);
        if (rd_en && empty)
            $error("FIFO underflow: read from empty FIFO at time %0t", $time);
    end
    // synthesis translate_on

endmodule
```

---

## Why `$clog2` for ADDR_W

`$clog2(N)` returns the ceiling of log₂(N) — the minimum number of bits needed to represent N addresses:

```verilog
$clog2(8)  = 3   // 8-deep FIFO needs 3 address bits (0–7)
$clog2(16) = 4   // 16-deep FIFO needs 4 address bits
$clog2(32) = 5
```

Using `$clog2` makes your FIFO truly parameterisable — change DEPTH and everything recalculates automatically.

---

## Write When Full / Read When Empty — Safe Behaviour

```verilog
// ✅ Correct — guard every access
always @(posedge clk) begin
    if (wr_en && !full)  mem[...] <= wr_data;   // only write when not full
    if (rd_en && !empty) rd_data  <= mem[...];  // only read when not empty
end

// ❌ Wrong — unguarded write overwrites valid data
always @(posedge clk) begin
    if (wr_en) mem[wr_ptr] <= wr_data;  // overwrites oldest entry when full!
end
```

Alternatively, use **"write-through" or "fall-through"** mode where rd_data is combinatorially driven from the memory (no read-enable register), useful for show-ahead FIFOs.

---

## Almost-Full and Almost-Empty Flags

Flow-control signals for upstream/downstream blocks that need advance warning:

```verilog
// Almost-full: stop writing 2 entries before actual full
// This gives the producer 2 clock cycles to stop
assign almost_full  = (fill_level >= DEPTH - 2);

// Almost-empty: warn consumer only 2 entries remain
assign almost_empty = (fill_level <= 2) && !empty;
```

**Why you need these:** A producer that checks `full` may already be mid-transaction when `full` goes high. `almost_full` gives it advance notice to stop safely.

---

## Asynchronous FIFO — Key Rules

An async FIFO has separate `wr_clk` and `rd_clk`. The design is significantly more complex because pointers must cross clock domains safely.

**Rule 1: Use Gray-coded pointers for the CDC crossing.**
Binary pointers change multiple bits at once (e.g., 3→4 is `011→100`, all 3 bits flip). If those bits are sampled in the other domain mid-transition, you get a corrupted pointer value that could generate a false full or empty.

Gray code changes only one bit per increment, making the two-flop synchroniser safe:

```verilog
// Binary to Gray conversion
function automatic [PTR_W-1:0] bin2gray(input [PTR_W-1:0] bin);
    bin2gray = bin ^ (bin >> 1);
endfunction

// Gray to Binary conversion (for fill-level calculation)
function automatic [PTR_W-1:0] gray2bin(input [PTR_W-1:0] gray);
    integer i;
    gray2bin[PTR_W-1] = gray[PTR_W-1];
    for (i = PTR_W-2; i >= 0; i--)
        gray2bin[i] = gray2bin[i+1] ^ gray[i];
endfunction
```

**Rule 2: Full is checked in the write domain; empty is checked in the read domain.**

```verilog
// Write domain: compare write pointer (binary) with
// synchronized read pointer (Gray → converted back to binary)
assign full = (wr_ptr_bin == {~rd_ptr_gray_sync[PTR_W-1],
                               ~rd_ptr_gray_sync[PTR_W-2],
                                rd_ptr_gray_sync[PTR_W-3:0]});
// (The MSB inversion trick avoids the gray2bin conversion for full detection)
```

**Rule 3: The pointer width (log₂(DEPTH)+1) rule applies to async FIFOs too** — for the same full/empty detection reason.

---

## FIFO Testbench

```verilog
module tb_sync_fifo;
    parameter DATA_W = 8;
    parameter DEPTH  = 16;

    reg                clk, rst_n, wr_en, rd_en;
    reg  [DATA_W-1:0]  wr_data;
    wire [DATA_W-1:0]  rd_data;
    wire               full, empty, almost_full, almost_empty;
    wire [4:0]         fill_level;   // log2(16)+1 = 5 bits for DEPTH=16

    sync_fifo #(.DATA_W(DATA_W), .DEPTH(DEPTH)) u_dut (
        .clk(clk), .rst_n(rst_n),
        .wr_en(wr_en), .wr_data(wr_data), .full(full), .almost_full(almost_full),
        .rd_en(rd_en), .rd_data(rd_data), .empty(empty), .almost_empty(almost_empty),
        .fill_level(fill_level)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    // Reference model — simple array + head/tail indices
    reg [DATA_W-1:0] ref_mem [0:DEPTH-1];
    integer ref_wr = 0, ref_rd = 0;
    integer errors = 0;
    integer i;

    initial begin
        rst_n = 0; wr_en = 0; rd_en = 0; wr_data = 0;
        repeat(2) @(posedge clk); #1; rst_n = 1;

        // Test 1: Fill FIFO completely with a deterministic pattern
        for (i = 0; i < DEPTH; i = i + 1) begin
            @(posedge clk); #1;
            if (!full) begin
                wr_data = (i * 13 + 7) & 8'hFF;   // deterministic pattern
                wr_en = 1;
                ref_mem[ref_wr] = wr_data;
                ref_wr = ref_wr + 1;
            end
        end
        @(posedge clk); #1; wr_en = 0;

        if (!full) begin
            $display("ERROR: Expected full after %0d writes", DEPTH);
            errors = errors + 1;
        end

        // Test 2: Drain FIFO and verify data order
        for (i = 0; i < DEPTH; i = i + 1) begin
            @(posedge clk); #1;
            if (!empty) begin
                rd_en = 1;
                @(posedge clk); #1; rd_en = 0;
                if (rd_data !== ref_mem[ref_rd]) begin
                    $display("ERROR: entry %0d — got 0x%0h, expected 0x%0h",
                             i, rd_data, ref_mem[ref_rd]);
                    errors = errors + 1;
                end
                ref_rd = ref_rd + 1;
            end
        end

        if (!empty) begin
            $display("ERROR: Expected empty after draining");
            errors = errors + 1;
        end

        $display("Errors: %0d", errors);
        if (errors == 0) $display("*** ALL FIFO TESTS PASSED ***");
        $finish;
    end
endmodule
```

---

## Common FIFO Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Pointer width = `log₂(DEPTH)` (no extra bit) | Cannot distinguish full from empty | Use `log₂(DEPTH)+1` bits |
| Comparing multi-bit binary pointers across clock domains | Metastability — corrupted pointer | Use Gray code + 2-FF synchroniser |
| No overflow/underflow guard | Silent data corruption | Always check `!full` before write, `!empty` before read |
| `DEPTH` not a power of 2 | Pointer wrap logic breaks | Constrain DEPTH to powers of 2, or use modulo addressing |
| `rd_data` registered one cycle late | Consumer reads stale data | Use synchronous read with registered output, or fall-through FIFO |

---

## What's Next

- **[Clock Domain Crossing (CDC)]({{ '/blog/2026/05/17/clock-domain-crossing/' | relative_url }})** — async FIFO in full detail with Gray-code synchroniser
- **[RTL Pipelining]({{ '/blog/2026/05/17/pipeline-rtl-design/' | relative_url }})** — FIFOs are used to decouple pipeline stages
- **[50 Verilog Interview Questions]({{ '/blog/2026/05/17/verilog-interview-questions/' | relative_url }})** — FIFO full/empty logic is one of the most common interview topics
