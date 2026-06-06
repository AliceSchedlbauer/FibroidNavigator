"""
FastAPI endpoint for the Fibroid Concierge Risk Calculator.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fibroid_concierge import FibroidConcierge, PatientInput, RiskResult

app = FastAPI(
    title="Fibroid Navigator API",
    description="AI Risk Calculator for uterine fibroids (AUC ~0.95)",
    version="1.0.0",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
