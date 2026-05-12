---
layout: page
title: Free Resources
description: "The best free tools, simulators, references, and communities for learning Digital IC Design."
permalink: /resources/
---

Everything on this page is completely free. No paywalls, no affiliate links — just the best resources I've found while learning.

---

## Online Practice & Simulators

| Resource | What It Is | Link |
|----------|-----------|------|
| **HDLBits** | Interactive Verilog exercises, graded in-browser | [hdlbits.01xz.net](https://hdlbits.01xz.net) |
| **EDA Playground** | Browser-based simulator for Verilog/VHDL/SV | [edaplayground.com](https://edaplayground.com) |
| **ChipVerify** | SystemVerilog & UVM tutorial + reference | [chipverify.com](https://chipverify.com) |
| **Icarus Verilog** | Free open-source Verilog simulator | [iverilog.icarus.com](http://iverilog.icarus.com) |
| **GTKWave** | Free waveform viewer for simulation output | [gtkwave.sourceforge.net](http://gtkwave.sourceforge.net) |
| **Yosys** | Open-source synthesis framework | [yosyshq.net/yosys](https://yosyshq.net/yosys/) |
| **OpenROAD** | Open-source ASIC P&R flow | [openroad.readthedocs.io](https://openroad.readthedocs.io) |

---

## Free Courses & Video Series

- **Nandland** — FPGA/Verilog tutorials: [nandland.com](https://nandland.com)
- **VLSI CAD (Coursera / U of Illinois)** — Free to audit, excellent rigour
- **MIT OpenCourseWare 6.004** — Computation Structures (digital systems from scratch)
- **NPTEL Digital Circuits & Systems** — Full university lecture series on YouTube
- **ZipCPU Blog** — Deep RTL design and formal verification articles: [zipcpu.com](https://zipcpu.com)

---

## Reference Books (Free / Open Access)

| Book | Author | Notes |
|------|--------|-------|
| *Digital Design and Computer Architecture* | Harris & Harris | Widely used textbook, PDFs circulate freely |
| *Verilog HDL* | Samir Palnitkar | Classic Verilog reference |
| *CMOS VLSI Design* | Weste & Harris | Standard physical design textbook |
| *Static Timing Analysis for Nanometer Designs* | J. Bhasker | STA bible |

---

## Communities & Forums

- **Reddit r/VLSI** — Active community for IC design questions
- **Reddit r/ECE** — Broader electrical engineering discussions
- **Stack Exchange (Electrical Engineering)** — Q&A for specific technical questions
- **Verification Academy** — Mentor's free UVM training portal
- **IEEE Xplore** — Technical papers (many accessible free through institutions)

---

## Cheat Sheets & Quick References

- **Verilog Quick Reference** — [sutherland-hdl.com](https://www.sutherland-hdl.com/online_verilog_ref_guide/vlog_ref_top.html)
- **SystemVerilog LRM** — IEEE 1800-2017 (the official language reference)
- **UVM Reference Guide** — Mentor/Siemens free download
- **SDC Command Reference** — Synopsys Design Constraints reference (search "SDC quick reference")

---

## Open-Source Tools Summary

```
Simulation:   Icarus Verilog + GTKWave (or Verilator for speed)
Synthesis:    Yosys
P&R:          OpenROAD / OpenLane
PDK:          SkyWater 130nm (open PDK from Google/SkyWater)
Full Flow:    OpenLane = Yosys + OpenROAD + Magic + Netgen
```

The **OpenLane / SkyWater 130nm** stack lets you run a complete ASIC flow for free — you can even submit for fabrication via [Efabless chipIgnite](https://efabless.com).
