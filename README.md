# 🗺️ Diagram & Decision Studio

A Streamlit app for building **executive-ready diagrams** — decision trees (with
Expected-Value math), process flowcharts, and org charts / mind maps — and
exporting them to **PowerPoint-friendly, resolution-independent** files.

Built for higher-level meetings: clean styling, sensible slide-sized fonts, and
**true vector SVG** export that never pixelates when you drop it on a slide.

---

## What it does

- **Three diagram types**
  - **Decision Tree** — Decision (▢, takes the *max* of its branches), Chance (◯,
    *probability-weighted* average), and Terminal (△, a payoff/cost). Every node shows
    its rolled-up **Expected Value**, and the **optimal path is highlighted**.
  - **Process Flow / Flowchart** — start/end, process, decision (◇), I/O, document,
    database shapes.
  - **Org Chart / Mind Map** — hierarchical boxes and center-out idea maps.
- **Auto-layout** via Graphviz — you fill in simple node/connection tables, the app
  arranges everything.
- **Full styling control** — 3 theme presets plus custom colors, fonts, font sizes,
  border widths, rounded corners, and per-role fill colors.
- **Templates gallery** — realistic, pre-filled examples (Make vs. Buy, Product Launch,
  Litigation Settlement, an approval flow, an org chart, and a mind map).
- **Export** — **SVG** (vector, recommended), **PNG @ 300 dpi**, **PDF** (vector),
  plus **DOT** and **JSON** for portability / version control. Exports have a solid
  white background and no app chrome.
- **Save / Load** diagrams as `.json`.

## Why SVG for slides?

PowerPoint 2016+ inserts SVG natively (**Insert → Pictures → This Device**), keeps it
sharp at any zoom, and can even *Convert to Shapes* for editing. PNG is provided at
300 dpi as a fallback for older tools.

---

## Run locally

1. **Install the Graphviz system engine** (the `dot` binary — this is separate from the
   Python package):
   - **Windows:** download the installer from <https://graphviz.org/download/> (or a
     portable zip). The app also auto-detects a portable copy unzipped under
     `%LOCALAPPDATA%\Graphviz\...`.
   - **macOS:** `brew install graphviz`
   - **Linux:** `sudo apt-get install graphviz`
2. **Install Python deps:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run:**
   ```bash
   streamlit run app.py
   ```

> The live **preview** renders in the browser and works even without the local `dot`
> engine. **File export** (SVG/PNG/PDF) requires the Graphviz `dot` binary.

## Deploy to Streamlit Community Cloud

Push this folder to a GitHub repo and point Streamlit Cloud at `app.py`. The included
[`packages.txt`](packages.txt) (containing `graphviz`) installs the system engine
automatically, and [`requirements.txt`](requirements.txt) installs the Python deps.

---

## Project layout

```
app.py                 Streamlit UI (sidebar controls, tables, preview, export)
diagram/
  gv_setup.py          Finds/loads the Graphviz `dot` engine
  model.py             Node / Edge / DiagramSpec + DataFrame & JSON (de)serialization
  ev.py                Expected-Value engine for decision trees
  themes.py            StyleTheme dataclass + preset palettes
  render.py            Builds a graphviz.Digraph from a spec + theme + EV
  export.py            SVG / PNG / PDF / DOT / JSON helpers
  templates.py         Ready-to-load example diagrams
requirements.txt       Python dependencies
packages.txt           System dependency for Streamlit Cloud (graphviz)
sample_diagrams/       Example .json diagrams you can load in-app
```

## Tips for great-looking slides

- Keep node **font size ~14–18pt** and edge labels **~11–13pt** (defaults are already in
  this range) so text is readable when projected.
- Export **SVG** first; only fall back to PNG if a tool can't take SVG.
- Use the **Optimal path** color to make the recommended decision pop for executives.
