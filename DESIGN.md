# Architectural Design Specification: High-Contrast Geometric UI/UX System

> **Document Type:** Design System Specification & Implementation Blueprint  
> **Document Status:** Active Standard (v1.0)  
> **Target Audience:** UI/UX Engineers, Game Developers, Autonomous Agents, Graphic Artists  
> **Coordinate Space:** Normalized Screen Coordinates (Ursina `camera.ui` space $[-0.5, 0.5]$, 16:9 Safe Aspect)

---

## 1. Design Philosophy

### 1.1 Core Vision & Aesthetic Manifesto
This design system rejects conventional, subdued game user interfaces characterized by sterile rounded rectangles, glassmorphic blurs, and passive symmetrical grids. Instead, it establishes an **expressive, high-energy graphic interface** rooted in:
- **Pop-Art & Comic-Book Graphic Architecture:** Sharp outlines, hard solid shadows without blur, bold halftone textures, and uncompromising visual weight.
- **Editorial Typography & Dynamic Asymmetry:** Magazine-style layout composition, oversized typographic watermarks, angled dividing axes, and intentional visual tension.
- **Pure Geometric Primitives as Structural Anchors:** Interfaces are constructed strictly from fundamental Euclidean and affine forms—parallelograms, triangles, circles, and diagonal cuts.

```
       CONVENTIONAL UI                          THIS DESIGN SYSTEM
  ┌─────────────────────────┐               ╱──────────────────────────╱
  │  [Rounded Card]         │              ╱   ▲ HERO BADGE           ╱
  │  (Subtle drop shadow)   │             ╱   ────────────────────── ╱
  │  (Low-contrast gray)    │            ╱   ◢ BUTTON [SOLID INK] ◢ ╱
  └─────────────────────────┘           ╱──────────────────────────╱
      (Passive & Sterile)                    (Kinetic & Authoritative)
```

### 1.2 Psychological & Emotional Impact
The visual system communicates three distinct visceral sensations:
1. **Urgency & Momentum:** Diagonal axes and sheared planes create an inherent vector of forward movement, driving player momentum even in static menus.
2. **Tactile Decisiveness:** Every interactive element has physical, snappy resistance. Binary states (resting vs. pressed) are unmistakable, eliminating user hesitation.
3. **Intellectual Sharpness:** Crisp geometric boundaries mirror precision logic and tactical mastery. Every element earns its place with structural purpose; decorative noise is strictly prohibited.

---

## 2. Color Palette & Design Tokens

The color architecture is adapted directly from the project's foundational palette (`theme.py`), augmented with high-contrast graphic inks to achieve complete visual clarity across unlit flat-shaded rendering environments.

### 2.1 The Core Chromatic Palette

| Token Identifier | Hex Code | Color Name | Role & Semantic Purpose |
| :--- | :--- | :--- | :--- |
| `COLOR_CANVAS_WARM` | `#FFEECC` | Warm Cream | Base window clear canvas, paper-tone dialog backing, switch marks. |
| `COLOR_INK_DARK` | `#46425E` | Deep Slate Plum | Dominant ground, primary typography ink, high-contrast structural shapes. |
| `COLOR_TEAL_DEEP` | `#15788C` | Shadow Teal | Secondary structural framing, grid lines, heavy mechanism accents, backdrop layers. |
| `COLOR_CYAN_ELECTRIC`| `#00B9BE` | Electric Cyan | Primary dynamic action, interactive highlights, affirmative state feedback, power conduit. |
| `COLOR_PEACH_MUTED` | `#FFB0A3` | Soft Peach | Warning alerts, passive status indicator, secondary/idle paired entities. |
| `COLOR_CORAL_HERO` | `#FF6973` | Vivid Coral | Critical primary player accent, high-priority CTAs, urgency alarms, goal targets. |
| `COLOR_INK_BLACK` | `#1A1824` | Comic Ink Black | Absolute graphic outlines, hard drop-shadow blocks, maximum knockout depth. |
| `COLOR_WHITE_PURE` | `#FFFFFF` | Stark White | Knockout labels on dark surfaces, dynamic specular pips, high-impact flash frames. |

### 2.2 Semantic Interaction Tokens

