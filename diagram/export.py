"""Export a rendered diagram to PowerPoint-friendly formats.

Priority order for slides:
    SVG  — true vector; PowerPoint 2016+ inserts it natively and it never pixelates.
    PDF  — vector; great for print/share.
    PNG  — high-DPI raster fallback (300 DPI) for older tools.
Plus DOT and JSON for portability / version control.
"""

from __future__ import annotations

import re

import graphviz

from .model import DiagramSpec

DEFAULT_PNG_DPI = 300


def slugify(text: str, default: str = "diagram") -> str:
    """Filesystem-friendly base name from a title."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or default


def to_svg_bytes(dot: graphviz.Digraph) -> bytes:
    return dot.pipe(format="svg")


def to_pdf_bytes(dot: graphviz.Digraph) -> bytes:
    return dot.pipe(format="pdf")


def to_png_bytes(dot: graphviz.Digraph, dpi: int = DEFAULT_PNG_DPI) -> bytes:
    """Render PNG at high DPI (default 300) so it never looks pixelated on a slide.

    Temporarily sets the graph ``dpi`` attribute and restores the previous value,
    so the on-screen render is left untouched.
    """
    prev = dot.graph_attr.get("dpi")
    dot.attr(dpi=str(dpi))
    try:
        return dot.pipe(format="png")
    finally:
        if prev is None:
            dot.graph_attr.pop("dpi", None)
        else:
            dot.graph_attr["dpi"] = prev


def to_dot_source(dot: graphviz.Digraph) -> str:
    return dot.source


def to_json(spec: DiagramSpec) -> str:
    return spec.to_json()
