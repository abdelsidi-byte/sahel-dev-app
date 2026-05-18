# Sahel Dev - Alerts Routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db, AlertChannel, User
from auth import get_current_user

router = APIRouter()


class AlertChannelCreate(BaseModel):
    name: str
    channel_type: str  # email, slack, discord, sms
    config: str  # webhook URL or email address


class AlertChannelResponse(BaseModel):
    id: int
    name: str
    channel_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/")
async def list_alert_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all alert channels for current user"""
    channels = db.query(AlertChannel).filter(AlertChannel.user_id == current_user.id).all()
    return [AlertChannelResponse.model_validate(c) for c in channels]


@router.post("/")
async def create_alert_channel(
    channel: AlertChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert channel"""
    new_channel = AlertChannel(
        name=channel.name,
        channel_type=channel.channel_type,
        config=channel.config,
        user_id=current_user.id
    )
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)

    return AlertChannelResponse.model_validate(new_channel)


@router.delete("/{channel_id}")
async def delete_alert_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an alert channel"""
    channel = db.query(AlertChannel).filter(
        AlertChannel.id == channel_id,
        AlertChannel.user_id == current_user.id
    ).first()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert channel not found"
        )

    db.delete(channel)
    db.commit()

    return {"message": "Alert channel deleted"}