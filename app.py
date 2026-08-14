"""Diagram & Decision Studio — a Streamlit app for building executive-ready
decision trees, flowcharts, and org/mind maps, with crisp SVG/PNG/PDF export.

Run locally:   streamlit run app.py
"""

from __future__ import annotations

import graphviz
import streamlit as st

from diagram import gv_setup
from diagram import export as export_mod
from diagram import templates as tpl
from diagram.ev import compute_ev, format_currency
from diagram.model import (
    DIAGRAM_TYPES,
    EDGE_STYLES,
    RANKDIRS,
    ROLE_LABELS,
    ROLES_BY_TYPE,
    DiagramSpec,
)
from diagram.render import build_graph
from diagram.themes import get_theme, preset_names

# --------------------------------------------------------------------------------------
# Page + engine setup
# --------------------------------------------------------------------------------------

st.set_page_config(
    page_title="Diagram & Decision Studio",
    page_icon="🗺️",
    layout="wide",
)

DOT_AVAILABLE = gv_setup.ensure_graphviz_on_path()

FONT_CHOICES = ["Helvetica", "Arial", "Times New Roman", "Courier New", "Verdana", "Georgia"]


# --------------------------------------------------------------------------------------
# Cached export rendering (keyed by DOT source so slider drags stay snappy)
# --------------------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _pipe(source: str, fmt: str) -> bytes:
    return graphviz.Source(source).pipe(format=fmt)


def _with_dpi(source: str, dpi: int) -> str:
    """Inject a graph-level dpi attribute (used for high-res PNG export)."""
    idx = source.find("{")
    if idx == -1:
        return source
    return source[: idx + 1] + f"\n\tgraph [dpi={dpi}]\n" + source[idx + 1 :]


# --------------------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------------------


def _load_spec(spec: DiagramSpec) -> None:
    """Replace the working diagram with `spec` and reset the data editors."""
    nodes_df, edges_df = spec.to_frames()
    st.session_state.diagram_type = spec.diagram_type
    st.session_state.title = spec.title
    st.session_state.rankdir = spec.rankdir
    st.session_state.theme_name = spec.theme_name if spec.theme_name in preset_names() else "Executive Slate"
    st.session_state.nodes_df = nodes_df
    st.session_state.edges_df = edges_df
    st.session_state.data_nonce = st.session_state.get("data_nonce", 0) + 1


if "diagram_type" not in st.session_state:
    _load_spec(tpl.default_spec())


