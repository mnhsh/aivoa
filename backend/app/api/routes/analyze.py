from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import workflow_traces
from app.db.session import get_db
from app.parsers.document_parser import parse_document_bytes
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.analysis_service import AnalysisService
from app.services.document_service import DocumentService

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("", response_model=AnalyzeResponse)
async def analyze_json(payload: AnalyzeRequest, db: AsyncSession = Depends(get_db)) -> AnalyzeResponse:
    return await AnalysisService(db, workflow_traces).analyze(text=payload.text, document_id=payload.document_id)


@router.post("/upload", response_model=AnalyzeResponse)
async def analyze_multipart(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> AnalyzeResponse:
    content = await file.read()
    doc = await DocumentService(db).upload(payload=content, filename=file.filename or "uploaded.bin", mime_type=file.content_type or "")
    parsed = parse_document_bytes(content, file.filename or "uploaded.bin")
    return await AnalysisService(db, workflow_traces).analyze(text=parsed, document_id=doc.id)


@router.post("/stream")
async def analyze_stream(text: str = Form(...), db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    async def event_generator() -> asyncio.AsyncGenerator[str, None]:
        steps = [
            "Document parsed",
            "Deviation details extracted",
            "Searching quality knowledge base",
            "Assessing impact",
            "Finding similar deviations",
        ]
        for idx, step in enumerate(steps, start=1):
            yield f"event: step\ndata: {json.dumps({'index': idx, 'label': step})}\n\n"
            await asyncio.sleep(0.02)
        result = await AnalysisService(db, workflow_traces).analyze(text=text, document_id=None)
        yield f"event: result\ndata: {result.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
