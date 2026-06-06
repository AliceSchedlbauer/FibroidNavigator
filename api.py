"""
FastAPI endpoint for WombWise - combined prevention + risk platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from demo_data import get_demo_payload, get_shield_demo_payload
from fibroid_concierge import FibroidConcierge, PatientInput, RiskResult
from fibroid_shield import ShieldInput, analyze_dict
from fibroid_x_predict_voicing import (
    SUPPORTED_CITIES,
    SUPPORTED_REGIONS,
    end_to_end_flow,
    voicing_for_appointments,
)
from wombwise_assessment import (
    DEMO_ASSESSMENT_INPUT,
    AssessmentInput,
    analyze_assessment_dict,
)

app = FastAPI(
    title="WombWise API",
    description="Cycle-based fibroid prevention, AI risk scoring, and specialist matching",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

concierge = FibroidConcierge()


class HealthResponse(BaseModel):
    status: str
    model_auc: float
    model_loaded: bool


class RiskResponse(BaseModel):
    risk_score: float
    risk_percent: float
    risk_category: str
    priority: str
    recommendation: str
    model_auc: float
    features_used: list[str]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_auc=concierge.metadata.get("auc", 0.0),
        model_loaded=concierge.model is not None,
    )


@app.post("/api/v1/risk", response_model=RiskResponse)
def calculate_risk(patient: PatientInput) -> RiskResult:
    try:
        return concierge.predict(patient)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/v1/demo")
def get_demo() -> dict:
    """Return showcase demo patient (Black woman, 32) with bleeding chart."""
    try:
        return get_demo_payload(concierge.metadata.get("auc", 0.0))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class FlowRequest(BaseModel):
    patient: PatientInput
    region: str = "Germany"
    city: str | None = "Berlin"


@app.get("/api/v1/regions")
def list_regions() -> dict:
    return {"regions": SUPPORTED_REGIONS, "cities": SUPPORTED_CITIES}


@app.post("/api/v1/flow")
def run_end_to_end_flow(request: FlowRequest) -> dict:
    """Full pipeline: risk prediction + specialist appointment matching."""
    try:
        return end_to_end_flow(request.patient, request.region, request.city, concierge)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/v1/appointments/{region}/{risk_level}")
def get_appointments(region: str, risk_level: str, city: str | None = None) -> dict:
    """Specialist matching by region and risk level (HIGH/MEDIUM/LOW)."""
    try:
        return voicing_for_appointments(region, risk_level.upper(), city)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analyze")
def analyze_daily_checkin(checkin: ShieldInput) -> dict:
    """WombWise daily check-in: cycle + stress + food -> micro-actions."""
    try:
        return analyze_dict(checkin)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/v1/shield/demo")
def get_shield_demo() -> dict:
    """Demo daily check-in: luteal phase + stress + red meat."""
    try:
        return get_shield_demo_payload()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/v1/assessment")
def run_interactive_assessment(payload: AssessmentInput) -> dict:
    """Interactive assessment: symptoms + profile + lifestyle + blood markers."""
    try:
        return analyze_assessment_dict(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/v1/assessment/demo")
def get_assessment_demo() -> dict:
    """Return a complete high-risk assessment demo payload."""
    try:
        return {
            "label": "Demo: full WombWise assessment",
            "input": DEMO_ASSESSMENT_INPUT.model_dump(),
            "result": analyze_assessment_dict(DEMO_ASSESSMENT_INPUT),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
