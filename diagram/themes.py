"""Visual themes: colors, fonts, and sizing presets.

A :class:`StyleTheme` is everything the renderer needs about *looks*. Structural
shape choices (square vs. circle vs. diamond) live in ``render.py`` because they
depend on a node's role, not on the palette.

Font-size defaults are deliberately chosen to read well when a diagram is dropped
onto a projected slide: node labels ~16pt, edge labels ~12pt, title ~22pt.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class StyleTheme:
    name: str
    font_family: str
    node_font_size: float
    edge_font_size: float
    title_font_size: float
    background: str          # graph background (white for clean slide exports)
    border_color: str        # node border
    edge_color: str          # default edge / arrow color
    optimal_color: str       # highlight for the optimal decision path
    text_color: str          # node label text
    pen_width: float         # border thickness
    rounded: bool            # round the corners of generic boxes
    fills: Dict[str, str] = field(default_factory=dict)  # role -> fill color

    def copy(self) -> "StyleTheme":
        return deepcopy(self)

    def fill_for(self, role: str) -> str:
        return self.fills.get(role, self.fills.get("_default", "#ffffff"))


# Fill colors shared as a base, then tinted per preset. Every role has an entry so
# there are never "missing color" surprises.
def _fills(default, decision, chance, terminal, process, accent, soft) -> Dict[str, str]:
    return {
        "_default": default,
        # decision tree
        "decision": decision,
        "chance": chance,
        "terminal": terminal,
        # flowchart
        "start_end": accent,
        "process": process,
        "io": soft,
        "document": soft,
        "database": soft,
        # org / mind
        "box": process,
        "mind": soft,
    }


PRESETS: Dict[str, StyleTheme] = {
    "Executive Slate": StyleTheme(
        name="Executive Slate",
        font_family="Helvetica",
        node_font_size=16,
        edge_font_size=12,
        title_font_size=22,
        background="#ffffff",
        border_color="#475569",   # slate-600
        edge_color="#64748b",     # slate-500
        optimal_color="#4f46e5",  # indigo-600
        text_color="#0f172a",     # slate-900
        pen_width=1.4,
        rounded=True,
        fills=_fills(
            default="#f1f5f9",     # slate-100
            decision="#e2e8f0",    # slate-200
            chance="#eef2ff",      # indigo-50
            terminal="#dcfce7",    # green-100
            process="#f1f5f9",
            accent="#e0e7ff",      # indigo-100
            soft="#f8fafc",        # slate-50
        ),
    ),
    "Boardroom Blue": StyleTheme(
        name="Boardroom Blue",
        font_family="Helvetica",
        node_font_size=16,
        edge_font_size=12,
        title_font_size=22,
        background="#ffffff",
        border_color="#1e3a8a",   # blue-900
        edge_color="#3b82f6",     # blue-500
        optimal_color="#0ea5e9",  # sky-500
        text_color="#0c1e3e",
        pen_width=1.6,
        rounded=True,
        fills=_fills(
            default="#eff6ff",     # blue-50
            decision="#dbeafe",    # blue-100
            chance="#e0f2fe",      # sky-100
            terminal="#cffafe",    # cyan-100
            process="#eff6ff",
            accent="#bfdbfe",      # blue-200
            soft="#f0f9ff",        # sky-50
        ),
    ),
    "Minimal Mono": StyleTheme(
        name="Minimal Mono",
        font_family="Helvetica",
        node_font_size=16,
        edge_font_size=12,
        title_font_size=22,
        background="#ffffff",
        border_color="#111827",   # gray-900
        edge_color="#374151",     # gray-700
        optimal_color="#111827",
        text_color="#111827",
        pen_width=1.4,
        rounded=False,
        fills=_fills(
            default="#ffffff",
            decision="#f3f4f6",    # gray-100
            chance="#ffffff",
            terminal="#e5e7eb",    # gray-200
            process="#f9fafb",     # gray-50
            accent="#e5e7eb",
            soft="#ffffff",
        ),
    ),
}


def preset_names() -> List[str]:
    return list(PRESETS.keys())


def get_theme(name: str) -> StyleTheme:
    """Return a *copy* of the named preset (so per-session tweaks don't mutate globals)."""
    return PRESETS.get(name, PRESETS["Executive Slate"]).copy()
