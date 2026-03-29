from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime, date, time
from database import get_db
from models.application import Application
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

router = APIRouter(prefix="/applications", tags=["Applications"])
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- Schemas ---
class ApplicationCreate(BaseModel):
    type: str                          # job, masters, phd, postdoc
    position_title: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    job_ad_text: Optional[str] = None
    deadline: Optional[date] = None     # YYYY-MM-DD
    @validator("deadline", pre=True)
    def validate_deadline_format(cls, value):
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError("Invalid deadline format. Expected YYYY-MM-DD") from exc
        raise ValueError("Invalid deadline format. Expected YYYY-MM-DD")
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    notes: Optional[str] = None

class ApplicationStatusUpdate(BaseModel):
    status: str  # draft, applied, acknowledged, interview, offer, rejected

# --- Routes ---
@router.get("/")
async def list_applications(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Application).where(Application.user_id == user_id)
    )
    applications = result.scalars().all()
    return {"applications": [
        {
            "id": app.id,
            "type": app.type,
            "position_title": app.position_title,
            "organization": app.organization,
            "status": app.status,
            "deadline": app.deadline,
            "contact_email": app.contact_email,
            "notes": app.notes,
            "created_at": app.created_at
        } for app in applications
    ]}

@router.post("/")
async def create_application(
    data: ApplicationCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    application = Application(
        user_id=user_id,
        type=data.type,
        position_title=data.position_title,
        organization=data.organization,
        location=data.location,
        job_ad_text=data.job_ad_text,
        deadline=datetime.combine(data.deadline, time.min) if data.deadline else None,
        contact_email=data.contact_email,
        contact_name=data.contact_name,
        notes=data.notes,
        status="draft"
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return {
        "message": "Application created",
        "application_id": application.id,
        "status": application.status,
        "deadline_format": "YYYY-MM-DD"
    }

@router.patch("/{application_id}/status")
async def update_status(
    application_id: str,
    data: ApplicationStatusUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user_id
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    valid_statuses = ["draft", "applied", "acknowledged", "interview", "offer", "rejected"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid_statuses}")

    app.status = data.status
    await db.commit()
    return {"message": "Status updated", "new_status": app.status}

@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user_id
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    await db.delete(app)
    await db.commit()
    return {"message": "Application deleted"}