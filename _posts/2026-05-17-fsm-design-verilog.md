---
layout: post
title: "FSM Design in Verilog — Moore & Mealy with Full Examples"
description: "Learn finite state machine design in Verilog: Moore vs Mealy machines, 2-process and 3-process coding styles, safe-state design, gray and one-hot encoding — with complete synthesisable examples."
date: 2026-05-17
category: RTL Design
tags: [fsm, verilog, rtl, state-machine, moore, mealy, synthesis, beginner]
image: /assets/images/fsm-moore-diagram.svg
---

Finite State Machines appear in almost every digital design — from traffic lights and UART controllers to cache state machines in processors. Understanding how to code them correctly in Verilog is one of the most important RTL skills. This guide covers Moore and Mealy machines, three coding styles, and synthesis-safe patterns.

---

## What Is an FSM?

An FSM has three parts:

| Block | What it does | Logic type |
|-------|-------------|------------|
| **State register** | Remembers the current state | Sequential (flip-flops) |
| **Next-state logic** | Computes the next state from current state + inputs | Combinational |
| **Output logic** | Computes outputs from state (and inputs for Mealy) | Combinational |

```verilog
// Skeleton of any FSM
always @(posedge clk or posedge rst) begin   // state register
    if (rst) state <= IDLE;
    else     state <= next_state;
end

always @(*) begin   // next-state logic (combinational)
    case (state)
        IDLE: next_state = ...;
    endcase
end

always @(*) begin   // output logic (combinational)
    out = ...;
end
```

---

## Moore vs Mealy

| | Moore | Mealy |
|--|-------|-------|
| Output depends on | State only | State **+** inputs |
| Output timing | Registered — 1 cycle after state entry | Combinational — same cycle as input |
| Glitch risk | Low (registered output) | Higher (combinational path through inputs) |
| States needed | Usually more | Usually fewer |
| Use when | You want stable outputs | You need faster response |

<img src="{{ '/assets/images/fsm-moore-diagram.svg' | relative_url }}" alt="Moore FSM state diagram — traffic light" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

<img src="{{ '/assets/images/fsm-timing.svg' | relative_url }}" alt="Moore vs Mealy output timing comparison" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

---

## Moore FSM Example — Traffic Light Controller

A traffic light cycles RED → GREEN → YELLOW → RED. The output depends only on the state (Moore).

```verilog
// moore_traffic.v — 2-process Moore FSM
module moore_traffic (
    input  wire       clk, rst,
    input  wire [5:0] count,      // cycle counter driven externally
    output reg  [1:0] light       // 00=RED 01=GREEN 10=YELLOW
);

    // State encoding
    localparam RED    = 2'b00,
               GREEN  = 2'b01,
               YELLOW = 2'b10;

    reg [1:0] state, next_state;

    // --- Process 1: State register (sequential) ---
    always @(posedge clk or posedge rst) begin
        if (rst) state <= RED;
        else     state <= next_state;
    end

    // --- Process 2: Next-state + output logic (combinational) ---
    always @(*) begin
        // Defaults prevent latches
        next_state = state;
        light      = 2'b00;

        case (state)
            RED: begin
                light = 2'b00;
                if (count >= 30) next_state = GREEN;
            end
            GREEN: begin
                light = 2'b01;
                if (count >= 25) next_state = YELLOW;
            end
            YELLOW: begin
                light = 2'b10;
                if (count >= 5) next_state = RED;
            end
            default: begin       // ← safe-state: handle X/undefined
                light      = 2'b00;
                next_state = RED;
            end
        endcase
    end

endmodule
```

