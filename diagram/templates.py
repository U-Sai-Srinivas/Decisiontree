"""Ready-to-load example diagrams.

Each builder returns a fully populated :class:`DiagramSpec` with realistic values so
a first-time user can load one and immediately see how the tool works. Decision-tree
templates are designed to have a clear (but not trivial) optimal path.
"""

from __future__ import annotations

from typing import Callable, Dict

from .model import DiagramSpec, Edge, Node


# --------------------------------------------------------------------------------------
# Decision trees
# --------------------------------------------------------------------------------------


def make_vs_buy() -> DiagramSpec:
    return DiagramSpec(
        diagram_type="decision_tree",
        title="Make vs. Buy",
        rankdir="LR",
        nodes=[
            Node("D1", "Make vs. Buy", "decision"),
            Node("C1", "Build In-House", "chance"),
            Node("C2", "Buy from Vendor", "chance"),
            Node("T1", "On-time launch", "terminal", value=500000),
            Node("T2", "Delay & overrun", "terminal", value=50000),
            Node("T3", "Meets needs", "terminal", value=300000),
            Node("T4", "Integration issues", "terminal", value=120000),
        ],
        edges=[
            Edge("D1", "C1", "Build In-House"),
            Edge("D1", "C2", "Buy from Vendor"),
            Edge("C1", "T1", "Success", probability=0.60),
            Edge("C1", "T2", "Delay", probability=0.40),
            Edge("C2", "T3", "Meets needs", probability=0.80),
            Edge("C2", "T4", "Issues", probability=0.20),
        ],
    )


def product_launch() -> DiagramSpec:
    return DiagramSpec(
        diagram_type="decision_tree",
        title="Product Launch Strategy",
        rankdir="LR",
        nodes=[
            Node("D1", "Marketing Strategy", "decision"),
            Node("C1", "Aggressive Spend", "chance"),
            Node("C2", "Conservative Spend", "chance"),
            Node("T1", "Market embraces", "terminal", value=1200000),
            Node("T2", "Weak uptake", "terminal", value=200000),
            Node("T3", "Steady growth", "terminal", value=600000),
            Node("T4", "Flat sales", "terminal", value=250000),
        ],
        edges=[
            Edge("D1", "C1", "Aggressive"),
            Edge("D1", "C2", "Conservative"),
            Edge("C1", "T1", "Embraced", probability=0.55),
            Edge("C1", "T2", "Weak", probability=0.45),
            Edge("C2", "T3", "Growth", probability=0.70),
            Edge("C2", "T4", "Flat", probability=0.30),
        ],
    )


def litigation_settlement() -> DiagramSpec:
    return DiagramSpec(
        diagram_type="decision_tree",
        title="Litigation Settlement",
        rankdir="LR",
        nodes=[
            Node("D1", "Settle or Trial?", "decision"),
            Node("S1", "Accept Settlement", "terminal", value=250000),
            Node("C1", "Go to Trial", "chance"),
            Node("T1", "Win case", "terminal", value=600000),
            Node("T2", "Lose case", "terminal", value=-50000, subtitle="legal costs"),
        ],
        edges=[
            Edge("D1", "S1", "Settle"),
            Edge("D1", "C1", "Go to Trial"),
            Edge("C1", "T1", "Win", probability=0.50),
            Edge("C1", "T2", "Lose", probability=0.50),
        ],
    )


# --------------------------------------------------------------------------------------
# Flowcharts
# --------------------------------------------------------------------------------------


def approval_process() -> DiagramSpec:
    return DiagramSpec(
        diagram_type="flowchart",
        title="Sample Approval Process",
        rankdir="TB",
        nodes=[
            Node("S", "Sample received", "start_end"),
            Node("P1", "Log in LIMS", "process"),
            Node("P2", "Run QC checks", "process"),
            Node("D1", "Passes QC?", "decision"),
            Node("P3", "Approve & store", "process"),
            Node("P4", "Flag for re-prep", "process"),
            Node("DOC", "QC report", "document"),
            Node("E", "Ready for assay", "start_end"),
        ],
        edges=[
            Edge("S", "P1"),
            Edge("P1", "P2"),
            Edge("P2", "D1"),
            Edge("D1", "P3", "Yes"),
            Edge("D1", "P4", "No", style="dashed"),
            Edge("P4", "P2", "re-run"),
            Edge("P3", "DOC"),
            Edge("DOC", "E"),
        ],
    )


# --------------------------------------------------------------------------------------
# Org chart / mind map
# --------------------------------------------------------------------------------------


def org_chart() -> DiagramSpec:
    return DiagramSpec(
        diagram_type="org_mindmap",
        title="Company Org Chart",
        rankdir="TB",
        nodes=[
            Node("CEO", "CEO", "box"),
            Node("CSO", "Chief Scientific Officer", "box"),
            Node("CFO", "Chief Financial Officer", "box"),
            Node("COO", "Chief Operating Officer", "box"),
            Node("GEN", "Genomics Lead", "box"),
            Node("CB", "Comp Bio Lead", "box"),
            Node("FIN", "Finance Manager", "box"),
        ],
        edges=[
            Edge("CEO", "CSO"),
            Edge("CEO", "CFO"),
            Edge("CEO", "COO"),
            Edge("CSO", "GEN"),
            Edge("CSO", "CB"),
            Edge("CFO", "FIN"),
        ],
    )


def project_mindmap() -> DiagramSpec:
    return DiagramSpec(
        diagram_type="org_mindmap",
        title="Project Kickoff",
        rankdir="LR",
        nodes=[
            Node("M", "Project Kickoff", "mind"),
            Node("SC", "Scope", "mind"),
            Node("TM", "Team", "mind"),
            Node("TL", "Timeline", "mind"),
            Node("RK", "Risks", "mind"),
            Node("DL", "Deliverables", "mind"),
            Node("SC1", "Define MVP", "mind"),
            Node("TM1", "Assign owners", "mind"),
            Node("TL1", "8 weeks", "mind"),
            Node("RK1", "Data gaps", "mind"),
            Node("DL1", "Demo + report", "mind"),
        ],
        edges=[
            Edge("M", "SC"),
            Edge("M", "TM"),
            Edge("M", "TL"),
            Edge("M", "RK"),
            Edge("M", "DL"),
            Edge("SC", "SC1"),
            Edge("TM", "TM1"),
            Edge("TL", "TL1"),
            Edge("RK", "RK1"),
            Edge("DL", "DL1"),
        ],
    )


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------

TEMPLATES: Dict[str, Dict[str, Callable[[], DiagramSpec]]] = {
    "decision_tree": {
        "Make vs. Buy": make_vs_buy,
        "Product Launch Strategy": product_launch,
        "Litigation Settlement": litigation_settlement,
    },
    "flowchart": {
        "Sample Approval Process": approval_process,
    },
    "org_mindmap": {
        "Company Org Chart": org_chart,
        "Project Kickoff (mind map)": project_mindmap,
    },
}


def template_names(diagram_type: str):
    return list(TEMPLATES.get(diagram_type, {}).keys())


def build_template(diagram_type: str, name: str) -> DiagramSpec:
    return TEMPLATES[diagram_type][name]()


def default_spec() -> DiagramSpec:
    """The diagram shown on first load."""
    return make_vs_buy()
