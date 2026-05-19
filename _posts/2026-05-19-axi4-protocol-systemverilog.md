---
layout: post
title: "AXI4 Protocol in SystemVerilog — Complete Guide with RTL Examples"
description: "Master the AXI4 and AXI4-Lite bus protocols: 5 channels, VALID/READY handshake, write and read transactions, and a complete AXI4-Lite slave RTL implementation in SystemVerilog."
date: 2026-05-19
category: RTL Design
tags: [axi4, axi4-lite, systemverilog, bus-protocol, rtl, soc, interface, beginner, intermediate]
image: axi4-channels.svg
---

AXI4 (Advanced eXtensible Interface 4) is the ARM AMBA bus standard used in virtually every modern SoC — from your phone's processor to FPGA-based accelerators. Understanding AXI4 is essential for connecting IP blocks, designing memory-mapped peripherals, and integrating third-party IP.

---

## AXI4 Variants — Which One to Use?

| Variant | Bursts | Use Case |
|---------|--------|----------|
| **AXI4** (Full) | Up to 256 beats | High-performance: caches, DDR controllers, DMA |
| **AXI4-Lite** | Single beat only | Low-throughput: register maps, CSRs, peripherals |
| **AXI4-Stream** | No address channel | Streaming data: video, DSP, network packets |

**Rule of thumb:** Use AXI4-Lite for register-mapped peripherals (the vast majority of cases). Use AXI4 full only when you need bursts for bandwidth efficiency.

---

## The 5 Independent Channels

AXI4 splits every transaction across 5 separate channels, each with its own VALID/READY handshake. This decoupling allows the master and slave to pipeline transactions independently.

<img src="{{ '/assets/images/axi4-channels.svg' | relative_url }}" alt="AXI4 five channels diagram" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

| Channel | Direction | Signals | Purpose |
|---------|-----------|---------|---------|
| **AW** | Master → Slave | AWADDR, AWLEN, AWSIZE, AWBURST, AWVALID, AWREADY | Write address + burst info |
| **W** | Master → Slave | WDATA, WSTRB, WLAST, WVALID, WREADY | Write data |
| **B** | Slave → Master | BRESP, BVALID, BREADY | Write response (OK/error) |
| **AR** | Master → Slave | ARADDR, ARLEN, ARSIZE, ARBURST, ARVALID, ARREADY | Read address + burst info |
| **R** | Slave → Master | RDATA, RRESP, RLAST, RVALID, RREADY | Read data |

**Key insight:** The AW, W, and B channels are independent. A master can send the write address and write data simultaneously — it doesn't have to send AW first.

---

## The VALID/READY Handshake

Every AXI4 channel uses the same handshake protocol: **a transfer occurs on the rising clock edge when both VALID and READY are HIGH simultaneously.**

<img src="{{ '/assets/images/axi4-handshake.svg' | relative_url }}" alt="AXI4 VALID/READY handshake waveform" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

**Critical rules (from ARM AXI spec):**

```
Rule 1: The source (VALID sender) must NOT wait for READY before asserting VALID.
        → Master cannot hold VALID low until it sees READY=1 from slave.
        → Slave cannot hold READY low until it sees VALID=1 from master.
        (Either is a deadlock if both wait for each other.)

Rule 2: Once VALID is asserted, it must stay HIGH until the transfer completes.
        → You cannot deassert VALID mid-transaction.

Rule 3: READY can be asserted before, with, or after VALID — all are legal.
```

```systemverilog
// Correct: assert VALID independently of READY
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)       awvalid <= 1'b0;
    else if (start)   awvalid <= 1'b1;               // assert when ready to send
    else if (awready) awvalid <= 1'b0;               // deassert after handshake
end

// Transfer detection — use this everywhere
wire aw_transfer = awvalid & awready;  // both high this cycle
```

---

## AXI4-Lite Signal List

AXI4-Lite is AXI4 without bursts. Fixed data width (32 or 64 bit). No ID fields. No exclusive access. Perfect for register maps.

