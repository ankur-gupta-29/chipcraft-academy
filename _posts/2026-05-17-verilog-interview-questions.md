---
layout: post
title: "Top 50 Verilog & SystemVerilog Interview Questions (with Answers)"
description: "The 50 most common Verilog and SystemVerilog interview questions asked at ASIC, VLSI, and RTL design interviews — with clear, concise answers covering synthesis, simulation, and verification."
date: 2026-05-17
category: RTL Design
tags: [interview, verilog, systemverilog, rtl, synthesis, beginner, career, questions-answers]
---

These are the questions that actually come up in RTL design and ASIC verification interviews at companies like Intel, Qualcomm, Apple, ARM, Nvidia, and TSMC design houses. Grouped by topic, with clear answers.

---

## Basics

**Q1. What is the difference between `reg` and `wire` in Verilog?**

`wire` represents a physical connection — driven by `assign` statements, module outputs, or tri-state drivers. `reg` is a variable that holds its value between assignments — driven by `always` blocks. Despite the name, `reg` does not necessarily infer a hardware register (flip-flop); it depends on whether the `always` block is sequential or combinational.

In SystemVerilog, use `logic` for both — it resolves the ambiguity automatically.

---

**Q2. What is the difference between blocking (`=`) and non-blocking (`<=`) assignments?**

| | Blocking (`=`) | Non-blocking (`<=`) |
|--|---------------|-------------------|
| Execution | Executes immediately; next line waits | Schedules update; all RHS evaluated first, then LHS updated at end of time step |
| Use in | Combinational `always` blocks | Sequential `always` blocks |
| Race condition | Can cause races if used in sequential blocks | Eliminates races between FFs in same time step |

```verilog
// Correct: swap using non-blocking (no temp variable needed)
always @(posedge clk) begin
    a <= b;
    b <= a;   // Both see old values simultaneously — correct!
end

// Wrong: swap using blocking (a and b are corrupted)
always @(posedge clk) begin
    a = b;    // a gets new value immediately
    b = a;    // now b gets the NEW a, not the old value!
end
```

---

**Q3. What is a race condition in Verilog?**

A race condition occurs when two or more `always` blocks in the same simulation time step write to and read from the same variable using blocking assignments. The result depends on the simulator's arbitrary scheduling order. Solution: use non-blocking assignments in sequential always blocks.

---

**Q4. What does `initial` do? Is it synthesisable?**

`initial` executes once at simulation time zero and is used for testbench stimulus and memory initialisation. It is **not synthesisable** (no hardware equivalent). The exception is `initial` used to set the initial value of `reg` variables in some FPGA synthesis tools (not standard for ASIC).

---

**Q5. What is the difference between `$display` and `$monitor`?**

- `$display`: prints once when the statement executes
- `$monitor`: re-prints automatically whenever any of its arguments change value (continuous monitoring throughout simulation)
- `$strobe`: similar to `$display` but prints at the end of the simulation time step (after all non-blocking assignments have resolved)

---

## Synthesis

**Q6. What constructs are not synthesisable?**

| Not synthesisable | Synthesisable alternative |
|------------------|--------------------------|
| `initial` block | Power-on reset logic |
| `#delay` (time delays) | Clock cycles |
| `$display`, `$finish`, `$random` | — (sim tasks) |
| `fork/join` | Sequential logic |
| `real`, `integer` (in some tools) | `logic`, `reg` |
| `casex`/`casez` in some contexts | `case` with explicit don't cares |
| `while` (unbounded loop) | Bounded `for` loops |

---

**Q7. How does a latch get accidentally inferred?**

A latch is inferred when a combinational `always` block doesn't assign a signal in every branch:

```verilog
// ❌ Infers latch — y not assigned when sel=0
always @(*) begin
    if (sel) y = a;
    // What is y when sel=0? Latch holds old value!
end

// ✓ No latch — y always assigned
always @(*) begin
    y = 0;         // default
    if (sel) y = a;
end
```

---

**Q8. What is the difference between synchronous and asynchronous reset?**

```verilog
// Synchronous reset — only resets at clock edge
always @(posedge clk) begin
    if (rst) q <= 0;
    else     q <= d;
end

// Asynchronous reset — resets immediately, independent of clock
always @(posedge clk or posedge rst) begin
    if (rst) q <= 0;
    else     q <= d;
end
```

| | Synchronous | Asynchronous |
|--|-------------|-------------|
| Filtered by clock | Yes (glitch-safe) | No (any rst glitch resets FF) |
| Timing analysis | Easier (treated as data) | Harder (needs special constraints) |
| Industry preference | ASIC: often sync | FPGA: async more common |

---

**Q9. What is `casex` vs `casez`?**

