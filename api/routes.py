"""API routes for Swift Event Intelligence Platform.

All event storage goes through db.repository.event_repo so the API
and the background pipeline share the same data.
"""

import uuid
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas import (
    SignalCreate, BatchSignalCreate,
    EventResponse, EventListResponse,
    UserCreate, UserLogin, TokenResponse,
    PipelineStatsResponse,
)
from api.auth import (
    get_current_user, require_role, register_user,
    authenticate_user, create_access_token,
)
from api.openclaw_auth import verify_openclaw_api_key
from pipeline.processor import process_signal, get_deduplicator
from db.repository import event_repo
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()
router = APIRouter(prefix="/api/v1")
_start_time = time.time()


# ── Auth ──────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=dict, tags=["Auth"])
async def register(user: UserCreate):
    return register_user(user.username, user.email, user.password, user.role)


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(credentials: UserLogin):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expiry_minutes * 60,
    )


# ── Events (read) ────────────────────────────────────────────────────

@router.get("/events", response_model=EventListResponse, tags=["Events"])
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    min_severity: Optional[int] = Query(None, ge=1, le=5),
    location: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List events with filtering, search, and pagination."""
    page_events, total = event_repo.list_events(
        event_type=event_type,
        min_severity=min_severity,
        location=location,
        search=search,
        page=page,
        page_size=page_size,
    )
    return EventListResponse(
        events=[EventResponse(**e) for e in page_events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/alerts", tags=["OpenClaw"])
async def list_alerts(
    min_severity: int = Query(3, ge=1, le=5),
    limit: int = Query(10, ge=1, le=50),
    _api_key: str = Depends(verify_openclaw_api_key),
):
    """List recent high-severity events for OpenClaw bridge. Auth: X-API-Key header."""
    page_events, _ = event_repo.list_events(
        min_severity=min_severity,
        page=1,
        page_size=limit,
    )
    return {"events": page_events, "count": len(page_events)}


@router.get("/events/{event_id}", response_model=EventResponse, tags=["Events"])
async def get_event(event_id: str, current_user: dict = Depends(get_current_user)):
    event = event_repo.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse(**event)


# ── Impacts (Impact Prediction Engine) ────────────────────────────────

@router.get("/events/{event_id}/impacts", tags=["Impacts"])
async def list_impacts_for_event(
    event_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List predicted impacts for an event."""
    event = event_repo.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    from db.impact_store import get_impact_store
    store = get_impact_store()
    impacts = store.list_impacts_for_event(event_id, limit=limit)
    return {"event_id": event_id, "impacts": impacts, "count": len(impacts)}


