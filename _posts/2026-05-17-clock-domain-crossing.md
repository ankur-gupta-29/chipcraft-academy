---
layout: post
title: "Clock Domain Crossing (CDC) — Synchronizers, Metastability & Async FIFOs"
description: "Master CDC in digital design: what metastability is, two-flop synchronizer, pulse synchronizer, Gray-coded async FIFO — complete synthesisable Verilog with explanations and diagrams."
date: 2026-05-17
category: STA
tags: [cdc, clock-domain-crossing, metastability, synchronizer, async-fifo, gray-code, verilog, sta]
image: /assets/images/cdc-two-flop-synchronizer.svg
---

STA can analyse paths within a single clock domain. But when a signal crosses from one clock domain to another — different frequencies, different sources, no guaranteed phase relationship — STA gives up. That's where Clock Domain Crossing (CDC) analysis and safe crossing techniques take over. This guide covers every technique you need for production-quality RTL.

---

## What Is a Clock Domain Crossing?

A CDC occurs when a signal driven by flip-flops in domain A is sampled by flip-flops in domain B, where A and B are driven by **unrelated clocks** (different PLLs, different frequencies, or same frequency but unknown phase).

```
clk_a domain:  clk_a ──► FF_src ──┐
                                   │ ← CDC crossing (danger zone)
clk_b domain:  clk_b ──► FF_dst ◄─┘
```

**Why is this dangerous?**
- STA assumes clocks have a known phase relationship. Unrelated clocks have none.
- STA may calculate false paths as if they're synchronous → miss violations.
- The real hazard is **metastability**.

---

## Metastability — What Actually Happens

When a flip-flop's setup or hold requirement is violated (which always happens in an asynchronous crossing), its output can enter a **metastable state** — neither logic 0 nor logic 1 — and float there for an unpredictable time.

```
Normal capture:  D changes → clock edge → Q settles to 0 or 1 (in Tcq)

Metastable:      D changes near clock edge → Q floats between 0 and 1
                 → eventually resolves, but timing is unpredictable
```

You **cannot eliminate** metastability in a CDC crossing. You can only reduce the probability that it persists long enough to cause errors, using synchronizers that give the output time to resolve before it's sampled again.

**MTBF (Mean Time Between Failures):**
```
MTBF = exp(Tw / τ) / (f_dest × f_src × Θ)
```
Where `Tw` is the resolution window, `τ` is the FF's time constant (~0.1 ns for modern processes), and `Θ` is a process parameter. Adding a second flop multiplies MTBF exponentially.

---

## Solution 1 — Two-Flop Synchronizer (Single-Bit)

The fundamental CDC solution: two flip-flops back-to-back in the destination domain.

<img src="{{ '/assets/images/cdc-two-flop-synchronizer.svg' | relative_url }}" alt="Two-flop synchronizer circuit" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

```verilog
// two_ff_sync.v — parameterisable two-flop synchronizer
module two_ff_sync #(
    parameter STAGES = 2   // 2 = standard; 3 for very fast clocks
)(
    input  wire clk_dst,   // destination clock
    input  wire rst_n,     // active-low async reset (in clk_dst domain)
    input  wire data_src,  // single-bit signal from source domain
    output wire data_sync  // synchronised output, safe in clk_dst
);
    reg [STAGES-1:0] sync_reg;

    always @(posedge clk_dst or negedge rst_n) begin
        if (!rst_n)
            sync_reg <= {STAGES{1'b0}};
        else
            sync_reg <= {sync_reg[STAGES-2:0], data_src};
    end

    assign data_sync = sync_reg[STAGES-1];

endmodule
```

**Why two stages?** The first FF may go metastable — but it has one full clk_dst period to resolve before the second FF samples it. This gives exponentially lower probability of propagating an indeterminate value.

> **Critical:** Only use the two-flop synchronizer for **single-bit** signals. Multi-bit buses need a different approach.

---

## The Multi-Bit Problem

If you naively synchronize a multi-bit bus bit-by-bit:

```verilog
// ❌ WRONG — bits may resolve at different times!
two_ff_sync sync_bit0(.data_src(data[0]), .data_sync(data_sync[0]), ...);
two_ff_sync sync_bit1(.data_src(data[1]), .data_sync(data_sync[1]), ...);
two_ff_sync sync_bit2(.data_src(data[2]), .data_sync(data_sync[2]), ...);
// data_sync[0:2] may all be from DIFFERENT source values — corrupted!
```

