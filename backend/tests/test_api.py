from fastapi.testclient import TestClient

from app.main import app
from app.integrations.groq_client import ChatUpdateResponse, ExtractionResponse, GroqClient

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


def test_range_before_actual_is_high():
    text = (
        "Material MET-3390. Approved temperature range: 2°C to 8°C. "
        "The actual temperature reached 12°C for 18 minutes."
    )
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"text": text})

    assert response.status_code == 200
    assert response.json()["recommendation"] == "High"


def test_low_side_excursion_is_high():
    text = (
        "Material MET-3390. Approved temperature range: 2°C to 8°C. "
        "The actual temperature reached -2°C for 18 minutes."
    )
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"text": text})

    assert response.status_code == 200
    assert response.json()["recommendation"] == "High"


def test_chat_updates_record_and_reassesses(monkeypatch):
    async def ai_chat_update(self, text, current_state):
        return ChatUpdateResponse(batch="MET-3390", actual_value=86.5, approved_max=82, duration_minutes=18)

    monkeypatch.setattr(GroqClient, "process_chat", ai_chat_update)

    with TestClient(app) as client:
        analyzed = client.post(
            "/api/v1/analyze",
            json={
                "text": "Batch OLD-1 reactor temperature reached 83°C above the approved upper limit of 82°C for 5 minutes."
            },
        )
        deviation_id = analyzed.json()["deviation_id"]
        response = client.post(
            f"/api/v1/deviations/{deviation_id}/chat",
            json={"message": "Change the batch to MET-3390 and correct the process values."},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["deviation"]["batch"] == "MET-3390"
    assert payload["deviation"]["severity"] == "High"
    assert set(payload["updated_fields"]) >= {"batch", "actual_value", "duration_minutes", "severity"}
    assert payload["deviation"]["approved_max"] == 82


def test_versioned_save_persists_reviewed_severity():
    with TestClient(app) as client:
        analyzed = client.post("/api/v1/analyze", json={"text": DEMO_TEXT}).json()
        deviation = client.get(f"/api/v1/deviations/{analyzed['deviation_id']}").json()
        response = client.patch(
            f"/api/v1/deviations/{deviation['id']}",
            json={
                "title": deviation["title"],
                "severity": "High",
                "status": "Under Review",
                "expected_version": deviation["version"],
            },
        )

    assert response.status_code == 200
    assert response.json()["severity"] == "High"


def test_direct_create_cannot_downgrade_mandatory_high():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/deviations",
            json={
                "title": "Temperature excursion in reactor",
                "product": "Metformin",
                "batch": "MET-3390",
                "severity": "Low",
                "parameter": "Reactor Temperature",
                "approved_max": 82,
                "actual_value": 86.5,
                "duration_minutes": 18,
            },
        )

    assert response.status_code == 201
    assert response.json()["severity"] == "High"


def test_upload_classifies_descriptive_impact_before_persisting():
    report = """Vasudha Pharma Chem Limited — Deviation Report
Site: Unit-II API Manufacturing Plant
Date: 2026-09-23
Source: Lab/Production Report
Product: Metformin Hydrochloride API
Batch: MET-3390
Impact: Potential impact on crystal size distribution and dissolution performance due to faster cooling rate.
During crystallization, the approved cooling rate range is 0.5-1.0 °C/min. The recorded rate was 2.3 °C/min for approximately 40 minutes.
"""

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyze/upload",
            files={"file": ("met-3390.txt", report.encode("utf-8"), "text/plain")},
        )
        assert response.status_code == 200
        deviation = client.get(f"/api/v1/deviations/{response.json()['deviation_id']}")

    assert deviation.status_code == 200
    payload = deviation.json()
    assert payload["batch"] == "MET-3390"
    assert payload["source"] == "Internal Deviation"
    assert payload["initial_impact"] == "Potential Quality Impact"


def test_paste_accepts_nullable_optional_ai_fields(monkeypatch):
    async def ai_extraction(self, text):
        return ExtractionResponse(
            site=None,
            title="Cooling rate excursion",
            description="Cooling exceeded the approved process rate.",
            product="Metformin Hydrochloride API",
            batch="MET-3390",
            parameter=None,
            approved_min=0.5,
            approved_max=1.0,
            actual_value=2.3,
            duration_minutes=40,
        )

    monkeypatch.setattr(GroqClient, "extract_deviation_data", ai_extraction)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Batch MET-3390 had a cooling rate excursion for 40 minutes."},
        )
        assert response.status_code == 200
        deviation = client.get(f"/api/v1/deviations/{response.json()['deviation_id']}")

    assert deviation.status_code == 200
    payload = deviation.json()
    assert payload["site"] == ""
    assert payload["parameter"] == ""
    assert payload["batch"] == "MET-3390"


def test_paste_rejects_technical_logs_without_creating_deviation():
    technical_log = """INFO: POST /api/v1/analyze 500 Internal Server Error
ERROR: Exception in ASGI application
Traceback (most recent call last):
  File /app/services/analysis_service.py, line 97
pydantic_core._pydantic_core.ValidationError: site must be a string
Copied form value: Batch MET-3390, severity High
"""

    with TestClient(app) as client:
        before = len(client.get("/api/v1/deviations").json())
        response = client.post("/api/v1/analyze", json={"text": technical_log})
        after = len(client.get("/api/v1/deviations").json())

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "not_quality_deviation"
    assert "stack trace" in response.json()["detail"]["message"]
    assert after == before
