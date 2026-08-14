"""Build a :class:`graphviz.Digraph` from a DiagramSpec + StyleTheme + EV result.

Graphviz is the layout engine *and* the export engine: it emits resolution-
independent SVG/PDF and high-DPI PNG, which is what keeps exported diagrams crisp
inside PowerPoint.
"""

from __future__ import annotations

from typing import Dict, Optional

import graphviz

from .ev import EVResult, format_currency
from .model import DiagramSpec, Node
from .themes import StyleTheme

# Friendly shape name -> Graphviz shape. Drives the per-role shape selectors in the UI.
SHAPE_CHOICES: Dict[str, str] = {
    "Rectangle": "box",
    "Circle": "circle",
    "Ellipse": "ellipse",
    "Diamond": "diamond",
    "Parallelogram": "parallelogram",
    "Hexagon": "hexagon",
    "Rounded tag": "cds",
    "Triangle": "triangle",
    "Cylinder": "cylinder",
    "Document": "note",
}
GV_TO_FRIENDLY: Dict[str, str] = {v: k for k, v in SHAPE_CHOICES.items()}

# Default Graphviz shape per role. (``decision`` is diamond in flowcharts — see shape_for.)
DEFAULT_ROLE_SHAPE: Dict[str, str] = {
    # decision tree
    "decision": "box",          # square-ish, sharp corners
    "chance": "circle",
    "terminal": "box",          # was "triangle" (text sat awkwardly); a rectangle reads cleaner
    # flowchart
    "start_end": "box",         # rounded via style -> stadium look
    "process": "box",           # rounded
    "io": "parallelogram",
    "document": "note",
    "database": "cylinder",
    # org / mind
    "box": "box",
    "mind": "ellipse",
}

# Roles whose boxes should always be rounded, regardless of theme.rounded
ALWAYS_ROUNDED = {"process", "start_end"}


def shape_for(node: Node, diagram_type: str = "", overrides: Optional[Dict[str, str]] = None) -> str:
    """Map a node's role to a Graphviz shape.

    Precedence: explicit per-role ``overrides`` > flowchart decision diamond >
    the role default. This lets the UI offer shape pickers while keeping sensible
    out-of-the-box shapes.
    """
    overrides = overrides or {}
    if node.role in overrides and overrides[node.role]:
        return overrides[node.role]
    if node.role == "decision" and diagram_type == "flowchart":
        return "diamond"
    return DEFAULT_ROLE_SHAPE.get(node.role, "box")


def _escape(text: str) -> str:
    """Graphviz uses \\ and quotes specially in labels; keep user text literal."""
    return (text or "").replace("\\", "\\\\").replace('"', '\\"')


def _node_label(node: Node, ev: EVResult, is_tree: bool, show_ev: bool, show_values: bool) -> str:
    """Compose a multi-line node label. EV / payoff are optional (see Labels toggles)."""
    lines = [_escape(node.label) if node.label else _escape(node.id)]
    if node.subtitle:
        lines.append(_escape(node.subtitle))

    if is_tree:
        if node.role == "terminal" and node.value is not None and show_values:
            lines.append(format_currency(node.value))
        elif show_ev and node.id in ev.values and node.role in ("decision", "chance"):
            lines.append(f"EV {format_currency(ev.values[node.id])}")

    return "\n".join(l for l in lines if l != "")


def _edge_label(label: str, probability: Optional[float], show_labels: bool, show_probs: bool) -> str:
    parts = []
    if label and show_labels:
        parts.append(_escape(label))
    if probability is not None and show_probs:
        parts.append(f"{probability * 100:.0f}%")
    return "\n".join(parts)


def build_graph(
    spec: DiagramSpec,
    theme: StyleTheme,
    ev: Optional[EVResult] = None,
    *,
    show_ev: bool = True,
    show_values: bool = True,
    show_edge_labels: bool = True,
    show_edge_probs: bool = True,
    shape_overrides: Optional[Dict[str, str]] = None,
    arrowheads: bool = True,
) -> graphviz.Digraph:
    is_tree = spec.diagram_type == "decision_tree"
    ev = ev if ev is not None else EVResult({}, set(), {}, [], [])

    dot = graphviz.Digraph("diagram", format="svg")
    dot.attr(
        rankdir=spec.rankdir,
        bgcolor=theme.background,
        splines="spline",
        pad="0.4",          # whitespace margin so nothing is cropped on paste
        nodesep="0.45",
        ranksep="0.55",
        fontname=theme.font_family,
    )

    # Optional title as a graph label at the top.
    if spec.title:
        dot.attr(
            label=_escape(spec.title),
            labelloc="t",
            fontsize=str(theme.title_font_size),
            fontname=theme.font_family,
            fontcolor=theme.text_color,
        )

    # Default node styling
    dot.attr(
        "node",
        fontname=theme.font_family,
        fontsize=str(theme.node_font_size),
        fontcolor=theme.text_color,
        color=theme.border_color,
        penwidth=str(theme.pen_width),
    )
    # Default edge styling. A small open "vee" arrowhead in the line color merges into
    # the connector instead of popping out as a heavy filled triangle at the box edge.
    dot.attr(
        "edge",
        fontname=theme.font_family,
        fontsize=str(theme.edge_font_size),
        color=theme.edge_color,
        fontcolor=theme.edge_color,
        penwidth=str(theme.pen_width),
        arrowsize="0.7",
        arrowhead="vee" if arrowheads else "none",
        dir="forward" if arrowheads else "none",
    )

    # Nodes
    for node in spec.nodes:
        shape = shape_for(node, spec.diagram_type, shape_overrides)
        styles = ["filled"]
        if shape == "box":
            if node.role in ALWAYS_ROUNDED or theme.rounded:
                styles.append("rounded")
        fill = node.fill or theme.fill_for(node.role)
        attrs = {
            "shape": shape,
            "style": ",".join(styles),
            "fillcolor": fill,
            "label": _node_label(node, ev, is_tree, show_ev, show_values),
        }
        if node.font_size is not None:
            attrs["fontsize"] = str(node.font_size)
        # Circles/ellipses read better with a little internal margin
        if shape in ("circle", "ellipse"):
            attrs["margin"] = "0.08"
        dot.node(node.id, **attrs)

    # Edges
    for e in spec.edges:
        is_optimal = (e.source, e.target) in ev.optimal_edges
        attrs = {
            "label": _edge_label(e.label, e.probability, show_edge_labels, show_edge_probs),
            "style": e.style or "solid",
        }
        if e.color:
            attrs["color"] = e.color
            attrs["fontcolor"] = e.color
        if is_optimal:
            attrs["color"] = theme.optimal_color
            attrs["fontcolor"] = theme.optimal_color
            attrs["penwidth"] = str(theme.pen_width + 1.4)
        dot.edge(e.source, e.target, **attrs)

    return dot
