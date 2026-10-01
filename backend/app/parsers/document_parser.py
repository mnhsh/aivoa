from __future__ import annotations
import io
import pypdf

def parse_document_bytes(payload: bytes, filename: str) -> str:
    if not payload:
        return ""

    # Simple check for PDF based on filename or signature
    if filename.lower().endswith('.pdf') or payload.startswith(b'%PDF'):
        try:
            reader = pypdf.PdfReader(io.BytesIO(payload))
            text = []
            for page in reader.pages:
                text.append(page.extract_text() or "")
            extracted = "\n".join(text).strip()
            if extracted:
                return extracted
        except Exception as e:
            return f"Error parsing PDF: {e}"

    # Fallback to UTF-8 decoding for text files
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return f"Binary document {filename} uploaded. Text extraction unavailable."