Both allow don't cares but differ in what's treated as don't care:
- `casez`: `?` and `z` in case items are don't cares
- `casex`: `?`, `z`, and `x` are all don't cares (dangerous — can mask X-propagation bugs)

**Industry advice:** Avoid `casex`; use `casez` or SystemVerilog's `case inside` instead.

---

**Q10. What is full_case and parallel_case?**

These are synthesis pragmas (directives):
- `// synthesis full_case`: tells the tool all input combinations are covered — suppresses latch inference for missing branches
- `// synthesis parallel_case`: tells the tool case branches don't overlap — allows parallel evaluation

**Warning:** These can cause simulation/synthesis mismatches. In SystemVerilog, use `unique case` and `priority case` instead — they have defined LRM semantics.

---

## Flip-Flops and Timing

**Q11. What is setup time and hold time?**

- **Setup time (Tsu):** Data must be stable for Tsu before the clock edge for the flip-flop to reliably capture it
- **Hold time (Th):** Data must remain stable for Th after the clock edge
- **Violation:** Setup violation → wrong value captured; Hold violation → indeterminate output (metastability)

---

**Q12. What is metastability?**

When a flip-flop's setup or hold time is violated, its output can enter an indeterminate state between 0 and 1. This typically occurs at clock domain crossings. The output eventually resolves but timing is unpredictable. Mitigated (not eliminated) by using multi-stage synchronizers.

---

**Q13. What is clock skew?**

Clock skew is the difference in arrival time of the clock signal at two different flip-flops. Positive skew (capture clock arrives later) helps setup but hurts hold. Negative skew hurts setup. The clock tree synthesis (CTS) step minimises skew.

---

**Q14. What is clock jitter?**

Jitter is cycle-to-cycle variation in the clock period due to PLL noise, power supply noise, and temperature. It's modelled in STA by `set_clock_uncertainty`. Setup violations: add jitter to clock period uncertainty. Hold: add jitter to minimum delay.

---

**Q15. What is the critical path?**

The path from launch FF to capture FF with the smallest (or most negative) timing slack — the path that limits maximum clock frequency. Fixing the critical path means either reducing logic depth, using faster cells, or pipelining.

---

## FSM Design

**Q16. What is a Moore vs Mealy FSM?**

- **Moore:** Outputs depend only on the current state — stable, glitch-free outputs
- **Mealy:** Outputs depend on current state AND inputs — fewer states needed, faster response but combinational path through inputs

---

**Q17. Why should you always include a `default` in a case statement?**

Without a default, if the state register contains `X` (at power-up before reset) or an undefined value, the `case` has no match — simulation continues with the last value (potential latch), and the design is in an undefined state. The default forces a safe known state.

---

**Q18. What is the difference between 1-hot, binary, and Gray encoding?**

| Encoding | Example (4 states) | Speed | Area | Glitch |
|----------|-------------------|-------|------|--------|
| Binary | 00, 01, 10, 11 | Slower decode | Small | Multiple bit changes |
| Gray | 00, 01, 11, 10 | Slower | Small | 1 bit changes at a time |
| One-hot | 0001, 0010, 0100, 1000 | Fastest decode | Largest | Multiple bits |

---

## Verification

**Q19. What is the difference between simulation and formal verification?**

| | Simulation | Formal Verification |
|--|-----------|---------------------|
| Method | Runs test vectors through design | Mathematical proof over all possible inputs |
| Coverage | Only tested scenarios | Exhaustive (for bounded properties) |
| Effort | Write testbenches | Write properties (SVA) |
| Scale | Any size | Limits at ~2M state elements |
| Finding bugs | Random/directed tests | Proves absence of bugs |

---

**Q20. What is functional coverage?**

Functional coverage measures whether meaningful design scenarios have been exercised by tests. Defined with `covergroup` and `coverpoint` in SystemVerilog. The verification team defines bins for important value ranges and transition sequences. Uncovered bins indicate test gaps.

---

**Q21. What is the difference between code coverage and functional coverage?**

- **Code coverage** (automatic): tracks which lines/branches of RTL executed. High code coverage doesn't guarantee the design was tested correctly.
- **Functional coverage** (manual): tracks whether important functional scenarios were exercised. Requires explicit `covergroup` definitions.

Both are required for sign-off.

---

**Q22. What is a scoreboard in UVM?**

A scoreboard is the self-checking component of a UVM testbench. It receives transactions from the monitor's analysis port, runs a reference model to compute expected results, and compares them to the DUT's actual output. It reports pass/fail and counts errors.

---

## SystemVerilog Specifics

**Q23. What is the difference between `logic` and `bit`?**

- `logic`: 4-state type (0, 1, X, Z) — can model unknown/high-impedance; default
- `bit`: 2-state type (0, 1 only) — faster simulation; used in testbench when X/Z not needed

