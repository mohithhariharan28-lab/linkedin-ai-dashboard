# Dashboard Typography Guidelines & Font Hierarchy

This document defines the typography guidelines, font size scales, weights, and styling parameters applied across the Power BI report pages.

---

## 1. Font Family System
Power BI Desktop relies primarily on system fonts. To guarantee visual consistency across web rendering and desktop instances, we use:

- **Primary Font Family**: `Segoe UI` (default for readable labels, table items, and axis markings)
- **Header Font Family**: `Segoe UI Semibold` or `Segoe UI Bold` (gives structure to titles and visual labels)
- **Monospace Font Family (Optional)**: `Courier New` (only for raw ID listing tooltips or schema metrics)

---

## 2. Typography Hierarchy

| Component | Font Family | Size (pt) | Weight / Style | Color Value | Usage / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Page Title** | Segoe UI Semibold | `20 pt` | Semibold | `#FFFFFF` | Main dashboard header (top-left) |
| **Visual Header Title** | Segoe UI Semibold | `12 pt` | Semibold | `#FFFFFF` | Title above individual charts and lists |
| **KPI Callout Value** | Segoe UI Bold | `28 pt` | Bold | `#FFFFFF` | Core numeric value inside Cards |
| **KPI Category Label** | Segoe UI | `10 pt` | Regular | `#94A3B8` | Subtitle detailing KPI name below value |
| **Table Header** | Segoe UI Semibold | `10 pt` | Semibold | `#FFFFFF` | Columns naming inside tables/matrices |
| **Table Values** | Segoe UI | `9 pt` | Regular | `#F8FAFC` | Data records displayed inside tables |
| **Chart Axis Labels** | Segoe UI | `9 pt` | Regular | `#94A3B8` | X and Y axis markings |
| **Chart Legend Text** | Segoe UI | `9 pt` | Regular | `#F8FAFC` | Text displaying categorization keys |
| **Tooltip Value** | Segoe UI | `9 pt` | Regular | `#FFFFFF` | Hover metadata box contents |

---

## 3. Formatting Parameters in Power BI Settings

For the best look, configure font visual scaling inside Power BI Desktop with these adjustments:

### A. KPI Cards
- **Callout value**: Text size = `28` | Bold | Alignment = `Center` | Font Color = `#FFFFFF`.
- **Category label**: Text size = `10` | Font Color = `#94A3B8` | Spacing above/below value = `2px`.

### B. Bar and Line Charts
- **X-Axis / Y-Axis**: Title = Off | Text size = `9` | Color = `#94A3B8` | Gridlines = Dotted, `#334155` (0.5px).
- **Data Labels**: Position = Auto | Text size = `9` | Bold | Color = `#F8FAFC` | Background = Off.

### C. Tables & Matrices
- **Style Preset**: None (Manual Formatting)
- **Column headers**: Font size = `10` | Bold | Header background = `#0F172A` | Gridlines = Horizontal only, `#334155`.
- **Values**: Font size = `9` | Row background = `#1E293B` | Alternate row background = `#1E293B`.
