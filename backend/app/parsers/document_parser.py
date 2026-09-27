from __future__ import annotations


def parse_document_bytes(payload: bytes, filename: str) -> str:
    if not payload:
        return ""
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return f"Binary document {filename} uploaded. Text extraction unavailable in demo parser."
