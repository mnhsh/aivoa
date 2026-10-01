import asyncio
from app.db.session import initialize_database, get_db
from app.services.analysis_service import AnalysisService
from app.services.workflow_service import WorkflowTraceService

async def main():
    await initialize_database()

    async for db in get_db():
        service = AnalysisService(db, WorkflowTraceService(db))
        text = "During API-ACM-01 batch B240918 processing, reactor temperature increased to 86.5°C and remained above the approved upper limit of 82°C for approximately 18 minutes."
        resp = await service.analyze(text=text, document_id=None)
        print(resp.model_dump_json(indent=2))
        break

asyncio.run(main())
