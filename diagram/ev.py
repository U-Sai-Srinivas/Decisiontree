"""Expected-Value engine for decision trees.

Rules
-----
* Terminal node  -> EV = its ``value`` (payoff / cost).
* Chance node    -> EV = sum(child_EV * branch_probability) over outgoing edges.
* Decision node  -> EV = max(child_EV) over outgoing edges; the winning branch is
                    recorded so the renderer can highlight the optimal path.

The function is defensive: it never raises on malformed trees (cycles, missing
probabilities, dangling edges). Instead it returns a list of human-readable
warnings the UI can surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from .model import DiagramSpec

PROB_TOLERANCE = 0.01  # how far a chance node's probabilities may sum from 1.0


@dataclass
class EVResult:
    values: Dict[str, float]                 # node_id -> expected value
    optimal_edges: Set[Tuple[str, str]]      # (source, target) edges on an optimal choice
    optimal_choice: Dict[str, str]           # decision node_id -> chosen edge label
    roots: List[str]                         # node ids with no incoming edge
    warnings: List[str]


def compute_ev(spec: DiagramSpec) -> EVResult:
    if spec.diagram_type != "decision_tree":
        return EVResult({}, set(), {}, [], [])

    nodes = {n.id: n for n in spec.nodes}
    # Adjacency: node_id -> list of outgoing edges
    out_edges: Dict[str, list] = {nid: [] for nid in nodes}
    indegree: Dict[str, int] = {nid: 0 for nid in nodes}
    warnings: List[str] = []

    for e in spec.edges:
        if e.source not in nodes or e.target not in nodes:
            warnings.append(f"Edge {e.source!r} → {e.target!r} references a missing node.")
            continue
        out_edges[e.source].append(e)
        indegree[e.target] += 1

    values: Dict[str, float] = {}
    optimal_edges: Set[Tuple[str, str]] = set()
    optimal_choice: Dict[str, str] = {}
    visiting: Set[str] = set()

    def ev(node_id: str) -> float:
        if node_id in values:
            return values[node_id]
        if node_id in visiting:
            warnings.append(f"Cycle detected at node {node_id!r}; treated as 0.")
            return 0.0

        visiting.add(node_id)
        node = nodes[node_id]
        children = out_edges.get(node_id, [])

        if node.role == "terminal" or not children:
            if node.role != "terminal" and children:
                # Non-terminal but no children handled above; here: leaf that isn't terminal
                pass
            result = float(node.value) if node.value is not None else 0.0
            if node.role != "terminal" and not children and node.value is None:
                warnings.append(
                    f"Node {node_id!r} ({node.role}) has no children and no value; treated as 0."
                )

        elif node.role == "chance":
            total_p = 0.0
            result = 0.0
            for e in children:
                p = e.probability if e.probability is not None else 0.0
                total_p += p
                result += p * ev(e.target)
            if abs(total_p - 1.0) > PROB_TOLERANCE:
                warnings.append(
                    f"Chance node {node_id!r}: branch probabilities sum to {total_p:.2f} "
                    f"(should be 1.00)."
                )

        elif node.role == "decision":
            best_val: Optional[float] = None
            best_edge = None
            for e in children:
                child_val = ev(e.target)
                if best_val is None or child_val > best_val:
                    best_val = child_val
                    best_edge = e
            result = best_val if best_val is not None else 0.0
            if best_edge is not None:
                optimal_edges.add((best_edge.source, best_edge.target))
                optimal_choice[node_id] = best_edge.label or nodes[best_edge.target].label

        else:  # unknown role in a decision tree — treat as pass-through/leaf
            result = float(node.value) if node.value is not None else 0.0

        visiting.discard(node_id)
        values[node_id] = result
        return result

    for nid in nodes:
        ev(nid)

    roots = [nid for nid, deg in indegree.items() if deg == 0]
    return EVResult(values, optimal_edges, optimal_choice, roots, warnings)


def format_currency(value: Optional[float]) -> str:
    """Format a number as a clean currency string, e.g. 12500 -> '$12,500', -300 -> '-$300'."""
    if value is None:
        return ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return ""
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.0f}"
