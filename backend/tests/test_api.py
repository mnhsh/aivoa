from fastapi.testclient import TestClient

from app.main import app

DEMO_TEXT = (
    "During API-ACM-01 batch B240918 processing, reactor temperature increased to 86.5°C and remained above "
    "the approved upper limit of 82°C for approximately 18 minutes. The excursion was identified through "
    "in-process monitoring."
)


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert "demo_mode" in payload


def test_document_upload_idempotent():
    with TestClient(app) as client:
        files = {"file": ("deviation.txt", DEMO_TEXT.encode("utf-8"), "text/plain")}
        first = client.post("/api/v1/documents/upload", files=files)
        assert first.status_code == 200
        second = client.post("/api/v1/documents/upload", files=files)
        assert second.status_code == 200
        assert second.json()["idempotent_reuse"] is True


def test_analyze_and_trace():
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"text": DEMO_TEXT})
        assert response.status_code == 200
        payload = response.json()
        assert payload["demo_mode"] is True
        assert payload["provider"] == "demo"
        assert payload["recommendation"] == "High"
        assert payload["extracted_fields"][0]["value"] == "B240918"

        trace = client.get(f"/api/v1/workflow/trace/{payload['trace_id']}")
        assert trace.status_code == 200
        assert len(trace.json()["steps"]) >= 4
