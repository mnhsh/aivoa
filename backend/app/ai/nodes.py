from __future__ import annotations

from app.ai.state import AnalysisState


def trace_step(state: AnalysisState, name: str, detail: str) -> None:
    state.trace.append({"step": name, "detail": detail})


def node_parse(state: AnalysisState) -> AnalysisState:
    trace_step(state, "parse", "Document parsed")
    return state


def node_extract(state: AnalysisState, fields: list[dict]) -> AnalysisState:
    state.fields = fields
    trace_step(state, "extract", "Deviation details extracted")
    return state


def node_evidence(state: AnalysisState, evidence: list[dict]) -> AnalysisState:
    state.evidence = evidence
    trace_step(state, "evidence", "RAG evidence retrieved")
    return state


def node_assess(state: AnalysisState, recommendation: str, conflict_detected: bool) -> AnalysisState:
    state.recommendation = recommendation
    state.conflict_detected = conflict_detected
    trace_step(state, "assess", "Impact assessment generated")
    return state


def node_similar(state: AnalysisState, similar_cases: list[dict]) -> AnalysisState:
    state.similar_cases = similar_cases
    trace_step(state, "similar", "Similar deviations retrieved")
    return state
