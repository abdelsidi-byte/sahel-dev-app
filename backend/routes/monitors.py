# Sahel Dev - Monitors Routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db, Monitor, Check, User
from auth import get_current_user

router = APIRouter()


class MonitorCreate(BaseModel):
    name: str
    url: str
    method: str = "GET"
    interval: int = 300


class MonitorResponse(BaseModel):
    id: int
    name: str
    url: str
    method: str
    interval: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/")
async def list_monitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all monitors for current user"""
    monitors = db.query(Monitor).filter(Monitor.user_id == current_user.id).all()
    return [MonitorResponse.model_validate(m) for m in monitors]


@router.post("/")
async def create_monitor(
    monitor: MonitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new monitor"""
    # Check plan limits
    from database import PlanEnum
    monitors_count = db.query(Monitor).filter(Monitor.user_id == current_user.id).count()

    if current_user.plan == PlanEnum.FREE and monitors_count >= 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free plan limit reached. Upgrade to Pro for unlimited monitors."
        )

    new_monitor = Monitor(
        name=monitor.name,
        url=monitor.url,
        method=monitor.method,
        interval=monitor.interval,
        user_id=current_user.id
    )
    db.add(new_monitor)
    db.commit()
    db.refresh(new_monitor)

    return MonitorResponse.model_validate(new_monitor)


@router.get("/{monitor_id}")
async def get_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific monitor"""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    return MonitorResponse.model_validate(monitor)


@router.delete("/{monitor_id}")
async def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a monitor"""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    db.delete(monitor)
    db.commit()

    return {"message": "Monitor deleted"}


@router.get("/{monitor_id}/checks")
async def get_monitor_checks(
    monitor_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent checks for a monitor"""
    monitor = db.query(Monitor).filter(
        Monitor.id == monitor_id,
        Monitor.user_id == current_user.id
    ).first()

    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found"
        )

    checks = db.query(Check).filter(
        Check.monitor_id == monitor_id
    ).order_by(Check.checked_at.desc()).limit(limit).all()

    return checks