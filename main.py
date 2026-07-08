from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging

BASE_DIR = Path(__file__).resolve().parent

from db import (
    ensure_ml_schema,
    get_dashboard_stats, get_all_customers, get_customer_detail,
    get_unactioned_alerts, mark_alert_actioned, get_risk_distribution,
    get_country_risk,
    create_customer, update_customer, delete_customer, customer_exists,
)
from ml_pipeline import run_pipeline

log = logging.getLogger(__name__)

app = FastAPI(
    title="Bank Churn Intelligence API",
    description="ML-powered churn detection pipeline for banking customers",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup_ensure_db_objects():
    try:
        ensure_ml_schema()
        log.info("Churn_Alerts + vw_model_features verified/created.")
    except Exception as e:
        log.warning("ensure_ml_schema failed (run db_setup.sql in MySQL if APIs error): %s", e)


@app.get("/")
def serve_dashboard():
    """ChurnIQ UI (open http://127.0.0.1:8000/ — /docs is only the raw API tester)."""
    path = BASE_DIR / "dashboard.html"
    if not path.is_file():
        raise HTTPException(404, "dashboard.html not found next to main.py")
    return FileResponse(path, media_type="text/html")


# ─── Request / Response Models ─────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name:         str           = Field(..., min_length=1, max_length=100)
    age:          int           = Field(..., ge=18, le=100)
    gender:       str           = Field(..., pattern="^(male|female|other)$")
    country:      str           = Field(..., min_length=2, max_length=50)
    salary:       float         = Field(..., ge=0)
    tenure:       int           = Field(..., ge=0, le=50)
    products_number: int        = Field(..., ge=1, le=10)
    credit_score: int           = Field(..., ge=300, le=900)
    created_at:   Optional[str] = None   # YYYY-MM-DD


class CustomerUpdate(BaseModel):
    """All fields optional — only supplied fields are written."""
    name:            Optional[str]   = Field(None, min_length=1, max_length=100)
    age:             Optional[int]   = Field(None, ge=18, le=100)
    gender:          Optional[str]   = Field(None, pattern="^(male|female|other)$")
    country:         Optional[str]   = Field(None, min_length=2, max_length=50)
    salary:          Optional[float] = Field(None, ge=0)
    tenure:          Optional[int]   = Field(None, ge=0, le=50)
    products_number: Optional[int]   = Field(None, ge=1, le=10)
    credit_score:    Optional[int]   = Field(None, ge=300, le=900)


class PipelineRequest(BaseModel):
    customer_ids: Optional[list[int]] = None


class ActionAlertRequest(BaseModel):
    customer_id: int


# ─── Dashboard ─────────────────────────────────────────────────────────────────


@app.get("/api/stats")
def dashboard_stats():
    try:
        return get_dashboard_stats()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/risk-distribution")
def risk_distribution():
    try:
        return get_risk_distribution()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/country-risk")
def country_risk():
    try:
        return get_country_risk()
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Customers — LIST + GET ────────────────────────────────────────────────────

@app.get("/api/customers")
def list_customers(
    limit:     int           = Query(500, ge=1, le=5000),
    offset:    int           = Query(0, ge=0),
    risk_band: Optional[str] = Query(None, pattern="^(High|Medium|Low)$")
):
    try:
        data = get_all_customers(limit=limit, offset=offset, risk_band=risk_band)
        return {"customers": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: int):
    try:
        data = get_customer_detail(customer_id)
        if not data:
            raise HTTPException(404, f"Customer {customer_id} not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Customers — CREATE ────────────────────────────────────────────────────────

@app.post("/api/customers", status_code=201)
def add_customer(body: CustomerCreate):
    """
    Insert a new customer. Also seeds Behavior_Summary so the ML view
    includes them immediately. Then call /api/pipeline/run with the new ID to score.
    """
    try:
        payload = body.model_dump()
        payload["prd_number"] = payload.pop("products_number")
        new_id = create_customer(payload)
        return {
            "status":      "created",
            "customer_id": new_id,
            "message":     f"Run POST /api/pipeline/run with customer_ids=[{new_id}] to score."
        }
    except Exception as e:
        log.exception("Create customer failed")
        raise HTTPException(500, str(e))


# ─── Customers — UPDATE ────────────────────────────────────────────────────────

@app.put("/api/customers/{customer_id}")
def edit_customer(customer_id: int, body: CustomerUpdate):
    """
    Partial update — only supplied fields are changed.
    Automatically triggers a pipeline re-score after update.
    """
    if not customer_exists(customer_id):
        raise HTTPException(404, f"Customer {customer_id} not found")
    try:
        payload = body.model_dump(exclude_none=True)
        if "products_number" in payload:
            payload["prd_number"] = payload.pop("products_number")
        changed = update_customer(customer_id, payload)
        if not changed:
            raise HTTPException(400, "No valid fields provided or nothing changed")

        try:
            run_pipeline(customer_ids=[customer_id])
            rescored = True
        except Exception:
            rescored = False

        return {"status": "updated", "customer_id": customer_id, "rescored": rescored}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Update customer failed")
        raise HTTPException(500, str(e))


# ─── Customers — DELETE ────────────────────────────────────────────────────────

@app.delete("/api/customers/{customer_id}")
def remove_customer(customer_id: int):
    """
    Hard-deletes the customer and all dependent rows in correct FK order:
    alerts → predictions → behavior → logins → tickets → loan payments →
    loans → cards → transactions → account holders → orphaned accounts → customer.
    """
    if not customer_exists(customer_id):
        raise HTTPException(404, f"Customer {customer_id} not found")
    try:
        ok = delete_customer(customer_id)
        if not ok:
            raise HTTPException(500, "Delete failed unexpectedly")
        return {"status": "deleted", "customer_id": customer_id}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Delete customer failed")
        raise HTTPException(500, str(e))


# ─── Alerts ────────────────────────────────────────────────────────────────────

@app.get("/api/alerts")
def alerts(limit: int = Query(20, ge=1, le=100)):
    try:
        return {"alerts": get_unactioned_alerts(limit=limit)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/alerts/action")
def action_alert(req: ActionAlertRequest):
    try:
        mark_alert_actioned(req.customer_id)
        return {"status": "ok", "customer_id": req.customer_id}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Pipeline ──────────────────────────────────────────────────────────────────

@app.post("/api/pipeline/run")
def run_pipeline_endpoint(req: PipelineRequest):
    try:
        result = run_pipeline(customer_ids=req.customer_ids)
        return {"status": "completed", **result}
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        log.exception("Pipeline error")
        raise HTTPException(500, str(e))


@app.post("/api/pipeline/run-async")
def run_pipeline_async(req: PipelineRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_pipeline, customer_ids=req.customer_ids)
    mode = f"targeted ({len(req.customer_ids)} customers)" if req.customer_ids else "full batch"
    return {"status": "queued", "mode": mode}


# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