# --------------------------------------------------------------------------------------
# Sidebar — controls
# --------------------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🗺️ Diagram Studio")

    # ---- Diagram type -----------------------------------------------------------
    type_keys = list(DIAGRAM_TYPES.keys())
    new_type = st.selectbox(
        "Diagram type",
        options=type_keys,
        index=type_keys.index(st.session_state.diagram_type),
        format_func=lambda k: DIAGRAM_TYPES[k],
        help="Switching type loads a starter template for that type.",
    )
    if new_type != st.session_state.diagram_type:
        first = tpl.template_names(new_type)
        _load_spec(tpl.build_template(new_type, first[0]) if first else tpl.default_spec())
        st.rerun()

    # ---- Templates --------------------------------------------------------------
    with st.expander("📚 Templates", expanded=True):
        names = tpl.template_names(st.session_state.diagram_type)
        if names:
            chosen = st.selectbox("Starter templates", names, key="template_choice")
            if st.button("Load template", width="stretch"):
                _load_spec(tpl.build_template(st.session_state.diagram_type, chosen))
                st.rerun()
        st.caption("New to this? Load a template to see how it works.")

    # ---- Theme ------------------------------------------------------------------
    st.markdown("### 🎨 Style")
    theme_name = st.selectbox(
        "Theme preset",
        preset_names(),
        index=preset_names().index(st.session_state.get("theme_name", "Executive Slate")),
    )
    st.session_state.theme_name = theme_name
    theme = get_theme(theme_name)

    with st.expander("Customize colors, fonts & shapes"):
        theme.font_family = st.selectbox(
            "Font family",
            FONT_CHOICES,
            index=FONT_CHOICES.index(theme.font_family) if theme.font_family in FONT_CHOICES else 0,
            help="Embedded in the export so text stays crisp in PowerPoint.",
        )
        c1, c2 = st.columns(2)
        with c1:
            theme.node_font_size = st.slider("Node font (pt)", 10, 32, int(theme.node_font_size))
            theme.title_font_size = st.slider("Title font (pt)", 12, 40, int(theme.title_font_size))
        with c2:
            theme.edge_font_size = st.slider("Edge font (pt)", 8, 24, int(theme.edge_font_size))
            theme.pen_width = st.slider("Border width", 0.5, 4.0, float(theme.pen_width), 0.1)
        theme.rounded = st.checkbox("Rounded boxes", value=theme.rounded)

        st.markdown("**Palette**")
        theme.background = st.color_picker("Background", theme.background)
        pc1, pc2 = st.columns(2)
        with pc1:
            theme.border_color = st.color_picker("Node border", theme.border_color)
            theme.edge_color = st.color_picker("Edges", theme.edge_color)
        with pc2:
            theme.text_color = st.color_picker("Text", theme.text_color)
            theme.optimal_color = st.color_picker("Optimal path", theme.optimal_color)

        st.markdown("**Node fill by role**")
        for role in ROLES_BY_TYPE[st.session_state.diagram_type]:
            theme.fills[role] = st.color_picker(
                ROLE_LABELS.get(role, role),
                theme.fill_for(role),
                key=f"fill_{role}",
            )

    # ---- Layout -----------------------------------------------------------------
    with st.expander("📐 Layout"):
        rankdir = st.radio(
            "Direction",
            options=list(RANKDIRS.keys()),
            index=list(RANKDIRS.keys()).index(st.session_state.rankdir),
            format_func=lambda k: RANKDIRS[k],
            horizontal=True,
        )
        st.session_state.rankdir = rankdir

    # ---- Save / Load ------------------------------------------------------------
    with st.expander("💾 Save / Load"):
        uploaded = st.file_uploader("Load a saved .json diagram", type=["json"])
        if uploaded is not None:
            try:
                _load_spec(DiagramSpec.from_json(uploaded.getvalue().decode("utf-8")))
                st.success("Diagram loaded.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - surface any parse error kindly
                st.error(f"Couldn't read that file: {exc}")


# --------------------------------------------------------------------------------------
# Main — title + tabs
# --------------------------------------------------------------------------------------

st.session_state.title = st.text_input("Diagram title", value=st.session_state.title)

if not DOT_AVAILABLE:
    st.warning(
        "The Graphviz **dot** engine wasn't found, so file exports are disabled. "
        "The live preview still works. Install Graphviz "
        "([download](https://graphviz.org/download/)) and restart to enable SVG/PNG/PDF export.",
        icon="⚠️",
    )

edit_tab, preview_tab = st.tabs(["✏️  Edit", "👁️  Preview & Export"])

# ---- Edit tab: node & edge tables ----------------------------------------------------
with edit_tab:
    roles = ROLES_BY_TYPE[st.session_state.diagram_type]
    is_tree = st.session_state.diagram_type == "decision_tree"

    st.markdown("#### Nodes")
    st.caption("Each node needs a short **ID** (e.g. `A`, `start`). Edges reference these IDs.")
    node_cfg = {
        "id": st.column_config.TextColumn("ID", required=True, width="small"),
        "label": st.column_config.TextColumn("Label", width="medium"),
        "role": st.column_config.SelectboxColumn("Role", options=roles, required=True),
        "value": st.column_config.NumberColumn(
            "Value ($)", help="Payoff/cost — for terminal nodes in a decision tree.", step=1000, format="%.0f"
        ),
        "subtitle": st.column_config.TextColumn("Subtitle"),
        "fill": st.column_config.TextColumn("Fill (hex)", help="e.g. #4f46e5 — blank uses the theme color."),
        "font_size": st.column_config.NumberColumn("Font", help="Per-node font size override (pt).", min_value=8, max_value=60, step=1),
    }
    if not is_tree:
        # Value/EV only meaningful for decision trees; hide to reduce clutter.
        node_cfg.pop("value")
    nodes_df = st.data_editor(
        st.session_state.nodes_df,
        column_config=node_cfg,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key=f"nodes_editor_{st.session_state.data_nonce}",
    )
    st.session_state.nodes_df = nodes_df

    st.markdown("#### Connections")
    edge_cfg = {
        "source": st.column_config.TextColumn("From (ID)", required=True),
        "target": st.column_config.TextColumn("To (ID)", required=True),
        "label": st.column_config.TextColumn("Label", width="medium"),
        "probability": st.column_config.NumberColumn(
            "Probability", help="0–1, for chance branches. Each chance node's branches should sum to 1.",
            min_value=0.0, max_value=1.0, step=0.05, format="%.2f",
        ),
        "style": st.column_config.SelectboxColumn("Line style", options=EDGE_STYLES),
        "color": st.column_config.TextColumn("Color (hex)"),
    }
    if not is_tree:
        edge_cfg.pop("probability")
    edges_df = st.data_editor(
        st.session_state.edges_df,
        column_config=edge_cfg,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key=f"edges_editor_{st.session_state.data_nonce}",
    )
    st.session_state.edges_df = edges_df

# ---- Build the current spec + EV -----------------------------------------------------
spec = DiagramSpec.from_frames(
    diagram_type=st.session_state.diagram_type,
    title=st.session_state.title,
    theme_name=st.session_state.theme_name,
    rankdir=st.session_state.rankdir,
    nodes_df=st.session_state.nodes_df,
    edges_df=st.session_state.edges_df,
)
ev = compute_ev(spec)

# General validation: edges pointing at non-existent node IDs.
node_ids = {n.id for n in spec.nodes}
dangling = [
    f"{e.source} → {e.target}"
    for e in spec.edges
    if e.source not in node_ids or e.target not in node_ids
]

# ---- Preview tab ---------------------------------------------------------------------
with preview_tab:
    if not spec.nodes:
        st.info("No nodes yet — add rows in the **Edit** tab or load a template.")
    else:
        # Decision-tree summary card
        if spec.diagram_type == "decision_tree":
            primary = next((r for r in ev.roots if r in node_ids), None)
            cols = st.columns(3)
            if primary is not None:
                cols[0].metric("Tree Expected Value", format_currency(ev.values.get(primary)))
                rec = ev.optimal_choice.get(primary)
                cols[1].metric("Recommended choice", rec if rec else "—")
            cols[2].metric("Nodes / Connections", f"{len(spec.nodes)} / {len(spec.edges)}")

        # Warnings
        for w in ev.warnings:
            st.warning(w, icon="⚠️")
        if dangling:
            st.error("Connections reference unknown node IDs: " + ", ".join(dangling), icon="🚫")

        # Render
        try:
            dot = build_graph(spec, theme, ev)
            st.graphviz_chart(dot, width="stretch")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Couldn't render the diagram: {exc}")
            dot = None

        # ---- Export ------------------------------------------------------------
        st.markdown("### ⬇️ Export for PowerPoint")
        st.caption(
            "**SVG** is recommended — it's true vector, so it stays razor-sharp at any size "
            "in PowerPoint (Insert → Pictures → This Device)."
        )
        base = export_mod.slugify(spec.title)
        if dot is not None and DOT_AVAILABLE:
            source = dot.source
            try:
                ecols = st.columns(5)
                ecols[0].download_button(
                    "SVG (vector)", _pipe(source, "svg"), file_name=f"{base}.svg",
                    mime="image/svg+xml", width="stretch", type="primary",
                )
                ecols[1].download_button(
                    "PNG (300 dpi)", _pipe(_with_dpi(source, export_mod.DEFAULT_PNG_DPI), "png"),
                    file_name=f"{base}.png", mime="image/png", width="stretch",
                )
                ecols[2].download_button(
                    "PDF (vector)", _pipe(source, "pdf"), file_name=f"{base}.pdf",
                    mime="application/pdf", width="stretch",
                )
                ecols[3].download_button(
                    "DOT", source, file_name=f"{base}.dot",
                    mime="text/vnd.graphviz", width="stretch",
                )
                ecols[4].download_button(
                    "JSON", spec.to_json(), file_name=f"{base}.json",
                    mime="application/json", width="stretch",
                )
            except graphviz.ExecutableNotFound:
                st.error("Graphviz engine not found — install it to enable exports.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Export failed: {exc}")
        else:
            # Even without the dot engine, the diagram is still portable as JSON/DOT text.
            st.download_button(
                "JSON (portable)", spec.to_json(), file_name=f"{base}.json",
                mime="application/json",
            )
