# Sahel Dev - Status Pages Routes
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db, StatusPage, User
from auth import get_current_user

router = APIRouter()


class StatusPageCreate(BaseModel):
    title: str
    slug: str
    description: str = ""


class StatusPageResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/")
async def list_status_pages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all status pages for current user"""
    pages = db.query(StatusPage).filter(StatusPage.user_id == current_user.id).all()
    return [StatusPageResponse.model_validate(p) for p in pages]


@router.post("/")
async def create_status_page(
    page: StatusPageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new status page"""
    # Check if slug is already taken
    existing = db.query(StatusPage).filter(StatusPage.slug == page.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already taken. Please choose another."
        )

    new_page = StatusPage(
        title=page.title,
        slug=page.slug,
        description=page.description,
        user_id=current_user.id
    )
    db.add(new_page)
    db.commit()
    db.refresh(new_page)

    return StatusPageResponse.model_validate(new_page)


@router.get("/{slug}")
async def get_status_page(slug: str, db: Session = Depends(get_db)):
    """Get public status page by slug"""
    page = db.query(StatusPage).filter(StatusPage.slug == slug).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status page not found"
        )

    return StatusPageResponse.model_validate(page)


@router.delete("/{page_id}")
async def delete_status_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a status page"""
    page = db.query(StatusPage).filter(
        StatusPage.id == page_id,
        StatusPage.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status page not found"
        )

    db.delete(page)
    db.commit()

    return {"message": "Status page deleted"}