> **Key rule:** Always assign defaults before the `case` statement. This prevents accidental latches (the synthesiser infers a latch if a variable isn't assigned in every branch).

---

## Mealy FSM Example — "101" Sequence Detector

A Mealy machine detects the sequence `1-0-1` on a serial input. Output goes high the **same cycle** the sequence completes.

<img src="{{ '/assets/images/fsm-mealy-diagram.svg' | relative_url }}" alt="Mealy FSM — 101 sequence detector" style="width:100%;max-width:700px;display:block;margin:1.5rem auto;">

```verilog
// mealy_101_detect.v
module mealy_101_detect (
    input  wire clk, rst,
    input  wire din,
    output reg  detected   // high for 1 cycle when "101" seen
);

    localparam IDLE = 2'd0,
               S1   = 2'd1,   // saw '1'
               S10  = 2'd2,   // saw '10'
               S101 = 2'd3;   // saw '101' — output fires on entering this

    reg [1:0] state, next_state;

    // State register
    always @(posedge clk or posedge rst) begin
        if (rst) state <= IDLE;
        else     state <= next_state;
    end

    // Next-state + Mealy output (combinational)
    always @(*) begin
        next_state = IDLE;
        detected   = 0;

        case (state)
            IDLE: next_state = din ? S1 : IDLE;
            S1:   next_state = din ? S1 : S10;   // stay in S1 on '1'
            S10: begin
                if (din) begin
                    next_state = S101;
                    detected   = 1;   // ← Mealy: output with transition
                end else
                    next_state = IDLE;
            end
            S101: next_state = din ? S1 : S10;   // handle overlap
        endcase
    end

endmodule
```

Notice: `detected` is assigned in the **combinational** block, not the sequential one. This gives the Mealy's same-cycle response.

---

## 3-Process Coding Style

When output logic is complex, separate it into its own always block:

```verilog
// 3-process style: cleaner for large FSMs
module three_process_fsm (
    input  wire clk, rst, req,
    output reg  grant, busy
);

    localparam IDLE   = 2'd0,
               ACTIVE = 2'd1,
               DONE   = 2'd2;

    reg [1:0] state, next_state;

    // Process 1: State register
    always @(posedge clk or posedge rst) begin
        if (rst) state <= IDLE;
        else     state <= next_state;
    end

    // Process 2: Next-state logic ONLY
    always @(*) begin
        next_state = state;   // default: stay
        case (state)
            IDLE:   if (req)   next_state = ACTIVE;
            ACTIVE:            next_state = DONE;
            DONE:   if (!req)  next_state = IDLE;
        endcase
    end

    // Process 3: Output logic ONLY (Moore outputs)
    always @(*) begin
        grant = 0;
        busy  = 0;
        case (state)
            IDLE:   begin grant = 0; busy = 0; end
            ACTIVE: begin grant = 1; busy = 1; end
            DONE:   begin grant = 0; busy = 1; end
        endcase
    end

endmodule
```

Use 3-process when: outputs are complex OR you want to add registered outputs later (just change `always @(*)` to `always @(posedge clk)`).

---

## One-Hot Encoding

Each state gets its own bit. Faster in FPGAs (saves LUT levels), uses more flip-flops.

```verilog
// One-hot encoding — 4 states need 4 bits
localparam [3:0]
    IDLE   = 4'b0001,
    FETCH  = 4'b0010,
    DECODE = 4'b0100,
    EXEC   = 4'b1000;

reg [3:0] state;

// Check state with AND — synthesises to a single LUT input
if (state[2]) begin  // DECODE state
    ...
end
```

For FPGAs: use one-hot. For ASICs with small state count: binary encoding uses fewer flip-flops.

---

## Gray Encoding

Consecutive states differ by only 1 bit — reduces glitches when state transitions are sampled asynchronously (e.g. in CDC paths).

```verilog
// Gray code for 4 states
localparam [1:0]
    S0 = 2'b00,
    S1 = 2'b01,
    S2 = 2'b11,   // ← only 1 bit changes from S1
    S3 = 2'b10;   // ← only 1 bit changes from S2
```

Most useful for state registers that cross clock domains (async FIFO pointers — see the CDC guide).

---

## Safe-State Design — Avoiding X-Propagation

Always include a `default` branch in the case statement:

```verilog
case (state)
    IDLE:   ...
    ACTIVE: ...
    DONE:   ...
    default: begin        // Handles X at startup or unreachable states
        next_state = IDLE;
        output_sig = 0;
    end
endcase
```

Avoid Verilog pragmas `// synthesis full_case parallel_case` unless you fully understand them — they suppress legitimate warnings and can cause mismatches between simulation and synthesis.

---

## Synthesis Checklist

| Check | Why |
|-------|-----|
| Default assignments before case | Prevents unintended latches |
| Reset to a known state | Avoids X-propagation at power-up |
| No blocking `=` in sequential always | Use non-blocking `<=` only |
| No non-blocking `<=` in combinational always | Use blocking `=` only |
| default: in every case statement | Catches unreachable/X states |
| Outputs always assigned in all branches | No latches on outputs |

---

## Common Mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Missing `default` assignment | Synthesiser infers latch | Assign defaults before `case` |
| Mixing `=` and `<=` in same always block | Simulation/synthesis mismatch | Sequential: always `<=`, Comb: always `=` |
| Forgetting `default:` in case | X-state propagates on reset | Add `default: state <= IDLE` |
| Mealy output in sequential block | One-cycle delay (becomes Moore-like) | Put Mealy outputs in combinational block |
| No reset | State undefined at power-up | Always provide synchronous or async reset |
| Latch in next-state logic | RTL doesn't synthesise as intended | Assign `next_state = state;` as default |

---

## What's Next

- **[SystemVerilog vs Verilog]({% post_url 2026-05-17-systemverilog-vs-verilog %})** — upgrade FSM coding style with `typedef enum`, `always_comb`, and `always_ff`
- **[Pipelining RTL Design]({% post_url 2026-05-17-pipeline-rtl-design %})** — apply state-machine thinking to multi-stage pipelines
- **[Setup & Hold Time]({% post_url 2026-05-17-setup-hold-time-sta %})** — understand why FSM state registers have timing constraints
