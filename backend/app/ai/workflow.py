from __future__ import annotations

from app.ai.nodes import node_assess, node_evidence, node_extract, node_parse, node_similar
from app.ai.state import AnalysisState

try:
    from langgraph.graph import END, START, StateGraph  # type: ignore

    HAS_LANGGRAPH = True
except Exception:
    HAS_LANGGRAPH = False


class AnalysisWorkflow:
    def run(
        self,
        *,
        text: str,
        fields: list[dict],
        evidence: list[dict],
        recommendation: str,
        conflict_detected: bool,
        similar_cases: list[dict],
    ) -> AnalysisState:
        state = AnalysisState(text=text)
        if HAS_LANGGRAPH:
            graph = StateGraph(AnalysisState)
            graph.add_node("parse", lambda s: node_parse(s))
            graph.add_node("extract", lambda s: node_extract(s, fields))
            graph.add_node("evidence", lambda s: node_evidence(s, evidence))
            graph.add_node("assess", lambda s: node_assess(s, recommendation, conflict_detected))
            graph.add_node("similar", lambda s: node_similar(s, similar_cases))
            graph.add_edge(START, "parse")
            graph.add_edge("parse", "extract")
            graph.add_edge("extract", "evidence")
            graph.add_edge("evidence", "assess")
            graph.add_edge("assess", "similar")
            graph.add_edge("similar", END)
            compiled = graph.compile()
            return compiled.invoke(state)
        state = node_parse(state)
        state = node_extract(state, fields)
        state = node_evidence(state, evidence)
        state = node_assess(state, recommendation, conflict_detected)
        state = node_similar(state, similar_cases)
        return state
