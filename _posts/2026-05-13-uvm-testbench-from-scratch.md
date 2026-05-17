---
layout: post
title: "UVM Testbench from Scratch — Step-by-Step Beginner Guide"
description: "Build a complete UVM testbench from zero: seq_item, sequence, sequencer, driver, monitor, scoreboard, agent, env, and test — all explained with a verified ALU example and annotated code."
date: 2026-05-13
category: Verification
tags: [uvm, systemverilog, verification, testbench, scoreboard, driver, monitor, agent, beginner]
---

UVM (Universal Verification Methodology) is the industry-standard framework for verifying complex SoCs. It looks intimidating — factories, phases, config_db — but the core idea is simple: separate stimulus generation, signal driving, response monitoring, and result checking into reusable classes. This guide builds a complete UVM testbench one component at a time, using a 32-bit ALU as the DUT.

---

## UVM at a Glance

```
┌─────────────────────────── UVM Environment ──────────────────────────────┐
│                                                                            │
│   ┌──────────── Agent ──────────────┐                                     │
│   │                                 │                                     │
│   │  Sequence → Sequencer → Driver ─┼──→ DUT ──→ Monitor → Scoreboard    │
│   │              (FIFO)             │                                     │
│   └─────────────────────────────────┘                                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

| Component | What it does |
|-----------|-------------|
| **seq_item** | A single transaction (inputs + expected outputs) |
| **sequence** | A series of seq_items — generates stimulus |
| **sequencer** | Arbitrates between sequences, feeds driver |
| **driver** | Converts seq_items to pin-level signal toggles |
| **monitor** | Watches DUT pins, captures responses into seq_items |
| **scoreboard** | Compares driver-side expected vs monitor-side actual |
| **agent** | Packages sequencer + driver + monitor together |
| **env** | Instantiates one or more agents + scoreboard |
| **test** | Top-level: selects environment, launches sequences |

---

## The DUT — 32-bit ALU

```verilog
// alu.v (same as cocotb tutorial)
module alu (
    input  wire [31:0] a, b,
    input  wire [3:0]  alu_ctrl,
    output reg  [31:0] result,
    output wire        zero
);
    always @(*) begin
        case (alu_ctrl)
            4'd0: result = a + b;
            4'd1: result = a - b;
            4'd2: result = a & b;
            4'd3: result = a | b;
            4'd4: result = a ^ b;
            4'd5: result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            default: result = 32'b0;
        endcase
    end
    assign zero = (result == 32'b0);
endmodule
```

---

## Step 1 — Interface

An interface bundles the DUT signals and provides a clean connection point between the testbench and hardware:

```systemverilog
// alu_if.sv
interface alu_if (input logic clk);
    logic [31:0] a, b;
    logic [3:0]  alu_ctrl;
    logic [31:0] result;
    logic        zero;

    // Clocking block — driver uses this to drive synchronously
    clocking driver_cb @(posedge clk);
        default input #1 output #1;
        output a, b, alu_ctrl;
        input  result, zero;
    endclocking

    // Clocking block — monitor samples outputs
    clocking monitor_cb @(posedge clk);
        default input #1;
        input a, b, alu_ctrl, result, zero;
    endclocking

    modport driver_mp  (clocking driver_cb);
    modport monitor_mp (clocking monitor_cb);
endinterface
```

---

## Step 2 — seq_item (Transaction)

`uvm_sequence_item` is the data unit passed between components:

```systemverilog
// alu_seq_item.sv
class alu_seq_item extends uvm_sequence_item;
    `uvm_object_utils(alu_seq_item)   // register with factory

    // Stimulus fields — randomisable
    rand logic [31:0] a, b;
    rand logic [3:0]  alu_ctrl;

    // Response fields — filled by driver or monitor
    logic [31:0] result;
    logic        zero;

    // Constraints — keep alu_ctrl in valid range 0–5
    constraint c_ctrl { alu_ctrl inside {[0:5]}; }

    function new(string name = "alu_seq_item");
        super.new(name);
    endfunction

    // Pretty-print for debug logs
    function string convert2string();
        return $sformatf("a=%0d b=%0d ctrl=%0d → result=%0d zero=%0b",
                          a, b, alu_ctrl, result, zero);
    endfunction
endclass
```

Key macros:
- `` `uvm_object_utils(T) `` — registers the class with UVM factory (enables override/create)
- `rand` — marks fields for `randomize()`
- `constraint` — restricts the random space

---

## Step 3 — Sequence

A sequence generates transactions and sends them to the sequencer:

```systemverilog
// alu_sequence.sv
class alu_base_seq extends uvm_sequence #(alu_seq_item);
    `uvm_object_utils(alu_base_seq)

    function new(string name = "alu_base_seq");
        super.new(name);
    endfunction

    // 20 random transactions
    task body();
        alu_seq_item item;
        repeat (20) begin
            item = alu_seq_item::type_id::create("item");
            start_item(item);          // request sequencer
            if (!item.randomize())
                `uvm_fatal("RAND", "Randomization failed")
            finish_item(item);         // send to driver — blocks until driver accepts
        end
    endtask
endclass

// Directed sequence — test specific corner cases
class alu_add_overflow_seq extends uvm_sequence #(alu_seq_item);
    `uvm_object_utils(alu_add_overflow_seq)

    function new(string name = "alu_add_overflow_seq");
        super.new(name);
    endfunction

    task body();
        alu_seq_item item;
        // 0xFFFFFFFF + 1 = 0 (32-bit overflow)
        item = alu_seq_item::type_id::create("overflow");
        start_item(item);
        item.a        = 32'hFFFFFFFF;
        item.b        = 32'd1;
        item.alu_ctrl = 4'd0;          // ADD
        finish_item(item);
    endtask
endclass
```

---

## Step 4 — Driver

The driver receives transactions from the sequencer and drives the DUT pins:

```systemverilog
// alu_driver.sv
class alu_driver extends uvm_driver #(alu_seq_item);
    `uvm_component_utils(alu_driver)   // component (not object) — has phases

    virtual alu_if vif;    // virtual interface handle

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // build_phase: get virtual interface from config_db
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(virtual alu_if)::get(this, "", "vif", vif))
            `uvm_fatal("CFG", "Could not get virtual interface from config_db")
    endfunction

    // run_phase: drive transactions forever
    task run_phase(uvm_phase phase);
        alu_seq_item item;
        forever begin
            seq_item_port.get_next_item(item);  // block until sequencer sends one

            // Drive signals to DUT
            vif.driver_cb.a        <= item.a;
            vif.driver_cb.b        <= item.b;
            vif.driver_cb.alu_ctrl <= item.alu_ctrl;

            // Wait one clock for combinational settle + sample
            @(vif.driver_cb);
            item.result = vif.driver_cb.result;
            item.zero   = vif.driver_cb.zero;

            seq_item_port.item_done();          // release the item
        end
    endtask
endclass
```

