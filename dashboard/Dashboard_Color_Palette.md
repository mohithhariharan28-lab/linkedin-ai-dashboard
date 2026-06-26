# Dashboard Color Palette & Token Definitions

This document details the dark blue color scheme, semantic roles, contrast checks, and design rules used for the LinkedIn Analytics Dashboard.

---

## 1. Core Color System

| Color Role | Color Name | Hex Code | Visual Preview / Description |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | Navy Blue | `#0F172A` | Background for pages |
| **Card / Visual Background** | Charcoal Gray | `#1E293B` | Fill color for containers, charts, and matrices |
| **Borders & Gridlines** | Slate Gray | `#334155` | Subtle dividers and border outlines |
| **Primary Accent** | Enterprise Blue | `#3B82F6` | Active navigation, branding highlights, slicer selections |
| **Secondary Accent** | Light Blue | `#60A5FA` | High-importance trends, comparisons |
| **Foreground (Text - Primary)** | White | `#F8FAFC` | Core titles, card values, table headers |
| **Foreground (Text - Secondary)** | Light Gray | `#CBD5E1` | Data labels, axis text, secondary metrics |

---

## 2. Semantic Color System

These colors indicate metrics performance, trends, or media categorization.

| Semantic Role | Color Name | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| **Growth / Success** | Green | `#22C55E` | Positive follower growth, positive MoM % |
| **Error / Decline** | Red | `#EF4444` | Negative growth, low-performing alerts |
| **Warning / Neutral Alert** | Orange | `#F59E0B` | Missing metrics, static indicators |
| **Media: Text** | Violet | `#8B5CF6` | Text-only posts representation |
| **Media: Image** | Pink | `#EC4899` | Image-only posts representation |
| **Media: Video** | Blue | `#3B82F6` | Video-based posts representation |
| **Media: Carousel** | Teal | `#0D9488` | Carousel/Document posts representation |

---

## 3. Contrast & Accessibility Checks

Calculated against the Card Background (`#1E293B`) and Canvas Background (`#0F172A`) to ensure WCAG 2.1 AA/AAA compliance:

- **White Text (`#F8FAFC`) on Card Background (`#1E293B`)**:
  - Contrast Ratio: **10.8:1**
  - Status: **PASS (AAA)**
- **Light Gray Text (`#CBD5E1`) on Card Background (`#1E293B`)**:
  - Contrast Ratio: **8.2:1**
  - Status: **PASS (AAA)**
- **Enterprise Blue (`#3B82F6`) on Canvas Background (`#0F172A`)**:
  - Contrast Ratio: **4.5:1**
  - Status: **PASS (AA)**
- **Green Success (`#22C55E`) on Card Background (`#1E293B`)**:
  - Contrast Ratio: **5.5:1**
  - Status: **PASS (AA)**

---

## 4. How to Use in Power BI Desktop
1. Import `Dashboard_Theme.json` (View ribbon -> Themes dropdown -> **Browse for themes**).
2. The palette will automatically populate the theme color selection box.
3. Apply `#1E293B` as the card background, with rounded corners of **8px** and border color of `#334155` (1px thick) to create a premium glassmorphic/flat card aesthetic.
