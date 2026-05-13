---
layout: post
title: "Cadence Virtuoso & Innovus Keyboard Shortcuts — Complete Cheat Sheet"
description: "Every keyboard shortcut you need for Cadence Virtuoso (schematic/layout) and Innovus (place & route), with a full keyboard SVG diagram."
date: 2026-05-13
category: ASIC Flow
tags: [cadence, virtuoso, innovus, shortcuts, asic, layout, schematic, productivity]
---

Switching between Cadence tools all day is slow when you reach for the mouse every time. This guide maps out every shortcut worth knowing for **Virtuoso** (schematic and layout editing) and **Innovus** (place & route), plus a colour-coded keyboard diagram you can print and pin above your workstation.

---

## Keyboard Diagram

<img src="{{ '/assets/images/cadence-keyboard-shortcuts.svg' | relative_url }}"
     alt="Cadence Virtuoso and Innovus keyboard shortcuts diagram"
     style="width:100%; border-radius:12px; margin:1.5rem 0; background:#0d1117;">

| Colour | Tool |
|--------|------|
| 🔵 Blue | Virtuoso only (Schematic / Layout) |
| 🟢 Green | Innovus only (Place & Route) |
| 🟠 Orange | Common to both tools |

---

## Cadence Virtuoso — Schematic Editor

### Essential Navigation

| Key | Action |
|-----|--------|
| `F` | Fit / Zoom to fit entire schematic |
| `Z` | Zoom in (centre of view) |
| `Shift+Z` | Zoom out |
| `Ctrl+Z` | Undo last action |
| `Ctrl+Y` | Redo |
| `Esc` | Cancel current command / deselect |

### Drawing & Editing

| Key | Action |
|-----|--------|
| `I` | Place Instance (component from library) |
| `W` | Add Wire |
| `P` | Add Pin (port) |
| `L` | Add Label / net name |
| `Q` | Edit Properties of selected object |
| `E` | Descend into hierarchy / Edit cell |
| `Ctrl+E` | Return from hierarchy (ascend) |
| `M` | Move selected object |
| `C` | Copy selected object |
| `D` | Delete selected object |
| `R` | Rotate selected object |
| `U` | Undo (alternative to Ctrl+Z in some Virtuoso versions) |

### Selection & View

| Key | Action |
|-----|--------|
| `Ctrl+A` | Select all objects |
| `Ctrl+F` | Find net or instance by name |
| `Ctrl+S` | Save |
| `Shift+F` | Fit to selected objects |
| `Del` | Delete selected |

---

## Cadence Virtuoso — Layout Editor (Virtuoso XL / Layout Suite)

All the schematic shortcuts carry over, plus these layout-specific ones:

| Key | Action |
|-----|--------|
| `R` | Draw Rectangle |
| `P` | Draw Polygon |
| `X` | Stretch selected shape |
| `K` | Add ruler / measure distance |
| `Shift+K` | Delete all rulers |
| `S` | Snap / Align to grid |
| `O` | Add Via |
| `J` | Add path (metal route) |
| `Ctrl+H` | Highlight net |
| `B` | Add pcell parameter |
| `G` | Gravity (snap to nearest point) |
| `F3` | Toggle Show/Hide layer |

### DRC / LVS Quick Commands

| Key | Action |
|-----|--------|
| `Shift+V` | Verify DRC (runs Assura/PVS) |
| `Ctrl+L` | Open layer selection panel |
| `Alt+F4` | Close active window |

---

## Cadence Innovus (formerly EDI / Encounter)

### Navigation

| Key | Action |
|-----|--------|
| `F` | Fit — zoom to show entire floorplan |
| `Z` | Zoom in |
| `Shift+Z` | Zoom out |
| `Ctrl+Z` | Undo |
| `Esc` | Cancel current selection or command |

### Selection & Inspection

| Key | Action |
|-----|--------|
| `S` | Select mode |
| `Ctrl+A` | Select all visible objects |
| `D` | Deselect all |
| `Q` | Query / inspect selected object properties |
| `H` | Highlight selected net or object |
| `Shift+H` | Remove all highlights |
| `G` | Fly to net / Go to net by name |
| `Del` | Delete selected object |

### Floorplan & Placement

| Key | Action |
|-----|--------|
| `F3` | Filter selection by object type |
| `Ctrl+F` | Find object by name |
| `M` | Move selected cell or macro |
| `R` | Rotate selected instance |
| `C` | Copy selected instance |

### Routing

| Key | Action |
|-----|--------|
| `J` | Interactive route (pencil route) |
| `Shift+J` | Add wire end-point |
| `X` | Edit route / fix DRC violation |
| `B` | Add bus route |

### Useful Ctrl Combinations (both tools)

| Combo | Action |
|-------|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+S` | Save design |
| `Ctrl+A` | Select all |
| `Ctrl+F` | Find by name |
| `Ctrl+H` | Highlight net (Virtuoso layout) |

---

## Customising Shortcuts

### Virtuoso
Shortcuts in Virtuoso are defined in the `~/.cadence/virtuoso/keys` SKILL file. You can override any binding:

```
hiSetPoint( "Layout" "K" nil "enterRuler" )
```

Or use the **Tools → Customize** menu inside Virtuoso to set bindings via the GUI.

### Innovus
In Innovus, add shortcut overrides to your `~/.inoKey` file:

```
# ~/.inoKey
bindKey    F      "fit"
bindKey    Z      "zoom in"
bindKey S+Z      "zoom out"
```

Reload with `source ~/.inoKey` at the Innovus command prompt.

---

## Pro Tips

**1. Layer shortcuts in Layout**  
Press `Ctrl+L` to open the layer panel, then type a layer abbreviation (`M1`, `M2`, `POLY`) to jump directly to that layer.

**2. Ruler muscle memory**  
In Virtuoso Layout, press `K` → click start point → click end point. You'll read spacing and overlap violations instantly. Use `Shift+K` to clear all rulers before a DRC run.

**3. `F` after every zoom operation**  
Get into the habit of pressing `F` whenever you feel lost. It's faster than scrolling back to context.

**4. `Q` is faster than the Properties menu**  
Select any object and press `Q` immediately — the Properties dialog opens instantly. Saves three menu clicks every time.

**5. Innovus `G` for net tracing**  
Press `G`, type a net name, and Innovus flies you straight to it. Essential when debugging post-route DRC on a congested design.

---

## Printable Reference

Save the keyboard diagram at the top of this page and print it at A4/Letter size — it fits neatly above a dual-monitor workstation setup.

*Need a deeper dive into the full ASIC flow from RTL to GDSII? Read the [LibreLane tutorial →](/blog/2026/05/12/librelane-tutorial-beginners/)*