For RTL: always use `logic`. For testbench variables where X/Z aren't meaningful: `bit` is fine.

---

**Q24. What is `always_comb` vs `always @(*)`?**

Both infer combinational logic, but `always_comb`:
- Automatically computes sensitivity list
- Executes once at time 0 (before any events)
- Tool verifies the block is truly combinational (errors if a latch would be inferred)
- Is part of the language standard — no pragma needed

---

**Q25. What is the `$cast` system function?**

Used to safely assign an expression to an enum variable when the type is derived at runtime:

```systemverilog
typedef enum {IDLE, ACTIVE, DONE} state_t;
state_t state;
int val = 1;
$cast(state, val);   // state = ACTIVE; errors if val is out of range
```

---

**Q26. What are packed vs unpacked arrays?**

```systemverilog
// Packed array: contiguous bits — can be sliced as a single vector
logic [7:0] byte_val;           // [7:0] is packed dimension
logic [3:0][7:0] packed_arr;    // 4 bytes = 32 bits contiguous

// Unpacked array: separate elements — cannot be sliced as vector
logic [7:0] mem [0:255];        // 256 8-bit words — unpacked
logic       reg_file [0:31];    // 32 bits, each independently addressed
```

Packed arrays are synthesisable; unpacked arrays can model memories.

---

## Common Interview Trick Questions

**Q27. What is the output of this code?**

```verilog
module test;
    reg [3:0] a;
    initial begin
        a = 4'b1010;
        $display("a = %b", a);
        a = a + 1'b1;
        $display("a = %b", a);
    end
endmodule
```

Output:
```
a = 1010
a = 1011
```
(Simple increment — `1010 + 1 = 1011`)

---

**Q28. What does this synthesise to?**

```verilog
always @(posedge clk)
    if (en) q <= d;
```

A **flip-flop with a clock enable** (`q` retains value when `en=0`). This is NOT a latch — the `always @(posedge clk)` makes it clocked. The `if` without `else` in a sequential block doesn't create a latch because the flip-flop itself holds state.

---

**Q29. What is wrong with this code?**

```verilog
always @(posedge clk) begin
    a = b + c;    // blocking in sequential — BUG
    d = a & e;    // depends on updated a — might be OK in sim, wrong in synth
end
```

Using blocking assignment in a sequential block causes simulation/synthesis mismatches. The synthesised circuit will compute `d = (b+c) & e` as combinational, not as two sequential registers. Use non-blocking: `a <= b + c; d <= a & e;` — this gives two flip-flops with `d` getting the OLD value of `a`.

---

**Q30. What is `$signed` used for?**