```
=============================================================================
INTERACTION STATE MATRIX
=============================================================================
Element State        Surface Color        Border / Rim         Label Color
-----------------------------------------------------------------------------
Default (Resting)    COLOR_INK_DARK       COLOR_TEAL_DEEP      COLOR_CANVAS_WARM
Hovered / Focused    COLOR_CYAN_ELECTRIC  COLOR_WHITE_PURE     COLOR_INK_BLACK
Active / Depressed   COLOR_CORAL_HERO     COLOR_INK_BLACK      COLOR_WHITE_PURE
Disabled             COLOR_INK_DARK (40%) None                 COLOR_TEAL_DEEP (50%)
Selected / Active    COLOR_CORAL_HERO     COLOR_CANVAS_WARM    COLOR_INK_BLACK
=============================================================================
```

### 2.3 Opacity & Depth Modifiers
- `ALPHA_SOLID`: $1.00$ ($100\%$) — Default for all interactive cards and typography.
- `ALPHA_OVERLAY`: $0.94$ ($94\%$) — Modal backplates (`rgba32(255, 238, 204, 240)`), preventing background clutter while preserving board context.
- `ALPHA_MUTED`: $0.35$ ($35\%$) — Construction grid lines and ambient geometric lines (`rgba32(21, 120, 140, 90)`).
- `ALPHA_WATERMARK`: $0.08$–$0.12$ ($8\%-12\%$) — Large background typographic decals and oversized geometric watermarks.

---

## 3. Typography System

### 3.1 Typeface Architecture & Pairing
To definitively avoid sterile monospace/terminal aesthetics and project a contemporary, bold editorial pop identity, the typography relies on a curated pair of geometric sans-serif typefaces bundled directly in `fonts/`:

```
+------------------------------------+-------------------------------------------+
| Display & Headline Anchor          | Interactive UI & Telemetry Workhorse      |
+------------------------------------+-------------------------------------------+
| Unbounded ExtraBold                | Plus Jakarta Sans ExtraBold               |
| File: fonts/Unbounded-ExtraBold.ttf| File: fonts/PlusJakartaSans-ExtraBold.ttf |
| Trait: Wide, Monumental, Graphic   | Trait: Geometric, Crisp, High-Velocity    |
+------------------------------------+-------------------------------------------+
```

1. **Display & Impact Header Fonts:**
   - *Monoton Regular* (`fonts/Monoton-Regular.ttf`): Dedicated multi-line inline display face for the main title wordmark, bringing a distinct retro-pop, graphic editorial grandeur when rendered at monumental scales ($4.0\text{x}-4.5\text{x}$).
   - *Unbounded ExtraBold* (`fonts/Unbounded-ExtraBold.ttf`): Ultra-modern geometric sans-serif with wide extended proportions, heavy structural weight, and monumental graphic character for stage banners, victory accolades, level index numbers, and oversized background watermarks.
   - **Casing:** Strictly `UPPERCASE` or specialized title-case for stylized hero taglines.

2. **UI & Precision Interaction Font:** *Plus Jakarta Sans ExtraBold* (`fonts/PlusJakartaSans-ExtraBold.ttf`)
   - **Characteristics:** Contemporary geometric grotesque featuring clean circular bowls, generous apertures, and razor-sharp terminals. Unlike cold monospace fonts, it delivers high-density readability with lively, premium polish.
   - **Usage:** Menu navigation buttons, action cards, dialog narrative copy, HUD live metrics (move counters, elapsed time), solver telemetry, and keyboard hint labels.
   - **Casing:** Uppercase for buttons and telemetry tags; natural mixed-case for dialog instructions and key hints.

### 3.2 Typographic Hierarchy Scale

