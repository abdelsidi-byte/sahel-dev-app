# Sahel Dev - Monitoring Endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta

from database import get_db, Monitor, Check, User
from auth import get_current_user

router = APIRouter()


class UptimeStatsResponse(BaseModel):
    uptime: float
    total: int
    avg_response: float
    last_check: datetime


@router.get("/{monitor_id}/stats")
async def get_monitor_stats(
    monitor_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get uptime statistics for a monitor"""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    since = datetime.utcnow() - timedelta(days=days)
    checks = db.query(Check).filter(
        Check.monitor_id == monitor_id,
        Check.checked_at >= since
    ).order_by(Check.checked_at.desc()).all()

    if not checks:
        return {
            "uptime": 0,
            "total": 0,
            "avg_response": 0,
            "last_check": None
        }

    total = len(checks)
    up = sum(1 for c in checks if c.is_up)
    response_times = [c.response_time for c in checks if c.response_time and c.response_time > 0]

    return {
        "uptime": round((up / total) * 100, 2) if total > 0 else 0,
        "total": total,
        "avg_response": round(sum(response_times) / len(response_times), 0) if response_times else 0,
        "last_check": checks[0].checked_at if checks else None
    }


@router.post("/{monitor_id}/run")
async def run_check_now(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a check immediately"""
    from worker import MonitoringWorker

    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    worker = MonitoringWorker()
    worker.run_check(monitor_id)

    return {"message": "Check triggered", "monitor_id": monitor_id}


@router.get("/history")
async def get_check_history(
    monitor_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get check history for a monitor"""
    from database import Check

    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    checks = db.query(Check).filter(
        Check.monitor_id == monitor_id
    ).order_by(Check.checked_at.desc()).limit(limit).all()

    return [
        {
            "id": c.id,
            "status_code": c.status_code,
            "response_time": c.response_time,
            "is_up": c.is_up,
            "error_message": c.error_message,
            "checked_at": c.checked_at
        }
        for c in checks
    ]