Key points:
- `uvm_component_utils` — components have phases (build, connect, run…)
- `seq_item_port` — TLM port connected to sequencer's export
- `uvm_config_db::get` — looks up the virtual interface registered by the top-level TB

---

## Step 5 — Monitor

The monitor is *passive* — it only observes the DUT pins and broadcasts what it sees:

```systemverilog
// alu_monitor.sv
class alu_monitor extends uvm_monitor;
    `uvm_component_utils(alu_monitor)

    virtual alu_if vif;

    // Analysis port — broadcast captured transactions to scoreboard
    uvm_analysis_port #(alu_seq_item) ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
        if (!uvm_config_db #(virtual alu_if)::get(this, "", "vif", vif))
            `uvm_fatal("CFG", "Monitor: could not get vif")
    endfunction

    task run_phase(uvm_phase phase);
        alu_seq_item item;
        forever begin
            @(vif.monitor_cb);  // sample at every clock edge

            item            = alu_seq_item::type_id::create("mon_item");
            item.a          = vif.monitor_cb.a;
            item.b          = vif.monitor_cb.b;
            item.alu_ctrl   = vif.monitor_cb.alu_ctrl;
            item.result     = vif.monitor_cb.result;
            item.zero       = vif.monitor_cb.zero;

            ap.write(item);     // broadcast to all connected subscribers
        end
    endtask
endclass
```

`uvm_analysis_port::write()` sends the item to every subscriber (scoreboard, coverage collector, etc.) without the monitor knowing who is listening — classic observer pattern.

---

## Step 6 — Scoreboard

The scoreboard computes the expected result and compares it against the monitor's observed result:

```systemverilog
// alu_scoreboard.sv
class alu_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(alu_scoreboard)

    uvm_analysis_imp #(alu_seq_item, alu_scoreboard) analysis_export;

    int pass_count = 0;
    int fail_count = 0;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        analysis_export = new("analysis_export", this);
    endfunction

    // Called by monitor's ap.write()
    function void write(alu_seq_item item);
        logic [31:0] expected;
        logic        exp_zero;

        // Reference model — mirrors alu.v logic
        case (item.alu_ctrl)
            4'd0: expected = item.a + item.b;
            4'd1: expected = item.a - item.b;
            4'd2: expected = item.a & item.b;
            4'd3: expected = item.a | item.b;
            4'd4: expected = item.a ^ item.b;
            4'd5: expected = ($signed(item.a) < $signed(item.b)) ? 32'd1 : 32'd0;
            default: expected = 32'd0;
        endcase
        exp_zero = (expected == 32'd0);

        if (item.result === expected && item.zero === exp_zero) begin
            pass_count++;
            `uvm_info("SCB", $sformatf("PASS: %s", item.convert2string()), UVM_HIGH)
        end else begin
            fail_count++;
            `uvm_error("SCB", $sformatf(
                "FAIL: %s | expected result=%0d zero=%0b",
                item.convert2string(), expected, exp_zero))
        end
    endfunction

    function void report_phase(uvm_phase phase);
        `uvm_info("SCB", $sformatf(
            "Results: PASS=%0d  FAIL=%0d", pass_count, fail_count), UVM_NONE)
        if (fail_count > 0)
            `uvm_fatal("SCB", "Scoreboard detected failures — test FAILED")
    endfunction
endclass
```

---

## Step 7 — Agent

The agent packages the sequencer, driver, and monitor. It can be **active** (drives + monitors) or **passive** (monitors only):

```systemverilog
// alu_agent.sv
class alu_agent extends uvm_agent;
    `uvm_component_utils(alu_agent)

    alu_sequencer sequencer;
    alu_driver    driver;
    alu_monitor   monitor;

    // Expose monitor's analysis port for env to connect
    uvm_analysis_port #(alu_seq_item) ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        monitor   = alu_monitor  ::type_id::create("monitor",   this);
        if (get_is_active() == UVM_ACTIVE) begin
            sequencer = alu_sequencer::type_id::create("sequencer", this);
            driver    = alu_driver   ::type_id::create("driver",    this);
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        // Connect driver's TLM port to sequencer's export
        if (get_is_active() == UVM_ACTIVE)
            driver.seq_item_port.connect(sequencer.seq_item_export);

        // Expose monitor's analysis port
        ap = monitor.ap;
    endfunction
endclass
```

---

## Step 8 — Environment

The environment instantiates and connects all components:

```systemverilog
// alu_env.sv
class alu_env extends uvm_env;
    `uvm_component_utils(alu_env)

    alu_agent      agent;
    alu_scoreboard scoreboard;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        agent      = alu_agent     ::type_id::create("agent",      this);
        scoreboard = alu_scoreboard::type_id::create("scoreboard", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        // Connect monitor's analysis port to scoreboard's export
        agent.ap.connect(scoreboard.analysis_export);
    endfunction
endclass
```

---

## Step 9 — Test

The test selects the environment and starts the sequences:

```systemverilog
// alu_base_test.sv
class alu_base_test extends uvm_test;
    `uvm_component_utils(alu_base_test)

    alu_env env;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        env = alu_env::type_id::create("env", this);
    endfunction

    task run_phase(uvm_phase phase);
        alu_base_seq seq;

        phase.raise_objection(this);  // tell UVM not to end simulation yet

        seq = alu_base_seq::type_id::create("seq");
        seq.start(env.agent.sequencer);

        #100;                         // let last transaction propagate
        phase.drop_objection(this);   // simulation can end
    endtask
endclass

// Directed test — runs overflow sequence
class alu_overflow_test extends alu_base_test;
    `uvm_component_utils(alu_overflow_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        alu_add_overflow_seq seq;

        phase.raise_objection(this);
        seq = alu_add_overflow_seq::type_id::create("overflow_seq");
        seq.start(env.agent.sequencer);
        #20;
        phase.drop_objection(this);
    endtask
endclass
```

---

## Step 10 — Top-Level Testbench Module

The `tb_top` module instantiates the DUT, interface, and kicks off UVM:

```systemverilog
// tb_top.sv
`include "uvm_macros.svh"
import uvm_pkg::*;

// Include all UVM components
`include "alu_if.sv"
`include "alu_seq_item.sv"
`include "alu_sequencer.sv"
`include "alu_driver.sv"
`include "alu_monitor.sv"
`include "alu_scoreboard.sv"
`include "alu_agent.sv"
`include "alu_env.sv"
`include "alu_sequence.sv"
`include "alu_base_test.sv"

module tb_top;
    logic clk;

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;    // 10 ns period → 100 MHz

    // Instantiate interface
    alu_if dut_if (.clk(clk));

    // Instantiate DUT — connect via interface
    alu dut (
        .a        (dut_if.a),
        .b        (dut_if.b),
        .alu_ctrl (dut_if.alu_ctrl),
        .result   (dut_if.result),
        .zero     (dut_if.zero)
    );

    // Pass interface to all UVM components via config_db
    initial begin
        uvm_config_db #(virtual alu_if)::set(null, "uvm_test_top.*", "vif", dut_if);
        run_test("alu_base_test");   // select test from +UVM_TESTNAME or hardcoded
    end

    // Dump waveforms
    initial begin
        $dumpfile("waves.vcd");
        $dumpvars(0, tb_top);
    end
endmodule
```

Sequencer (boilerplate — just a typedef):
```systemverilog
// alu_sequencer.sv
class alu_sequencer extends uvm_sequencer #(alu_seq_item);
    `uvm_component_utils(alu_sequencer)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass
```

---

## UVM Phases — Execution Order

UVM executes phases in this order, ensuring components are built before connected, connected before run:

| Phase | Type | Purpose |
|-------|------|---------|
| `build_phase` | Function | `create()` child components, `get()` from config_db |
| `connect_phase` | Function | `connect()` TLM ports |
| `start_of_simulation_phase` | Function | Print topology, set defaults |
| `run_phase` | Task (time-consuming) | Drive stimulus, run sequences |
| `extract_phase` | Function | Collect results from monitors |
| `check_phase` | Function | Verify results (alternative to scoreboard) |
| `report_phase` | Function | Print summary, counts |
| `final_phase` | Function | Cleanup |

> **Phases are called bottom-up for `build_phase` (parent builds children first) and top-down for `connect_phase` and `run_phase`.**

---

## config_db — Passing Interfaces

`uvm_config_db` is UVM's global blackboard for sharing objects across the hierarchy:

```systemverilog
// Set — called in tb_top before run_test()
// Arguments: context, instance path, key, value
uvm_config_db #(virtual alu_if)::set(null, "uvm_test_top.*", "vif", dut_if);

// Get — called in driver/monitor build_phase
// Returns 1 if found, 0 if not (fatal if not found)
if (!uvm_config_db #(virtual alu_if)::get(this, "", "vif", vif))
    `uvm_fatal("CFG", "No virtual interface in config_db")
```

The path `"uvm_test_top.*"` matches any component under `uvm_test_top` — the root of the UVM hierarchy created by `run_test()`.

---

## Running the Testbench

```bash
# Compile + run with Cadence Xcelium
xrun -sv -uvm tb_top.sv -top tb_top

# With specific test name via plusarg
xrun -sv -uvm tb_top.sv -top tb_top +UVM_TESTNAME=alu_overflow_test

# Synopsys VCS
vcs -sverilog -ntb_opts uvm-1.2 tb_top.sv -o sim
./sim +UVM_TESTNAME=alu_base_test

# Verbosity levels (controls how much UVM prints)
+UVM_VERBOSITY=UVM_LOW     # errors + fatals only
+UVM_VERBOSITY=UVM_MEDIUM  # default
+UVM_VERBOSITY=UVM_HIGH    # all uvm_info messages
+UVM_VERBOSITY=UVM_FULL    # maximum detail
```

**Expected output (20 random tests):**
```
UVM_INFO alu_scoreboard.sv: Results: PASS=20  FAIL=0
UVM_INFO  : ** UVM TEST PASSED **
```

---

## Factory Override — Swapping Components Without Editing Code

UVM's factory lets you substitute any component at runtime:

```systemverilog
// In test — replace default sequence with a directed one
alu_base_seq::type_id::set_type_override(alu_add_overflow_seq::get_type());

// Or from command line
+uvm_set_type_override=alu_base_seq,alu_add_overflow_seq
```

This is how teams reuse the same environment across many tests — override only what changes.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `create()` instead of `type_id::create()` | Always use `type_id::create()` — enables factory |
| Forgetting `raise/drop_objection` | Simulation ends immediately — all sequences skipped |
| Connecting TLM port wrong direction | `driver.seq_item_port.connect(sequencer.seq_item_export)` |
| Null virtual interface | Set `config_db` *before* `run_test()`, path must match component path |
| `uvm_component_utils` vs `uvm_object_utils` | Components have phases; objects (seq_items, sequences) do not |
| Building children in `connect_phase` | Children must be built in `build_phase` before connect |

---

## What's Next

- **[Functional Coverage in SystemVerilog]({{ site.baseurl }}{% post_url 2026-05-13-functional-coverage-systemverilog %})** — add covergroups to this UVM environment to measure what the random sequences hit
- **[SystemVerilog Assertions (SVA)]({{ site.baseurl }}{% post_url 2026-05-13-systemverilog-assertions-sva-guide %})** — add concurrent property checks to the DUT, run alongside the UVM TB
- **[cocotb Python Verification]({{ site.baseurl }}{% post_url 2026-05-13-cocotb-python-rtl-verification-tutorial %})** — lighter-weight Python alternative for smaller blocks