```
+------------------+---------------+---------------------+-----------+----------------------+
| Hierarchy Level  | Scale (ui)    | Font Asset          | Transform | Color Token          |
+------------------+---------------+---------------------+-----------+----------------------+
| Display Title    | 2.20 - 2.80   | Unbounded ExtraBold | -10° Skew | COLOR_INK_DARK       |
| Section Banner   | 1.30 - 1.60   | Unbounded ExtraBold | -8° Skew  | COLOR_CORAL_HERO     |
| Level Index (L#) | 1.10 - 1.30   | Unbounded ExtraBold | Upright   | COLOR_WHITE_PURE     |
| Component Header | 0.85 - 1.05   | Plus Jakarta Sans   | Upright   | COLOR_CANVAS_WARM    |
| Primary Button   | 0.70 - 0.80   | Plus Jakarta Sans   | -8° Skew  | COLOR_WHITE_PURE     |
| HUD Counter / Val| 0.65 - 0.75   | Plus Jakarta Sans   | Upright   | COLOR_CYAN_ELECTRIC  |
| Caption / Hint   | 0.45 - 0.55   | Plus Jakarta Sans   | Upright   | COLOR_TEAL_DEEP      |
| Watermark Decal  | 4.50 - 6.00   | Unbounded ExtraBold | -12° Skew | ALPHA_WATERMARK      |
+------------------+---------------+---------------------+-----------+----------------------+
```

### 3.3 Graphic Text Styling: Comic Pop Rules
- **Hard Solid Drop Shadows:** Text never uses soft Gaussian blur. Drop shadows are rendered via a duplicated text mesh offset at $(\Delta x = +0.008, \Delta y = -0.008)$ in normalized UI space, filled with `COLOR_INK_BLACK` or `COLOR_INK_DARK`.
- **Text Knockouts & Inverted Backing Bars:** Important labels are placed inside solid sheared rectangles. The text inherits the inverted color of the shape (e.g., `COLOR_INK_BLACK` text on a `COLOR_CYAN_ELECTRIC` backing plate).
- **Kinetic Shearing (Dynamic Slant):** Major headings and callouts are sheared along the horizontal axis by $-8^\circ$ to $-12^\circ$, generating visual acceleration toward the upper-right.

---

## 4. Geometry & Shapes

Every visual surface must be decomposable into four primary geometric primitives. Organic curves, rounded pill shapes, and soft continuous gradients are prohibited.

```
       PARALLELOGRAM                  TRIANGLE                      CIRCLE
  ┌──────────────────────╱              ▲                        ╭──────╮
 ╱                      ╱              ╱ ╲                      │   ●   │
╱──────────────────────┘              ▼───▼                      ╰──────╯
  (Actions, Cards, Tabs)       (Pointers, Alerts, Chevrons)   (Stamps, Rings, Badges)
```