Each bit independently resolves from metastability, so you can read a combination of old and new values.

**The solutions:**

| Method | When to use |
|--------|------------|
| Gray code + 2-FF sync | Counters that increment by 1 (FIFO pointers) |
| Async FIFO | High-bandwidth multi-bit data streams |
| Handshake (req/ack) | Infrequent control bus transfers |
| MCP (multi-cycle path) | Same frequency, known phase relationship |

---

## Solution 2 — Gray Code for Counters

Gray code: consecutive values differ by exactly **1 bit**. Safe to synchronize because at the moment of crossing, at most 1 bit is changing — eliminating the multi-bit glitch problem.

```verilog
// gray_counter.v — 4-bit Gray counter for FIFO pointers
module gray_counter #(parameter WIDTH = 4)(
    input  wire             clk, rst_n,
    output reg  [WIDTH-1:0] gray_out,
    output reg  [WIDTH-1:0] bin_out
);
    wire [WIDTH-1:0] bin_next = bin_out + 1'b1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bin_out  <= 0;
            gray_out <= 0;
        end else begin
            bin_out  <= bin_next;
            gray_out <= (bin_next >> 1) ^ bin_next;  // binary-to-Gray
        end
    end
endmodule
```

Binary-to-Gray: `gray[i] = bin[i] XOR bin[i+1]` (MSB unchanged).
Gray-to-Binary: `bin[i] = XOR of gray[i], gray[i+1], ... gray[MSB]`.

---

## Solution 3 — Async FIFO

The standard solution for transferring a stream of multi-bit data across a clock boundary.

<img src="{{ '/assets/images/cdc-async-fifo.svg' | relative_url }}" alt="Async FIFO block diagram with Gray-coded pointers" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

```verilog
// async_fifo.v — complete synthesisable async FIFO
module async_fifo #(
    parameter DATA_W = 8,
    parameter DEPTH  = 16   // must be power of 2
)(
    // Write port
    input  wire              wclk, wrst_n,
    input  wire              wren,
    input  wire [DATA_W-1:0] wdata,
    output wire              wfull,

    // Read port
    input  wire              rclk, rrst_n,
    input  wire              rren,
    output wire [DATA_W-1:0] rdata,
    output wire              rempty
);
    localparam ADDR_W = $clog2(DEPTH);

    // Memory array
    reg [DATA_W-1:0] mem [0:DEPTH-1];

    // Write-side binary and Gray pointers
    reg  [ADDR_W:0] wptr_bin, rptr_gray_w;  // wptr has 1 extra bit for full detection
    wire [ADDR_W:0] wptr_bin_next = wptr_bin + (wren && !wfull);
    wire [ADDR_W:0] wptr_gray     = (wptr_bin_next >> 1) ^ wptr_bin_next;

    // Read-side binary and Gray pointers
    reg  [ADDR_W:0] rptr_bin, wptr_gray_r;
    wire [ADDR_W:0] rptr_bin_next = rptr_bin + (rren && !rempty);
    wire [ADDR_W:0] rptr_gray     = (rptr_bin_next >> 1) ^ rptr_bin_next;

    // ── Write domain ─────────────────────────────────────────────
    // Register wptr, write memory
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n)
            wptr_bin <= 0;
        else
            wptr_bin <= wptr_bin_next;
    end

    always @(posedge wclk) begin
        if (wren && !wfull)
            mem[wptr_bin[ADDR_W-1:0]] <= wdata;
    end

    // Sync rptr_gray into write domain (2 FF sync)
    reg [ADDR_W:0] rptr_gray_w1, rptr_gray_w2;
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n)
            {rptr_gray_w2, rptr_gray_w1} <= 0;
        else
            {rptr_gray_w2, rptr_gray_w1} <= {rptr_gray_w1, rptr_gray};
    end

    // Full when Gray pointers match except MSBs differ
    assign wfull = (wptr_gray == {~rptr_gray_w2[ADDR_W:ADDR_W-1],
                                   rptr_gray_w2[ADDR_W-2:0]});

    // ── Read domain ──────────────────────────────────────────────
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n)
            rptr_bin <= 0;
        else
            rptr_bin <= rptr_bin_next;
    end

    assign rdata = mem[rptr_bin[ADDR_W-1:0]];

    // Sync wptr_gray into read domain (2 FF sync)
    reg [ADDR_W:0] wptr_gray_r1, wptr_gray_r2;
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n)
            {wptr_gray_r2, wptr_gray_r1} <= 0;
        else
            {wptr_gray_r2, wptr_gray_r1} <= {wptr_gray_r1, wptr_gray};
    end

    // Empty when Gray pointers are equal
    assign rempty = (rptr_gray == wptr_gray_r2);

endmodule
```