```systemverilog
// AXI4-Lite Slave port (32-bit data, 32-bit address)
module axi4_lite_slave #(
    parameter ADDR_W = 32,
    parameter DATA_W = 32,
    parameter N_REGS = 8          // number of 32-bit registers
)(
    input  logic                 clk,
    input  logic                 rst_n,
    // Write Address Channel
    input  logic [ADDR_W-1:0]   s_awaddr,
    input  logic                 s_awvalid,
    output logic                 s_awready,
    // Write Data Channel
    input  logic [DATA_W-1:0]   s_wdata,
    input  logic [DATA_W/8-1:0] s_wstrb,     // byte enables
    input  logic                 s_wvalid,
    output logic                 s_wready,
    // Write Response Channel
    output logic [1:0]           s_bresp,     // 2'b00 = OKAY
    output logic                 s_bvalid,
    input  logic                 s_bready,
    // Read Address Channel
    input  logic [ADDR_W-1:0]   s_araddr,
    input  logic                 s_arvalid,
    output logic                 s_arready,
    // Read Data Channel
    output logic [DATA_W-1:0]   s_rdata,
    output logic [1:0]           s_rresp,     // 2'b00 = OKAY
    output logic                 s_rvalid,
    input  logic                 s_rready
);
```

---

## Write Transaction — Step by Step

A write transaction uses AW + W + B channels:

```
Cycle 1: Master drives AWADDR + AWVALID=1, WDATA + WVALID=1 (simultaneously)
Cycle 2: Slave asserts AWREADY=1, WREADY=1 → both channels handshake
Cycle 3: Slave drives BRESP=OKAY + BVALID=1
Cycle 4: Master asserts BREADY=1 → write response handshake complete
```

```systemverilog
// ── Write transaction state machine ──────────────────────────────────────
typedef enum logic [1:0] {
    WR_IDLE  = 2'b00,
    WR_DATA  = 2'b01,
    WR_RESP  = 2'b10
} wr_state_t;

wr_state_t wr_state;

// Latch write address
logic [ADDR_W-1:0] wr_addr;
logic              aw_done, w_done;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        wr_state  <= WR_IDLE;
        s_awready <= 1'b0;
        s_wready  <= 1'b0;
        s_bvalid  <= 1'b0;
        s_bresp   <= 2'b00;
        aw_done   <= 1'b0;
        w_done    <= 1'b0;
    end else begin
        case (wr_state)
            WR_IDLE: begin
                s_awready <= 1'b1;   // ready to accept address
                s_wready  <= 1'b1;   // ready to accept data
                s_bvalid  <= 1'b0;
                aw_done   <= 1'b0;
                w_done    <= 1'b0;

                if (s_awvalid && s_awready) begin
                    wr_addr <= s_awaddr;
                    aw_done <= 1'b1;
                    s_awready <= 1'b0;
                end
                if (s_wvalid && s_wready) begin
                    w_done <= 1'b1;
                    // Write to register file
                    // (see register write logic below)
                    s_wready <= 1'b0;
                end

                if ((aw_done || (s_awvalid && s_awready)) &&
                    (w_done  || (s_wvalid  && s_wready )))
                    wr_state <= WR_RESP;
            end

            WR_RESP: begin
                s_bvalid <= 1'b1;
                s_bresp  <= 2'b00;   // OKAY
                if (s_bvalid && s_bready) begin
                    s_bvalid <= 1'b0;
                    wr_state <= WR_IDLE;
                end
            end
            default: wr_state <= WR_IDLE;
        endcase
    end
end
```

---

## Read Transaction — Step by Step

A read uses AR + R channels only (no response channel — RRESP carries the status inline with data):

```
Cycle 1: Master drives ARADDR + ARVALID=1
Cycle 2: Slave asserts ARREADY=1 → address handshake
Cycle 3: Slave drives RDATA + RRESP=OKAY + RVALID=1
Cycle 4: Master asserts RREADY=1 → data handshake complete
```

```systemverilog
// ── Read transaction ─────────────────────────────────────────────────────
typedef enum logic {
    RD_IDLE = 1'b0,
    RD_DATA = 1'b1
} rd_state_t;

rd_state_t rd_state;
logic [ADDR_W-1:0] rd_addr;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        rd_state  <= RD_IDLE;
        s_arready <= 1'b0;
        s_rvalid  <= 1'b0;
        s_rresp   <= 2'b00;
        s_rdata   <= '0;
    end else begin
        case (rd_state)
            RD_IDLE: begin
                s_arready <= 1'b1;
                s_rvalid  <= 1'b0;
                if (s_arvalid && s_arready) begin
                    rd_addr   <= s_araddr;
                    s_arready <= 1'b0;
                    rd_state  <= RD_DATA;
                end
            end

            RD_DATA: begin
                s_rvalid <= 1'b1;
                s_rresp  <= 2'b00;   // OKAY
                // Drive read data from register file
                s_rdata  <= reg_file[rd_addr[ADDR_W-1:2]]; // word-addressed
                if (s_rvalid && s_rready) begin
                    s_rvalid <= 1'b0;
                    rd_state <= RD_IDLE;
                end
            end
            default: rd_state <= RD_IDLE;
        endcase
    end
end
```

---