Forces a value to be treated as a signed (2's complement) number in arithmetic and comparison operations:

```verilog
logic [7:0] a = 8'hF0;   // = 240 unsigned, or -16 signed
logic [7:0] b = 8'h10;

// Unsigned comparison (default): 240 > 16 → true
if (a > b) ...

// Signed comparison: -16 < 16 → result changes!
if ($signed(a) > $signed(b)) ...
```

---

## Advanced Topics

**Q31. What is glue logic and why is it bad for timing?**

Glue logic is combinational logic placed at the top-level of a design to connect blocks — outside any block's hierarchy. It's hard for place-and-route tools to optimise since it has no natural home in the floorplan, often creating long wires. Better practice: push glue logic into one of the blocks it connects.

**Q32. What is a half-adder vs full-adder?**

- **Half-adder:** `Sum = A XOR B`, `Carry = A AND B` — no carry input
- **Full-adder:** `Sum = A XOR B XOR Cin`, `Cout = majority(A, B, Cin)` — includes carry in

**Q33. What is `tri`, `tri0`, `tri1`?**

`tri` is equivalent to `wire` for tri-state nets. `tri0` resolves to 0 when undriven (pull-down); `tri1` resolves to 1 (pull-up). Used to model open-collector or open-drain buses.

**Q34. What is `wor` and `wand`?**

`wor` (wired-OR): when multiple drivers drive the net, the result is OR of all values. `wand` (wired-AND): result is AND. Used for open-collector (wand) and open-emitter (wor) bus topologies.

**Q35. What is the difference between `==` and `===`?**

- `==`: 4-state equality — if either operand has X or Z, result is X (unknown)
- `===`: case equality — X matches X, Z matches Z; returns 0 or 1 only
- `!==`: case inequality

`===` is simulation-only (not synthesisable). Used in testbenches to check for X values: `if (result === 4'bxxxx) $error("X propagated!")`.

**Q36. What is event-driven simulation?**

Verilog simulators only evaluate a process when one of its input signals changes (an "event"). Between events, nothing executes. This makes simulation efficient — large quiescent designs use minimal CPU time.

**Q37. What is the `deassign` statement?**

Releases a continuous procedural assignment made by `assign` inside a procedural block (not the continuous assignment outside always blocks). Rarely used; largely a Verilog-95 construct.

**Q38. What is the PLI/VPI in Verilog?**

The Programming Language Interface (PLI) / Verilog Procedural Interface (VPI) allows external C/C++ code to interact with a Verilog simulation — read/write signals, inject events, add system tasks. Used to connect simulators to external models (e.g. a C reference model, power estimator, or co-simulation framework like cocotb).

**Q39. What is `$dumpvars`?**

Saves signal waveforms to a VCD (Value Change Dump) file for waveform viewing in GTKWave or similar tools:

```verilog
initial begin
    $dumpfile("waves.vcd");
    $dumpvars(0, tb_top);    // 0 = all hierarchy levels
end
```

**Q40. How do you model a dual-port RAM in Verilog?**

```verilog
module dual_port_ram #(parameter W=8, D=256)(
    input              clk,
    input              we_a,
    input  [$clog2(D)-1:0] addr_a, addr_b,
    input  [W-1:0]     din_a,
    output reg [W-1:0] dout_a, dout_b
);
    reg [W-1:0] mem [0:D-1];

    always @(posedge clk) begin
        if (we_a) mem[addr_a] <= din_a;
        dout_a <= mem[addr_a];
    end

    always @(posedge clk)
        dout_b <= mem[addr_b];   // read port B (read-only)
endmodule
```

---

## Power and Physical Design Questions

**Q41. What is clock gating and why is it used?**

Clock gating disables the clock signal to a group of flip-flops when their data isn't changing. Since the clock tree is the largest power consumer in most chips (25–40%), gating unused clocks saves significant dynamic power. An integrated clock gate (ICG) cell combines a latch (for glitch prevention) and an AND gate.

**Q42. What is IR drop?**

IR drop is the resistive voltage loss across the power delivery network (metal wires) from the power pad to the standard cells. High IR drop means cells see lower VDD → they run slower → timing violations. Fixed by widening power stripes, adding vias, or repositioning high-current blocks.

**Q43. What is the difference between static and dynamic IR drop?**

- **Static IR drop:** Average current analysis — shows worst-case DC resistance effects
- **Dynamic IR drop:** Instantaneous current analysis — captures peak current during clock edges when many cells switch simultaneously; more accurate but requires switching activity data

**Q44. What are decap cells?**

Decoupling capacitor (decap) cells are standard cells filled with large MOS capacitors. They store local charge near switching logic to supply instantaneous current demand without it travelling all the way from the power pad — reduces dynamic IR drop.

**Q45. What is the purpose of filler cells?**

Filler cells fill gaps between standard cells in cell rows. They maintain N-well continuity (required by DRC), provide substrate ties, and in some libraries add small amounts of decap. They carry no logic — they're placement artifacts.

---

## Interview Process Tips

**Q46–50: Questions you should ask the interviewer**

These show engagement and technical depth:

- "What is your typical RTL-to-GDSII timeline, and where does the team spend the most iteration time?"
- "What verification methodology does the team use — UVM, formal, cocotb, or a mix?"
- "At what abstraction level is most of the RTL written — RTL, TLM, or IP reuse?"
- "What are the main timing closure challenges on your current design node?"
- "How does the team manage CDC verification — which tools and what sign-off criteria?"

---

## Quick-Reference Summary Table

| Concept | One-line answer |
|---------|----------------|
| `reg` vs `wire` | `reg` holds value between assignments; `wire` is a net — use `logic` in SV |
| `=` vs `<=` | Blocking (immediate); Non-blocking (end-of-timestep) |
| Latch | Inferred when comb always block omits assignment in a branch |
| Setup time | Data must be stable Tsu before clock edge |
| Hold time | Data must be stable Th after clock edge |
| Metastability | FF output between 0/1 after setup/hold violation |
| CDC | Signals crossing unrelated clock domains — needs synchronizers |
| FSM Moore | Output = f(state only) |
| FSM Mealy | Output = f(state, inputs) |
| Clock gating | Disable clock to idle FFs → saves dynamic power |
| Multi-Vt | Mix HVT/LVT cells for leakage vs speed trade-off |
| `===` | Case equality — X matches X; simulation-only |
| `always_comb` | SV replacement for `always @(*)`; enforces combinational intent |
| `unique case` | SV replacement for full_case/parallel_case pragmas |

---

## What's Next

- **[FSM Design in Verilog]({% post_url 2026-05-17-fsm-design-verilog %})** — master the FSM interview questions with real code
- **[SystemVerilog vs Verilog]({% post_url 2026-05-17-systemverilog-vs-verilog %})** — answer the SV-specific questions confidently
- **[Setup & Hold Time — STA]({% post_url 2026-05-17-setup-hold-time-sta %})** — deep dive into timing interview questions
