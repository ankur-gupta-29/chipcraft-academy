---
layout: post
title: "Cadence Virtuoso & Innovus Keyboard Shortcuts — Complete Cheat Sheet"
description: "Every keyboard shortcut you need for Cadence Virtuoso (schematic/layout) and Innovus (place & route), verified against Cadence community sources, with a full keyboard SVG diagram."
date: 2026-05-13
category: ASIC Flow
tags: [cadence, virtuoso, innovus, shortcuts, asic, layout, schematic, productivity]
---

Switching between Cadence tools all day is slow when you reach for the mouse every time. This guide maps out every shortcut worth knowing for **Virtuoso** (schematic and layout editing) and **Innovus** (place & route), verified against multiple Cadence community and university lab sources. A colour-coded keyboard diagram is included — print it and pin it above your workstation.

> **⚠️ Important:** Virtuoso's layout editor remaps `Ctrl+Z` to **Zoom In 2×** (not Undo). Undo in both editors is `U` / `Shift+U`. Keep this in muscle memory — it trips up everyone coming from standard Windows apps.

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

### Navigation & Zoom

| Key | Action |
|-----|--------|
| `F` | Fit — zoom to fit entire schematic |
| `Shift+F` | Fit to selected objects only |
| `Z` | Zoom in |
| `Shift+Z` | Zoom out |
| `Esc` | Cancel current command / deselect |

### Undo / Save
> In Virtuoso, `U` / `Shift+U` are the primary undo/redo keys. `Ctrl+Z` is **not** undo in the layout editor (see below).

| Key | Action |
|-----|--------|
| `U` | Undo last action |
| `Shift+U` | Redo |
| `X` | Save schematic |
| `Shift+X` | Check and Save (runs checks before saving) |
| `Ctrl+S` | Save (also works in most Virtuoso windows) |

### Drawing & Wiring

| Key | Action |
|-----|--------|
| `W` | Add Wire |
| `Shift+W` | Add Bus wire (wide wire) |
| `L` | Add Label / net name |
| `I` | Place Instance (component from library) |
| `P` | Add Pin (port) |
| `N` | Add note shape |
| `Shift+N` | Add text note |

### Editing

| Key | Action |
|-----|--------|
| `Q` | Edit Properties of selected object |
| `T` | Click net to edit name in-place |
| `M` | Move selected object |
| `C` | Copy selected object |
| `R` | Rotate selected object 90° |
| `Shift+R` | Mirror instance horizontally |
| `Ctrl+R` | Mirror instance vertically |
| `Del` | Delete selected |
| `Shift+Del` | Comment / uncomment instance |

### Hierarchy Navigation

| Key | Action |
|-----|--------|
| `E` | Descend into hierarchy (read-only view) |
| `Shift+E` | Descend into hierarchy (edit mode) |
| `Ctrl+E` | Ascend — return to parent level |

### Selection

| Key | Action |
|-----|--------|
| `Ctrl+A` | Select all objects |
| `Ctrl+F` | Find net or instance by name |
| `F3` | Options for current active command |
| `O` | Display / layer settings |

---

## Cadence Virtuoso — Layout Editor (VLS / Layout XL)

> **Critical difference from schematic:**
> - `Z` = Zoom to box (drag to select zoom area)
> - `Ctrl+Z` = Zoom In 2× *(this is NOT undo!)*
> - `Shift+Z` = Zoom Out 2×
> - `U` = Undo, `Shift+U` = Redo

### Navigation & Zoom

| Key | Action |
|-----|--------|
| `F` | Fit entire layout to screen |
| `Z` | Zoom to box — drag to define zoom area |
| `Ctrl+Z` | Zoom In 2× (not undo!) |
| `Shift+Z` | Zoom Out 2× |
| `U` | Undo |
| `Shift+U` | Redo |

### Drawing Shapes

| Key | Action |
|-----|--------|
| `R` | Draw Rectangle |
| `P` | Draw Path (wire / metal route) |
| `Ctrl+P` | Create Pin |
| `O` | Add Via |
| `J` | Add path segment |
| `N` | Add note / annotation |

### Editing Shapes

| Key | Action |
|-----|--------|
| `Q` | Edit properties of selected object |
| `M` | Move selected object |
| `C` | Copy selected object |
| `S` | Stretch selected wire or shape |
| `X` | Descend into hierarchy (layout cell) |
| `Shift+B` | Ascend — return to parent level |
| `Del` | Delete selected |
| `A` | Align selected objects (F3 for spacing options) |
| `Shift+M` | Merge two shapes on same layer |
| `Shift+C` | Chop — cut a hole in a shape |
| `Shift+G` | Add guard ring (F3 for options) |

### Measurement & DRC

| Key | Action |
|-----|--------|
| `K` | Add ruler / measure distance |
| `Shift+K` | Delete all rulers |
| `Ctrl+H` | Highlight net |
| `Ctrl+A` | Select all |
| `Ctrl+D` | Deselect all |
| `Ctrl+L` | Open layer selection panel |
| `F3` | Options for current active command |
| `G` | Gravity — snap to nearest object point |

