"""Data model for a diagram, plus conversions to/from pandas DataFrames and JSON.

A single :class:`DiagramSpec` drives every diagram type. Nodes carry a short,
user-controlled ``id`` (e.g. ``"A"``, ``"start"``) so the edge table can reference
them in a human-friendly way inside ``st.data_editor``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

import pandas as pd

# --------------------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------------------

# diagram_type -> human label (shown in the UI selector)
DIAGRAM_TYPES: Dict[str, str] = {
    "decision_tree": "Decision Tree (with EV math)",
    "flowchart": "Process Flow / Flowchart",
    "org_mindmap": "Org Chart / Mind Map",
}

# Which node roles are offered for each diagram type
ROLES_BY_TYPE: Dict[str, List[str]] = {
    "decision_tree": ["decision", "chance", "terminal"],
    "flowchart": ["start_end", "process", "decision", "io", "document", "database"],
    "org_mindmap": ["box", "mind"],
}

# role -> friendly label (used in help text / summaries)
ROLE_LABELS: Dict[str, str] = {
    "decision": "Decision (takes MAX of children)",
    "chance": "Chance (probability-weighted)",
    "terminal": "Terminal (payoff / cost)",
    "start_end": "Start / End",
    "process": "Process step",
    "io": "Input / Output",
    "document": "Document",
    "database": "Database",
    "box": "Box",
    "mind": "Mind node",
}

EDGE_STYLES: List[str] = ["solid", "dashed", "dotted", "bold"]
RANKDIRS: Dict[str, str] = {"TB": "Top → Bottom", "LR": "Left → Right"}

# DataFrame column order (kept stable so st.data_editor is predictable)
NODE_COLUMNS: List[str] = ["id", "label", "role", "value", "subtitle", "fill", "font_size"]
EDGE_COLUMNS: List[str] = ["source", "target", "label", "probability", "style", "color"]


# --------------------------------------------------------------------------------------
# Dataclasses
# --------------------------------------------------------------------------------------


@dataclass
class Node:
    id: str
    label: str = ""
    role: str = "process"
    value: Optional[float] = None      # terminal payoff / cost
    subtitle: str = ""
    fill: Optional[str] = None         # hex override, else theme default
    font_size: Optional[float] = None  # per-node override, else theme default


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    probability: Optional[float] = None  # chance-branch probability (0..1)
    style: str = "solid"
    color: Optional[str] = None


@dataclass
class DiagramSpec:
    diagram_type: str = "decision_tree"
    title: str = "Untitled Diagram"
    theme_name: str = "Executive Slate"
    rankdir: str = "TB"
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    # ---- JSON ------------------------------------------------------------------
    def to_json(self) -> str:
        return json.dumps(
            {
                "diagram_type": self.diagram_type,
                "title": self.title,
                "theme_name": self.theme_name,
                "rankdir": self.rankdir,
                "nodes": [asdict(n) for n in self.nodes],
                "edges": [asdict(e) for e in self.edges],
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, text: str) -> "DiagramSpec":
        data = json.loads(text)
        nodes = [Node(**_filter_keys(n, Node)) for n in data.get("nodes", [])]
        edges = [Edge(**_filter_keys(e, Edge)) for e in data.get("edges", [])]
        return cls(
            diagram_type=data.get("diagram_type", "decision_tree"),
            title=data.get("title", "Untitled Diagram"),
            theme_name=data.get("theme_name", "Executive Slate"),
            rankdir=data.get("rankdir", "TB"),
            nodes=nodes,
            edges=edges,
        )

    # ---- DataFrames (for st.data_editor) ---------------------------------------
    def to_frames(self):
        """Return (nodes_df, edges_df) with stable columns and dtypes."""
        node_rows = [
            {
                "id": n.id,
                "label": n.label,
                "role": n.role,
                "value": _to_float(n.value),
                "subtitle": n.subtitle,
                "fill": n.fill or "",
                "font_size": _to_float(n.font_size),
            }
            for n in self.nodes
        ]
        edge_rows = [
            {
                "source": e.source,
                "target": e.target,
                "label": e.label,
                "probability": _to_float(e.probability),
                "style": e.style,
                "color": e.color or "",
            }
            for e in self.edges
        ]
        nodes_df = pd.DataFrame(node_rows, columns=NODE_COLUMNS)
        edges_df = pd.DataFrame(edge_rows, columns=EDGE_COLUMNS)
        return _coerce_node_dtypes(nodes_df), _coerce_edge_dtypes(edges_df)

    @classmethod
    def from_frames(
        cls,
        diagram_type: str,
        title: str,
        theme_name: str,
        rankdir: str,
        nodes_df: pd.DataFrame,
        edges_df: pd.DataFrame,
    ) -> "DiagramSpec":
        nodes: List[Node] = []
        for _, row in nodes_df.iterrows():
            node_id = _clean_str(row.get("id"))
            if not node_id:
                continue  # skip blank rows the user hasn't filled in yet
            nodes.append(
                Node(
                    id=node_id,
                    label=_clean_str(row.get("label")),
                    role=_clean_str(row.get("role")) or "process",
                    value=_clean_float(row.get("value")),
                    subtitle=_clean_str(row.get("subtitle")),
                    fill=_clean_str(row.get("fill")) or None,
                    font_size=_clean_float(row.get("font_size")),
                )
            )

        edges: List[Edge] = []
        for _, row in edges_df.iterrows():
            source = _clean_str(row.get("source"))
            target = _clean_str(row.get("target"))
            if not source or not target:
                continue
            edges.append(
                Edge(
                    source=source,
                    target=target,
                    label=_clean_str(row.get("label")),
                    probability=_clean_float(row.get("probability")),
                    style=_clean_str(row.get("style")) or "solid",
                    color=_clean_str(row.get("color")) or None,
                )
            )

        return cls(
            diagram_type=diagram_type,
            title=title,
            theme_name=theme_name,
            rankdir=rankdir,
            nodes=nodes,
            edges=edges,
        )


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def _filter_keys(d: dict, dataclass_type) -> dict:
    """Keep only keys that are valid fields of the dataclass (forward-compatible loads)."""
    valid = dataclass_type.__dataclass_fields__.keys()
    return {k: v for k, v in d.items() if k in valid}


def _to_float(value) -> float:
    """None -> NaN so numeric DataFrame columns stay float and render as blank cells."""
    if value is None:
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _clean_str(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _clean_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().replace(",", "").replace("$", "").replace("%", "")
        if value == "":
            return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_node_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("id", "label", "role", "subtitle", "fill"):
        df[col] = df[col].astype("object")
    for col in ("value", "font_size"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _coerce_edge_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("source", "target", "label", "style", "color"):
        df[col] = df[col].astype("object")
    df["probability"] = pd.to_numeric(df["probability"], errors="coerce")
    return df


def empty_frames():
    """Return a pair of empty (nodes_df, edges_df) with correct columns/dtypes."""
    nodes_df = _coerce_node_dtypes(pd.DataFrame(columns=NODE_COLUMNS))
    edges_df = _coerce_edge_dtypes(pd.DataFrame(columns=EDGE_COLUMNS))
    return nodes_df, edges_df
