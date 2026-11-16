# Linear Gauge Maker

A Python desktop application built with **Tkinter** and **Pillow (PIL)** that allows you to generate and customize linear gauges in real-time. It features Roblox-style color and transparency sequences (`ColorSequence` and `NumberSequence`), multi-zone support with independent per-zone sequences, center-line highlighting, live preview, custom font selection, preset management, and custom export path selection.

---

## Features

- **Live Preview Window:** Instantly view changes as you tweak parameters, values, and styles.
- **Roblox-Style Sequences (Per-Zone Support):**
  - **Color Sequence:** Define multi-point color gradients using time and RGB/Hex values, separated by `|` to match each zone (e.g., `0: #FF0000; 0.5: #FFFF00 | 0: #FFFF00; 0.5: #00FF00`).
  - **Transparency Sequence:** Control fade-ins and fade-outs across zones using time and transparency values, separated by `|` for individual zones (e.g., `0, 0 | 0.5, 1`).
- **Zone Management:** Define multiple independent or overlapping zone ranges (e.g., `0, 0.5; 0.5, 1`), adjust zone vertical offsets, and change zone thickness.
- **Custom Typography:** Support for custom `.ttf` fonts with adjustable font sizes and vertical offsets for titles and units.
- **Line & Tick Customization:** Adjust the baseline Y position, baseline line width, tick line width, and font sizes dynamically.
- **Tick Marks & Center Highlight:** Automatically calculates major and minor tick divisions with an optional highlighted center reference line.
- **Deferred Export (Save As):** Images are rendered in-memory during editing and only exported to disk when you explicitly click **Save Gauge File As...** and choose your destination path.
- **Preset Management:** Save, load, and delete your favorite gauge configurations locally using `gauge_presets.json`.

---

## Installation & Running

1. Clone or download this repository/script.
2. Place the project in your working directory.
3. Run the executable in `dist` named Linear Gauge Maker.
4. If Windows SmartScreen pops up, click 'Run Anyway'. This is not a virus, it's because the program isn't signed.
  
---

## How to Use Sequences & Zones

### 1. Multi-Zone Ranges (`Zones Ranges`)
Define multiple distinct gauge zones separated by semicolons:
```text
min, max; min, max
```
*Example:* `0, 0.5; 0.5, 1`

### 2. Color Sequence (`Color Sequence`)
Defines colors across the width of each zone from start (`0.0`) to end (`1.0`). Use `|` to assign separate sequences to each zone:
```text
time: color; time: color | time: color; time: color
```
*Example:* `0: #FF0000; 0.5: #FFFF00 | 0: #FFFF00; 0.5: #00FF00`

### 3. Transparency Sequence (`Transparency Sequence`)
Defines transparency across each zone where `0` is fully opaque and `1` is fully transparent, separated by `|` for each zone:
```text
time, transparency_value | time, transparency_value
```
*Example:* `0, 0; 0.5, 1 | 0, 0`

---

## Presets
All saved custom presets are automatically stored in a local file named `gauge_presets.json`. You can easily switch between presets using the dropdown menu at the top of the control panel, save new ones, or delete unwanted ones.

---
## Star History

<a href="https://www.star-history.com/?repos=theonewhobuilds1%2Flinear-gauge-maker&type=date&logscale=&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=theonewhobuilds1/linear-gauge-maker&type=timeline&theme=dark&logscale&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=theonewhobuilds1/linear-gauge-maker&type=timeline&logscale&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=theonewhobuilds1/linear-gauge-maker&type=timeline&logscale&legend=top-left" />
 </picture>
</a>