## Complete AXI4-Lite Slave — Register File

Putting it all together: a parametric register-mapped peripheral with 8 × 32-bit registers:

```systemverilog
// Register file storage
logic [DATA_W-1:0] reg_file [0:N_REGS-1];

// ── Register write with byte strobes ─────────────────────────────────────
function automatic void write_reg(
    input logic [ADDR_W-1:0]   addr,
    input logic [DATA_W-1:0]   data,
    input logic [DATA_W/8-1:0] strb
);
    integer idx;
    idx = addr[ADDR_W-1:2];          // word index (ignore byte offset)
    if (idx < N_REGS) begin
        for (int b = 0; b < DATA_W/8; b++) begin
            if (strb[b])
                reg_file[idx][b*8 +: 8] <= data[b*8 +: 8];
        end
    end
endfunction

// Called from write state machine when w_done and aw_done both asserted:
// write_reg(wr_addr, s_wdata, s_wstrb);

// ── Initialise registers ──────────────────────────────────────────────────
integer i;
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        for (i = 0; i < N_REGS; i++) reg_file[i] <= '0;
end
```

---

## BRESP and RRESP Response Codes

```systemverilog
// AXI4 response codes
localparam RESP_OKAY   = 2'b00;  // Transaction OK
localparam RESP_EXOKAY = 2'b01;  // Exclusive access OK (AXI4 full only)
localparam RESP_SLVERR = 2'b10;  // Slave error (address out of range etc.)
localparam RESP_DECERR = 2'b11;  // Decode error (no slave at this address)

// Return SLVERR for out-of-range address
assign s_bresp = (wr_addr[ADDR_W-1:2] < N_REGS) ? RESP_OKAY : RESP_SLVERR;
assign s_rresp = (rd_addr[ADDR_W-1:2] < N_REGS) ? RESP_OKAY : RESP_SLVERR;
```

---

## AXI4 Burst Transaction (Full AXI4 Only)

For AXI4 full, masters can transfer up to 256 beats in a single transaction:

```systemverilog
// AWLEN=7 means 8 beats (AWLEN+1)
// AWSIZE=2 means 4 bytes per beat (2^AWSIZE)
// AWBURST=01 means INCR (address increments each beat)

// Beat count tracking
logic [7:0] burst_cnt;

always_ff @(posedge clk) begin
    if (aw_transfer) begin
        burst_cnt <= s_awlen;          // load burst length
    end else if (w_transfer) begin
        burst_cnt <= burst_cnt - 1;
        if (s_wlast) begin             // WLAST asserted on final beat
            // burst complete
        end
    end
end

// AWBURST encoding:
// 2'b00 = FIXED  — address stays the same (FIFOs)
// 2'b01 = INCR   — address increments (normal memory)
// 2'b10 = WRAP   — address wraps at boundary (cache lines)
```

---

## Common AXI4 Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Master waits for READY before asserting VALID | Potential deadlock | Assert VALID immediately when data is ready |
| Deasserting VALID before handshake completes | Protocol violation — slave may miss data | Keep VALID high until READY seen |
| Ignoring WSTRB | Wrong bytes written | Always apply byte-enable mask |
| Forgetting WLAST on burst final beat | Slave never knows burst is done | Assert WLAST when burst_cnt == 0 |
| Using ARADDR without waiting for ARREADY | May lose address | Latch address only on valid+ready handshake |
| Not returning BRESP before accepting next AW | Back-pressure violation | Complete B channel before next write |

---

## AXI4 Verification Checklist

```systemverilog
// SVA assertions for AXI4 protocol compliance
// VALID must not drop without handshake
property valid_stable (valid, ready);
    @(posedge clk) disable iff (!rst_n)
    (valid && !ready) |=> valid;  // once asserted, stays until ready
endproperty

assert property (valid_stable(s_awvalid, s_awready)) else
    $error("AWVALID dropped without handshake!");

assert property (valid_stable(s_wvalid, s_wready)) else
    $error("WVALID dropped without handshake!");

assert property (valid_stable(s_arvalid, s_arready)) else
    $error("ARVALID dropped without handshake!");
```

---

## What's Next

- **[RTL Pipelining]({{ '/blog/2026/05/17/pipeline-rtl-design/' | relative_url }})** — pipeline the datapath that drives AXI transactions
- **[SystemVerilog Assertions (SVA)]({{ '/blog/2026/05/13/systemverilog-assertions-sva-guide/' | relative_url }})** — write protocol compliance checks for AXI
- **[Clock Domain Crossing]({{ '/blog/2026/05/17/clock-domain-crossing/' | relative_url }})** — handle AXI master and slave in different clock domains
