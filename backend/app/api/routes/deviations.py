from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import Message
from app.schemas.deviations import (
    DeviationCreate,
    ChatRequest,
    ChatResponse,
    DeviationOut,
    DeviationUpdate,
    ReassessRequest,
    ReassessResponse,
)
from app.services.deviation_service import DeviationService

router = APIRouter(prefix="/deviations", tags=["deviations"])


@router.get("", response_model=list[DeviationOut])
async def list_deviations(db: AsyncSession = Depends(get_db)) -> list[DeviationOut]:
    return await DeviationService(db).list()


@router.post("", response_model=DeviationOut, status_code=status.HTTP_201_CREATED)
async def create_deviation(payload: DeviationCreate, db: AsyncSession = Depends(get_db)) -> DeviationOut:
    return await DeviationService(db).create(payload)


@router.get("/{deviation_id}", response_model=DeviationOut)
async def get_deviation(deviation_id: str, db: AsyncSession = Depends(get_db)) -> DeviationOut:
    return await DeviationService(db).get(deviation_id)


@router.patch("/{deviation_id}", response_model=DeviationOut)
async def update_deviation(deviation_id: str, payload: DeviationUpdate, db: AsyncSession = Depends(get_db)) -> DeviationOut:
    item, ok = await DeviationService(db).update(deviation_id, payload)
    if not ok:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Version conflict detected")
    return item


@router.delete("/{deviation_id}", response_model=Message)
async def delete_deviation(deviation_id: str, db: AsyncSession = Depends(get_db)) -> Message:
    await DeviationService(db).delete(deviation_id)
    return Message(message="Deleted")


@router.get("/{deviation_id}/similar")
async def similar_cases(deviation_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    return await DeviationService(db).similar_cases(deviation_id)


@router.get("/{deviation_id}/evidence")
async def deviation_evidence(deviation_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    return await DeviationService(db).evidence(deviation_id)


@router.get("/{deviation_id}/fields")
async def deviation_fields(deviation_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    return await DeviationService(db).fields(deviation_id)


@router.post("/{deviation_id}/reassess", response_model=ReassessResponse)
async def reassess(deviation_id: str, payload: ReassessRequest, db: AsyncSession = Depends(get_db)) -> ReassessResponse:
    return await DeviationService(db).reassess(deviation_id, payload.rationale)

@router.post("/{deviation_id}/chat", response_model=ChatResponse)
async def chat_deviation(deviation_id: str, payload: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    return await DeviationService(db).process_chat(deviation_id, payload.message)