@router.get("/impacts/{impact_id}", tags=["Impacts"])
async def get_impact(impact_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single impact with explanation."""
    from db.impact_store import get_impact_store
    store = get_impact_store()
    impact = store.get_impact(impact_id)
    if not impact:
        raise HTTPException(status_code=404, detail="Impact not found")
    explanation = None
    if impact.get("explanation_id"):
        explanation = store.get_explanation(impact["explanation_id"])
    return {"impact": impact, "explanation": explanation}


@router.post("/events/{event_id}/predict-impacts", tags=["Impacts"])
async def trigger_impact_prediction(
    event_id: str,
    current_user: dict = Depends(require_role("analyst")),
):
    """Manually trigger impact prediction for an event."""
    event = event_repo.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    from services.impact_prediction.engine import predict_impacts
    impacts = predict_impacts(event)
    return {"status": "completed", "event_id": event_id, "impacts_created": len(impacts), "impacts": impacts}


# ── Ingestion ─────────────────────────────────────────────────────────

@router.post("/ingest", response_model=dict, tags=["Ingestion"])
async def ingest_signal(
    signal: SignalCreate,
    current_user: dict = Depends(require_role("analyst")),
):
    """Push a single signal through the full pipeline."""
    signal_dict = signal.model_dump()
    signal_dict["signal_id"] = str(uuid.uuid4())

    result = process_signal(signal_dict)

    if result:
        return {"status": "accepted", "event": result}
    return {"status": "rejected", "reason": "filtered_or_duplicate"}


@router.post("/ingest/batch", response_model=dict, tags=["Ingestion"])
async def ingest_batch(
    batch: BatchSignalCreate,
    current_user: dict = Depends(require_role("analyst")),
):
    """Push multiple signals through the pipeline in one request."""
    accepted = 0
    rejected = 0

    for signal in batch.signals:
        signal_dict = signal.model_dump()
        signal_dict["signal_id"] = str(uuid.uuid4())
        result = process_signal(signal_dict)
        if result:
            accepted += 1
        else:
            rejected += 1

    event_repo.record_ingestion(filtered=accepted, rejected=rejected)
    return {"accepted": accepted, "rejected": rejected, "total": len(batch.signals)}


# ── Pipeline ──────────────────────────────────────────────────────────

@router.get("/pipeline/status", response_model=PipelineStatsResponse, tags=["Pipeline"])
async def pipeline_status(current_user: dict = Depends(get_current_user)):
    stats = event_repo.get_stats()
    return PipelineStatsResponse(
        **stats,
        dedup_index_size=get_deduplicator().get_index_size(),
        uptime_seconds=round(time.time() - _start_time, 1),
        collector_status="active",
    )


@router.post("/pipeline/trigger", response_model=dict, tags=["Pipeline"])
async def trigger_pipeline(current_user: dict = Depends(require_role("admin"))):
    """Manually trigger one pipeline collection cycle."""
    from pipeline.orchestrator import build_collectors, run_pipeline_cycle
    collectors = build_collectors()
    stats = await run_pipeline_cycle(collectors)
    return {"status": "completed", **stats}


# ── Admin ─────────────────────────────────────────────────────────────

@router.delete(
    "/events/{event_id}",
    tags=["Admin"],
    dependencies=[Depends(require_role("admin"))],
)
async def delete_event(event_id: str):
    if event_repo.delete_event(event_id):
        return {"status": "deleted", "event_id": event_id}
    raise HTTPException(status_code=404, detail="Event not found")


@router.get("/events/types/summary", tags=["Events"])
async def event_type_summary(current_user: dict = Depends(get_current_user)):
    """Return count of events grouped by event_type."""
    all_events, _ = event_repo.list_events(page_size=10000)
    summary: dict = {}
    for e in all_events:
        t = e.get("event_type", "unknown")
        summary[t] = summary.get(t, 0) + 1
    return {"types": summary, "total": len(all_events)}


@router.post("/admin/rotate-keys", tags=["Admin"])
async def rotate_encryption_keys(current_user: dict = Depends(require_role("admin"))):
    """Re-encrypt all stored events with the current (newest) Fernet key.

    Workflow:
      1. Generate a new key (or use manage_keys.py)
      2. Move old FERNET_KEY → FERNET_KEYS_PREVIOUS
      3. Set new FERNET_KEY, restart the service
      4. Call this endpoint to re-encrypt all data
    """
    result = event_repo.re_encrypt_all()
    return {"status": "rotation_complete", **result}


@router.get("/admin/key-health", tags=["Admin"])
async def key_health(current_user: dict = Depends(require_role("admin"))):
    """Report encryption key status (without revealing key material)."""
    from utils.security_utils import get_key_manager
    km = get_key_manager()
    return {
        "active_keys": km.key_count,
        "rotation_needed": km.key_count > 1,
        "encrypt_sensitive_fields": settings.encrypt_sensitive_fields,
    }


# ── Dead-letter queue ────────────────────────────────────────────

@router.get("/admin/dlq", tags=["Admin"])
async def list_dlq(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_role("admin")),
):
    """List failed signals in the dead-letter queue."""
    from ingestion.dlq import list_entries, count
    entries = list_entries(limit=limit, offset=offset)
    return {"entries": entries, "total": count(), "limit": limit, "offset": offset}


@router.delete("/admin/dlq/{dlq_id}", tags=["Admin"])
async def remove_dlq_entry(dlq_id: str, current_user: dict = Depends(require_role("admin"))):
    """Remove a single entry from the DLQ."""
    from ingestion.dlq import remove
    if remove(dlq_id):
        return {"status": "removed", "dlq_id": dlq_id}
    raise HTTPException(status_code=404, detail="DLQ entry not found")


@router.delete("/admin/dlq", tags=["Admin"])
async def clear_dlq(current_user: dict = Depends(require_role("admin"))):
    """Clear all entries from the dead-letter queue."""
    from ingestion.dlq import clear
    clear()
    return {"status": "cleared"}