**Key design decisions:**
- Pointers are `ADDR_W + 1` bits wide (extra MSB distinguishes full from empty)
- Write pointer synchronised to read domain → empty detection
- Read pointer synchronised to write domain → full detection
- Only Gray-coded pointers cross clock domains — safe for 2-FF sync

---

## Solution 4 — Pulse Synchronizer (Handshake)

For infrequent control signals (configuration writes, interrupts):

```verilog
// pulse_sync.v — toggle-based pulse synchronizer
module pulse_sync (
    input  wire clk_src, rst_src,
    input  wire pulse_in,     // single-cycle pulse in clk_src domain
    input  wire clk_dst, rst_dst,
    output reg  pulse_out     // single-cycle pulse in clk_dst domain
);
    // Toggle FF in source domain
    reg toggle_src;
    always @(posedge clk_src or posedge rst_src) begin
        if (rst_src) toggle_src <= 0;
        else if (pulse_in) toggle_src <= ~toggle_src;
    end

    // 2-FF sync toggle into destination domain
    reg [2:0] sync_dst;
    always @(posedge clk_dst or posedge rst_dst) begin
        if (rst_dst) sync_dst <= 0;
        else         sync_dst <= {sync_dst[1:0], toggle_src};
    end

    // Edge detect on synchronised toggle
    always @(posedge clk_dst or posedge rst_dst) begin
        if (rst_dst) pulse_out <= 0;
        else         pulse_out <= sync_dst[2] ^ sync_dst[1];
    end
endmodule
```

**How it works:** The source pulse toggles a FF, turning a pulse into a level change. The level safely synchronises through 2 FFs. An edge detector on the output recreates the pulse in the destination domain.

---

## CDC Verification

CDC bugs are notoriously hard to catch in simulation (they require specific timing relationships). Use dedicated CDC tools:

| Tool | Vendor | What it checks |
|------|--------|---------------|
| SpyGlass CDC | Synopsys | Missing synchronizers, multi-bit crossings |
| VC CDC | Synopsys | Formal CDC verification |
| JasperGold CDC | Cadence | Formal + structural CDC |
| Conformal CDC | Cadence | RTL CDC analysis |

Typical CDC tool report output:
```
WARNING: cdc_signal 'data[7:0]' crosses from clk_a to clk_b with no synchronizer
ERROR:   multi-bit bus 'status[3:0]' uses per-bit 2FF sync — may sample mixed values
INFO:    'valid' uses 2FF sync — OK for single bit
```

---

## Common CDC Mistakes

| Mistake | Why it fails | Fix |
|---------|-------------|-----|
| Synchronizing multi-bit bus with per-bit 2FF | Bits resolve at different times — corrupted | Use async FIFO or Gray code |
| Using combinational output of metastable FF | Glitch propagates | Always register synchronizer output |
| Single-FF synchronizer | Not enough resolution time — still metastable | Always use minimum 2 FFs |
| Synchronizer clock = source clock | Defeats the purpose | Sync FFs MUST use destination clock |
| Reset across domains without sync | Reset glitch in destination domain | Sync reset across domains too |
| Forgetting `set_false_path` for CDC in SDC | STA analyses an impossible path | `set_false_path -from clk_a -to clk_b` |

---

## What's Next

- **[Setup & Hold Time — STA]({{ '/blog/2026/05/17/setup-hold-time-sta/' | relative_url }})** — understand the metastability hazard at the transistor level
- **[SDC Timing Constraints]({{ '/blog/2026/05/17/sdc-timing-constraints/' | relative_url }})** — use `set_false_path` and `set_clock_groups` to tell STA about your CDC paths
- **[FSM Design in Verilog]({{ '/blog/2026/05/17/fsm-design-verilog/' | relative_url }})** — apply these crossing techniques when FSMs span clock domains