### 4.1 Parallelograms (Sheared Quadrilaterals)
- **Geometry:** Rectangles sheared along the X-axis by an angle of $\theta = 10^\circ$ to $14^\circ$ ($\tan \theta \approx 0.176$ to $0.249$).
- **Role:** Interactive cards, menu buttons, dialog header ribbons, and HUD value containers.
- **Directionality:** Leftward slant (`/`) conveys forward velocity; rightward counter-slant (`\`) is reserved for cancellation or closure actions.

### 4.2 Triangles (Acute & Isosceles Primitives)
- **Geometry:** Sharp sharp-cornered polygons with acute angles ($30^\circ$, $45^\circ$, $60^\circ$).
- **Role:** 
  - Directional navigation arrows and selection carats.
  - Caution/hazard indicators flanking critical warning notifications.
  - Corner corner-flairs decorating rectangular containers.

### 4.3 Circles & Circular Annuli
- **Geometry:** Crisp circular discs and concentric ring frames.
- **Role:**
  - Status indicators (e.g., active vs. passive cube states, step indicators).
  - Numbered stage badges and circular lock icons.
  - Radial target reticles.

### 4.4 Diagonal Cuts & Chamfers (The Dynamic Slash)
- **Geometry:** Polygons derived from rectangles by cutting one or two opposite corners at a $45^\circ$ or $60^\circ$ chamfer.
- **Rule of Asymmetry:** Never cut all four corners equally. Cut either:
  - Top-right and bottom-left (kinetic flow), or
  - Top-left only (editorial index tab).

```
         KINETIC CUT                          TAB CHAMFER
     ┌───────────────────╱                ╱──────────────────┐
    ╱                   │                │                  │
   │                   ╱                 │                  │
  ╱───────────────────┘                  └──────────────────┘
```

---

## 5. Layout & Composition Architecture

### 5.1 The Break-the-Grid Doctrine
Traditional UI centers content inside neat, padded bounding boxes. This design system organizes space through **diagonal tension** and **asymmetric balance**:

```
0.5 -------------------------------------------------------------
    | [TOP-LEFT ANCHOR]                           [STATUS RETICLE]|
    |  \ STAGE BANNER \                                  ( O )    |
    |   \──────────────\                                          |
    |                                                             |
    |                   DIAGONAL COMPOSITION AXIS                 |
    |                      \                                      |
    |                       \       [FOCUS ZONE]                  |
    |                        \       3D PLAYFIELD                 |
    |                         \                                   |
    |                          \                                  |
    |                           \     [INTERACTION RAIL]          |
    |                            \     / ACTION 01 /              |
    | [TELEMETRY DOCK]            \   / ACTION 02 /               |
    |  [### MOVES: 024 ###]        \ / ACTION 03 /                |
-0.5 -------------------------------------------------------------
   -0.5                                                         0.5
```

1. **The Primary Thrust Line:** A dynamic vector traversing from $(X = -0.45, Y = 0.40)$ to $(X = 0.45, Y = -0.40)$. UI modules align along this axis.
2. **Asymmetric Counter-Weighting:** If a heavy title block occupies the top-left, the bottom-right must anchor the primary interaction block with an inverted color weight.
3. **Negative Space as Structural Form:** Large uninterrupted voids are deliberate design statements, representing the infinite void surrounding the playfield.

### 5.2 Layer Depth Model (UI Z-Stack)
All interface elements are positioned within Ursina's `camera.ui` coordinate system with strictly regulated Z-offsets:

```
Z = -0.05  [LAYER 4: POPUP FOREGROUND]    -> Dialog boxes, toast banners, alert modals
Z = -0.03  [LAYER 3: INTERACTIVE CARDS]   -> Buttons, tab ribbons, clickable menu cards
Z = -0.01  [LAYER 2: HUD & DECORATIONS]    -> Telemetry text, corner brackets, reticles
Z =  0.00  [LAYER 1: SCREEN PANELS]       -> Modal backdrop masks, halftone screen panels
Z = +0.05  [LAYER 0: BACKGROUND DECALS]    -> Oversized watermarks, parallax diagonal stripes
```
*Note: In the engine UI camera space, more negative Z values render in front of more positive Z values.*

---

## 6. UI Component Standards & Guidelines

### 6.1 Main Menu & Navigation Rail
- **Structure:** A vertically stacked, diagonally skewed card rail positioned on the right quadrant of the screen ($X \in [0.10, 0.40]$).
- **Item Construction:**
  - Base width: $0.32$ ui units; base height: $0.08$ ui units.
  - Shape: Parallelogram sheared by $-10^\circ$.
  - Resting fill: `COLOR_INK_DARK`, resting label: `COLOR_CANVAS_WARM`.
  - Right-aligned trailing indicator: Acute chevron triangle ($\blacktriangleright$).
- **Hover Sequence:**
  - Surface instantaneously snaps to `COLOR_CYAN_ELECTRIC`.
  - Label shifts to `COLOR_INK_BLACK`.
  - Item shifts $-0.02$ units along the horizontal axis, protruding into the central void.
- **Selected Sequence:**
  - Card pulses into `COLOR_CORAL_HERO` with a solid `COLOR_INK_BLACK` shadow stamp.

```
       RESTING STATE                           HOVER / ACTIVE STATE
   ┌──────────────────────╱                 ┌────────────────────────╱
  ╱   01  START CAMPAIGN ╱                 ╱ █ 01  START CAMPAIGN  ▲╱  <- Protrudes Left
 ╱                      ╱                 ╱                        ╱   <- Cyan/Coral Fill
╱──────────────────────┘                 ╱────────────────────────┘
```

### 6.2 Buttons & Interaction Controls
Every button consists of a two-piece mechanical assembly:
1. **The Solid Shadow Base:** A fixed, non-reactive sheared polygon in `COLOR_INK_BLACK` placed at $(X + 0.010, Y - 0.010, Z + 0.005)$.
2. **The Kinetic Face Plate:** The interactive polygon in `COLOR_INK_DARK` or `COLOR_CYAN_ELECTRIC`.

```
        RESTING (RAISED)                       PRESSED (BOTTOMED OUT)
       /══════════════════════/                      ......................
      /   CONFIRM ACTION     /                      /══════════════════════/
     /──────────────────────/                      /   CONFIRM ACTION     /
    //  (Black Shadow Base)//                     /──────────────────────/
   //                     //                     // (Face plate overlaps base)
```

- **Resting:** Face plate elevated above shadow base.
- **Hover:** Face plate expands by $104\%$ scale and shifts $+0.004$ units up and left.
- **Pressed:** Face plate translates directly into the shadow base $(\Delta x = +0.010, \Delta y = -0.010)$, creating a physical stamp effect.

### 6.3 Dialogs, Overlays & Modal Windows
- **Masking Panel:** Semi-opaque screen cover using `COLOR_CANVAS_WARM` at $94\%$ opacity (`ALPHA_OVERLAY`).
- **Frame Geometry:** Asymmetrical card with:
  - Top-left corner: $45^\circ$ diagonal cut ($0.06$ ui scale).
  - Bottom-right corner: $45^\circ$ diagonal cut ($0.06$ ui scale).
  - Top-right and bottom-left: Sharp $90^\circ$ right angles.
- **Header Banner:** An inverted solid strip (`COLOR_INK_DARK` or `COLOR_CORAL_HERO`) occupying the upper $18\%$ of the dialog height, housing the title in `COLOR_WHITE_PURE`.
- **Close / Dismiss Target:** A high-contrast circular button $(R = 0.025)$ bearing an inverted bold diagonal cross ($\times$) pinned to the top-right apex.

```
       /─────────────────────────────────────────────────┐
      /  [!] STAGE CLEARED                             [X]│  <- Header Banner (Solid)
     /───────────────────────────────────────────────────│
     │                                                   │
     │   RECORD TIME:    00:14.82                        │
     │   MOVES EXECUTED: 32                              │
     │                                                   │
     │           /═══════════════/   /═══════════════/   │
     │          /  RETRY LEVEL  /   /  NEXT STAGE   /    │
     │         /───────────────/   /───────────────/     │
     │                                                  /
     └─────────────────────────────────────────────────/
```

### 6.4 Heads-Up Display (HUD) Telemetry
The in-game telemetry floats as detached graphic elements around the playfield:
- **Level Designation (Top-Left):** Angled trapezoid badge with stage code (e.g., `L1-01`) in `COLOR_WHITE_PURE` on `COLOR_CORAL_HERO`, accompanied by the stage name in `COLOR_INK_DARK`.
- **Turn & Clock Dock (Bottom-Left):** High-density tabular layout. Numbers are scaled $1.4\times$ larger than their descriptive subtitles (`MOVES`, `TIME`).
- **Interactive Cube Indicator (Bottom-Center):** For multi-segment states, two interlocking geometric circles or lozenges:
  - Active segment: Bright `COLOR_CORAL_HERO` ring with spinning triangular tick.
  - Inactive segment: Muted `COLOR_PEACH_MUTED` solid pip.

---

## 7. Motion & Animation Rules

Animation is **snappy, mechanical, and impactful**. Gradual linear fades and slow floating easing curves are strictly forbidden.

### 7.1 Motion Timing Curves

```
1.0 ───────────────────────────────────────────/─── Settle
    │                                        ╱
0.8 │                                      ╱
0.6 │                                   ╱
0.4 │                                ╱
0.2 │                             ╱
0.0 ┼───────────────────────────╱────────────────── Launch
   0.00s                       0.12s              0.18s
    [       PUNCH PHASE       ] [   SETTLE PHASE   ]
```

- **Standard Snap (Action Response):** $0.12\text{s}$ to $0.18\text{s}$ duration using an **Overshoot Elastic Ease** (`out_back` or `out_expo`). The element accelerates instantly, slightly overshoots its target coordinate by $3-5\%$, and snaps back into place.
- **Screen Shutter Wipe (Scene Transitions):** $0.22\text{s}$ to $0.28\text{s}$. Multiple solid diagonal blades (`COLOR_INK_DARK`, `COLOR_CYAN_ELECTRIC`, `COLOR_CORAL_HERO`) sweep sequentially across the screen from top-right to bottom-left, fully occluding the scene before snapping open.
- **Micro-Interaction Hover:** $0.05\text{s}$ (effectively 3 frames at 60 FPS). Immediate visual response gives the interface a tactile, clicky feel.

### 7.2 Micro-Interaction Choreography

| Trigger Event | Visual Transform | Sound Profile Cue |
| :--- | :--- | :--- |
| **Element Hover** | $+4\%$ scale, $-0.02$ ui horizontal shift, Instant color swap | Crisp mechanical click / high tick |
| **Element Press** | $-4\%$ scale, down-right translation into shadow base | Solid thud / tactile strike |
| **Element Release** | Restores resting scale with $2\%$ rebound bounce | High-frequency snap |
| **Error / Invalid Action** | Horizontal 3-pulse angular jitter ($\pm 0.015$ ui, $0.10\text{s}$) | Low-frequency buzz / buzzer |
| **Stage Clear Fanfare** | Fullscreen flash (`COLOR_WHITE_PURE` for $0.04\text{s}$), followed by diagonal banner snap | Heavy cinematic bass drop |

---

## 8. Screen Construction Matrix & Blueprint Reference

To construct game screens adhering to this specification, developers must assemble components according to the layout formulas below:

```
=============================================================================
SCREEN: LEVEL TITLE / BOOT BANNER
=============================================================================
Element Name       Position (X, Y)      Geometry / Component    Palette Token
-----------------------------------------------------------------------------
Backdrop Watermark ( 0.00,  0.05 )      Oversized Display Text  COLOR_INK_DARK (8%)
Main Wordmark      (-0.02,  0.22 )      Sheared Text (-10°)     COLOR_CORAL_HERO
Tagline Ribbon     ( 0.00,  0.12 )      Parallelogram Bar       COLOR_INK_DARK
Play Action Card   ( 0.00, -0.04 )      Parallelogram Button    COLOR_CYAN_ELECTRIC
Quit Action Card   ( 0.00, -0.16 )      Parallelogram Button    COLOR_INK_DARK
Key Hint Anchor    ( 0.00, -0.32 )      Tabular Monospace Line  COLOR_TEAL_DEEP

=============================================================================
SCREEN: IN-GAME HUD OVERLAY
=============================================================================
Element Name       Position (X, Y)      Geometry / Component    Palette Token
-----------------------------------------------------------------------------
Stage ID Notch     (-0.42,  0.42 )      Chamfered Hexagon Tag   COLOR_CORAL_HERO
Stage Name Label   (-0.30,  0.42 )      Display Heading         COLOR_INK_DARK
Step Telemetry     (-0.40, -0.42 )      Solid Dual-Box Plate    COLOR_INK_DARK
Algorithm Panel    ( 0.40, -0.42 )      Diagonal Ribbon Tray    COLOR_TEAL_DEEP
Active Cube PIP    ( 0.00, -0.42 )      Concentric Ring Reticle COLOR_CORAL_HERO
=============================================================================
```

---

## 9. Implementation Checklist for Agents and Developers

Before submitting or certifying any UI code or screen redesign, verify compliance against this checklist:

1. [ ] **Palette Fidelity:** Are all visible surfaces assigned explicitly to the defined palette tokens? Are arbitrary hex values eliminated?
2. [ ] **Zero Unlit Deviations:** Does every 3D UI entity use `unlit_shader` to guarantee pure flat color rendering without artificial light degradation?
3. [ ] **No Generic Rounded Rectangles:** Are all containers constructed from parallelograms, triangles, circles, or diagonal-cut polygons?
4. [ ] **Contrast Verification:** Does every text element have an absolute contrast ratio $\ge 7:1$ against its immediate backing geometry?
5. [ ] **Sharp Solid Shadows:** Are all drop shadows solid, zero-blur geometric blocks offset diagonally?
6. [ ] **Kinetic Typography:** Are major headlines sheared by $-8^\circ$ to $-12^\circ$ to reinforce the dynamic vector?
7. [ ] **Tactile Snapping:** Are button interaction transitions configured under $0.18\text{s}$ using snappy overshoot easing?
8. [ ] **Safe-Zone Conformance:** Are all vital HUD indicators confined within the normalized $[-0.45, 0.45]$ safe-frame zone to ensure display integrity across arbitrary aspect ratios?
