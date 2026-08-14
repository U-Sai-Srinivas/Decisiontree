"""Diagram & Decision Studio — core package.

Modules:
    gv_setup   Ensure the Graphviz `dot` engine is available on PATH.
    model      Dataclasses (Node, Edge, DiagramSpec) + DataFrame/JSON (de)serialization.
    ev         Expected-Value engine for decision trees.
    themes     StyleTheme dataclass + preset palettes.
    render     Build a graphviz.Digraph from a DiagramSpec + StyleTheme.
    export     SVG / PNG / PDF / DOT / JSON export helpers.
    templates  Ready-to-load example diagrams.
"""

__all__ = [
    "gv_setup",
    "model",
    "ev",
    "themes",
    "render",
    "export",
    "templates",
]
