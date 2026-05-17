---
layout: page
title: "Learning Path — Digital IC Design Roadmap"
description: "Follow this guided roadmap to go from complete beginner to job-ready digital IC designer. Four tracks: Beginner, RTL Design, ASIC Flow, and Verification."
permalink: /learning-path/
---

<style>
.lp-intro { max-width: 700px; margin: 0 auto 2.5rem; text-align: center; color: var(--text-muted); font-size: 1.05rem; }
.lp-track { margin-bottom: 3rem; }
.lp-track-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; border-bottom: 2px solid var(--border); padding-bottom: 0.75rem; }
.lp-track-icon { font-size: 2rem; }
.lp-track-title { margin: 0; font-size: 1.4rem; }
.lp-track-subtitle { margin: 0; color: var(--text-muted); font-size: 0.9rem; }
.lp-steps { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.75rem; }
.lp-step { display: flex; gap: 1rem; align-items: flex-start; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 1rem 1.25rem; transition: border-color 0.2s; }
.lp-step:hover { border-color: var(--accent); }
.lp-step-num { flex-shrink: 0; width: 2rem; height: 2rem; border-radius: 50%; background: var(--accent); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; }
.lp-step-num.done { background: #3fb950; }
.lp-step-body { flex: 1; }
.lp-step-body h4 { margin: 0 0 0.2rem; font-size: 1rem; }
.lp-step-body h4 a { color: var(--text); text-decoration: none; }
.lp-step-body h4 a:hover { color: var(--accent); }
.lp-step-body p { margin: 0; font-size: 0.85rem; color: var(--text-muted); }
.lp-badge { display: inline-block; font-size: 0.7rem; font-weight: 600; padding: 0.15rem 0.5rem; border-radius: 99px; margin-left: 0.5rem; vertical-align: middle; }
.lp-badge.beginner  { background: #1a2e1a; color: #3fb950; border: 1px solid #3fb950; }
.lp-badge.intermediate { background: #1a1e2e; color: #58a6ff; border: 1px solid #58a6ff; }
.lp-badge.advanced  { background: #2e1a1a; color: #ffa657; border: 1px solid #ffa657; }
.lp-cta { text-align: center; margin: 3rem 0 1rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 2rem; }
.lp-cta h3 { margin-top: 0; }
.lp-cta p { color: var(--text-muted); }
</style>

<p class="lp-intro">
  This roadmap shows you exactly what to read and in what order.
  Follow one track top-to-bottom, or jump between tracks as your interests grow.
</p>

---

## Track 1 — Start Here (Beginner)
{: .lp-track-title }

<div class="lp-track">
<div class="lp-track-header">
  <div class="lp-track-icon">🚀</div>
  <div>
    <h2 class="lp-track-title">Absolute Beginner</h2>
    <p class="lp-track-subtitle">No prior IC design knowledge needed. Start here if you're new to the field.</p>
  </div>
</div>
<ol class="lp-steps">
  <li class="lp-step">
    <div class="lp-step-num">1</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-01-what-is-digital-ic-design %}">What Is Digital IC Design?</a> <span class="lp-badge beginner">Beginner</span></h4>
      <p>Understand what chips are, how they're designed, and where the industry is heading.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">2</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-08-asic-vs-fpga %}">ASIC vs FPGA — Which Should You Learn?</a> <span class="lp-badge beginner">Beginner</span></h4>
      <p>Understand the trade-offs between custom chips (ASIC) and programmable hardware (FPGA).</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">3</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-10-how-to-start-rtl-design %}">How to Start RTL Design</a> <span class="lp-badge beginner">Beginner</span></h4>
      <p>Set up your environment and write your first Verilog module — step by step.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">4</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-05-best-free-verilog-courses-2026 %}">Best Free Verilog Courses (2026)</a> <span class="lp-badge beginner">Beginner</span></h4>
      <p>Curated list of free online courses to supplement your reading.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">5</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-12-top-5-books-vlsi-beginners %}">Top 5 Books for VLSI Beginners</a> <span class="lp-badge beginner">Beginner</span></h4>
      <p>The essential reading list every IC designer should work through.</p>
    </div>
  </li>
</ol>
</div>

---

## Track 2 — RTL Design
{: .lp-track-title }

<div class="lp-track">
<div class="lp-track-header">
  <div class="lp-track-icon">💻</div>
  <div>
    <h2 class="lp-track-title">RTL Design with Verilog & SystemVerilog</h2>
    <p class="lp-track-subtitle">Learn to write synthesisable RTL — the core skill for every digital IC engineer.</p>
  </div>
</div>
<ol class="lp-steps">
  <li class="lp-step">
    <div class="lp-step-num">1</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-systemverilog-vs-verilog %}">SystemVerilog vs Verilog — Key Differences</a> <span class="lp-badge beginner">Beginner</span></h4>
      <p>Understand <code>logic</code>, <code>always_comb</code>/<code>always_ff</code>, interfaces, and why modern RTL uses SystemVerilog.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">2</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-fsm-design-verilog %}">FSM Design in Verilog — Moore, Mealy & Best Practices</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Design finite state machines correctly — 2-process, 3-process, one-hot, Gray encoding.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">3</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-pipeline-rtl-design %}">RTL Pipelining — Design & Hazard Handling</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Build pipelined datapaths, handle RAW/structural/control hazards, implement forwarding.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">4</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-12-riscv-single-cycle-verilog %}">RISC-V Single-Cycle CPU in Verilog</a> <span class="lp-badge advanced">Advanced</span></h4>
      <p>Build a complete working RISC-V processor from scratch — the ultimate RTL project.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">5</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-verilog-interview-questions %}">50 Verilog & Digital Design Interview Questions</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Test your knowledge and prepare for RTL design interviews.</p>
    </div>
  </li>
</ol>
</div>

---

## Track 3 — ASIC Flow & Physical Design
{: .lp-track-title }

<div class="lp-track">
<div class="lp-track-header">
  <div class="lp-track-icon">⚙️</div>
  <div>
    <h2 class="lp-track-title">ASIC Flow — From Netlist to Silicon</h2>
    <p class="lp-track-subtitle">Follow your RTL through synthesis, floorplanning, timing closure, and sign-off.</p>
  </div>
</div>
<ol class="lp-steps">
  <li class="lp-step">
    <div class="lp-step-num">1</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-setup-hold-time-sta %}">Setup & Hold Time — Static Timing Analysis</a> <span class="lp-badge beginner">Beginner</span></h4>
      <p>Understand Tsu, Th, slack, and how STA determines if your design will work at speed.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">2</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-sdc-timing-constraints %}">SDC Timing Constraints — Complete Guide</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Write correct <code>create_clock</code>, <code>set_input_delay</code>, <code>set_multicycle_path</code>, and more.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">3</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-synopsys-design-compiler %}">RTL Synthesis with Synopsys Design Compiler</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Run a complete synthesis flow: read RTL, apply constraints, compile, and write the netlist.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">4</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-vlsi-floorplanning %}">VLSI Floorplanning — Concepts & Techniques</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Place macros, build the power grid, assign pins — set the physical foundation of your chip.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">5</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-power-analysis-asic %}">Power Analysis — Dynamic, Static & Low-Power Techniques</a> <span class="lp-badge advanced">Advanced</span></h4>
      <p>Calculate dynamic/static power, apply clock gating, multi-Vt, UPF power domains, and DVFS.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">6</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-12-librelane-tutorial-beginners %}">LibreLane ASIC Flow Tutorial</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Run a free, open-source ASIC flow end-to-end — no expensive EDA tools required.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">7</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-13-cadence-virtuoso-innovus-shortcuts %}">Cadence Innovus Keyboard Shortcuts</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Work faster in Innovus PnR — essential shortcuts every physical design engineer needs.</p>
    </div>
  </li>
</ol>
</div>

---

## Track 4 — Verification
{: .lp-track-title }

<div class="lp-track">
<div class="lp-track-header">
  <div class="lp-track-icon">✅</div>
  <div>
    <h2 class="lp-track-title">Functional Verification</h2>
    <p class="lp-track-subtitle">Verify that your RTL is correct before tape-out — using industry-standard methods.</p>
  </div>
</div>
<ol class="lp-steps">
  <li class="lp-step">
    <div class="lp-step-num">1</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-17-clock-domain-crossing %}">Clock Domain Crossing — CDC Verification</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Handle metastability, two-flop synchronizers, async FIFOs, and Gray-coded pointers.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">2</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-13-systemverilog-assertions-sva-guide %}">SystemVerilog Assertions (SVA) — Complete Guide</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Write immediate and concurrent assertions, sequences, properties — catch bugs automatically.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">3</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-13-functional-coverage-systemverilog %}">Functional Coverage in SystemVerilog</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Use covergroups, coverpoints, and cross-coverage to measure verification completeness.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">4</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-13-uvm-testbench-from-scratch %}">UVM Testbench from Scratch</a> <span class="lp-badge advanced">Advanced</span></h4>
      <p>Build a complete UVM environment: driver, monitor, scoreboard, sequencer — step by step.</p>
    </div>
  </li>
  <li class="lp-step">
    <div class="lp-step-num">5</div>
    <div class="lp-step-body">
      <h4><a href="{{ site.baseurl }}{% post_url 2026-05-13-cocotb-python-rtl-verification-tutorial %}">cocotb — Python-Based RTL Verification</a> <span class="lp-badge intermediate">Intermediate</span></h4>
      <p>Write testbenches in Python using cocotb — great for data-science engineers entering IC design.</p>
    </div>
  </li>
</ol>
</div>

---

<div class="lp-cta">
  <h3>📖 Not sure where to start?</h3>
  <p>If you're completely new, begin at Track 1 Step 1. If you already know basic Verilog, jump straight to Track 2.</p>
  <a href="{{ '/blog' | relative_url }}" class="btn btn-primary">Browse All Articles →</a>
  &nbsp;
  <a href="{{ '/contact' | relative_url }}" class="btn btn-secondary">Ask a Question</a>
</div>