---

## Cadence Innovus (formerly EDI / Encounter)

### Navigation & Zoom

| Key | Action |
|-----|--------|
| `F` | Fit — zoom to show entire floorplan |
| `Z` | Zoom in |
| `Shift+Z` | Zoom out |
| `Esc` | Cancel current selection or command |

### Metal Layer Visibility (Innovus exclusive)

| Key | Action |
|-----|--------|
| `1` | Toggle Metal 1 (M1) visibility |
| `2` | Toggle Metal 2 (M2) visibility |
| `3–9` | Toggle M3–M9 visibility |

This is one of the most useful Innovus tricks — press a number key to quickly show or hide a routing layer when debugging congestion.

### Selection & Inspection

| Key | Action |
|-----|--------|
| `S` | Select mode |
| `Ctrl+A` | Select all visible objects |
| `D` | Deselect all |
| `Q` | Query / inspect selected object properties |
| `H` | Highlight selected net or object |
| `Shift+H` | Remove all highlights |
| `G` | Fly to net — type a net name to jump to it |
| `Del` | Delete selected object |
| `F3` | Filter selection by object type |
| `Ctrl+F` | Find object by name |

### Placement & Floorplan

| Key | Action |
|-----|--------|
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

### Undo / Save (Innovus)

| Combo | Action |
|-------|--------|
| `Ctrl+Z` | Undo (standard in Innovus) |
| `Ctrl+Y` | Redo |
| `Ctrl+S` | Save design database |

---

## Ctrl Combinations — Quick Reference

| Combo | Virtuoso Schematic | Virtuoso Layout | Innovus |
|-------|--------------------|-----------------|---------|
| `Ctrl+Z` | Undo | **Zoom In 2×** ⚠️ | Undo |
| `Ctrl+Y` | — | — | Redo |
| `Ctrl+S` | Save | Save | Save |
| `Ctrl+A` | Select All | Select All | Select All |
| `Ctrl+E` | Ascend hierarchy | — | — |
| `Ctrl+P` | — | Create Pin | — |
| `Ctrl+D` | — | Deselect All | — |
| `Ctrl+H` | — | Highlight Net | — |
| `Ctrl+F` | Find | Find | Find |
| `Ctrl+L` | — | Layer panel | — |

---

## Customising Shortcuts

### Virtuoso — `.cdsinit` / SKILL bindkeys
Create or edit `~/.cdsinit` and add lines like:

```scheme
; Schematic editor — bind Ctrl+W to close window
hiSetBindKey("Schematics" "Ctrl<Key>w" "hiClose()")

; Layout editor — custom ruler key
hiSetBindKey("Layout" "<Key>k" "leEnterRuler()")
```

### Innovus — `~/.inoKey`
Create `~/.inoKey` and add:

```
# Zoom and fit
bindKey  F      "fit"
bindKey  Z      "zoom in"
bindKey S+Z     "zoom out"

# Layer visibility
bindKey  1      "setLayerVisible metal1 toggle"
bindKey  2      "setLayerVisible metal2 toggle"
```

Load at runtime: `source ~/.inoKey`

---

## Pro Tips

**1. `Ctrl+Z` ≠ Undo in Virtuoso Layout**
This catches everyone. In layout, `Ctrl+Z` zooms in. Use `U` to undo and `Shift+U` to redo. Tattoo this on your hand.

**2. `Shift+X` before every commit**
Always use `Shift+X` (Check and Save) rather than plain `X` in the schematic editor. It runs a connectivity check and catches floating wires and unconnected pins before you save a broken netlist.

**3. Metal layer toggle with number keys (Innovus)**
When debugging post-route DRC, press `3` to hide M3, fix your view, then `3` again to restore. Far faster than the layer panel.

**4. Ruler muscle memory (Layout)**
`K` → click start → click end → read the DRC spacing instantly. `Shift+K` clears all rulers before a DRC run so the canvas stays clean.

**5. `Q` beats every Properties menu**
Select any object in schematic or layout and press `Q` — the Properties dialog opens instantly with no menu traversal.

**6. `G` in Innovus for net debugging**
Press `G`, type a net name (e.g. `VDD`, `clk`), and the view flies straight to it. Indispensable on a 5-million-cell design.

**7. `Shift+E` vs `E` in schematic hierarchy**
`E` descends read-only (safe for inspection). `Shift+E` descends in edit mode and lets you modify the child cell. Use `E` by default to avoid accidental edits to shared cells.

---

## Printable Reference

Save the keyboard diagram at the top of this page and print at A4/Letter size — colour laser preferred so the key-colour coding is clear.

*Need a deeper dive into the full ASIC flow? Read the [LibreLane open-source RTL-to-GDSII tutorial →]({% post_url 2026-05-12-librelane-tutorial-beginners %})*
