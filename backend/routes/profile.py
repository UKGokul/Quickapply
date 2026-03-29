import os
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models.profile import Profile
from services.pdf_parser import extract_text_from_pdf

router = APIRouter(prefix="/profile", tags=["Profile"])
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"

# --- Auth helper ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- Pydantic schemas ---
class WorkExperience(BaseModel):
    title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    nationality: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    university: Optional[str] = None
    gpa: Optional[str] = None
    graduation_year: Optional[str] = None
    work_experience: List[WorkExperience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    target_countries: List[str] = Field(default_factory=list)
    target_programs: List[str] = Field(default_factory=list)
    application_types: List[str] = Field(default_factory=list)
    cv_raw_text: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_strengths: List[str] = Field(default_factory=list)
    ai_gaps: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProfileUpdate(BaseModel):
    full_name:          Optional[str] = None
    email:              Optional[str] = None
    phone:              Optional[str] = None
    nationality:        Optional[str] = None
    location:           Optional[str] = None
    degree:             Optional[str] = None
    field_of_study:     Optional[str] = None
    university:         Optional[str] = None
    gpa:                Optional[str] = None
    graduation_year:    Optional[str] = None
    work_experience:    Optional[List[WorkExperience]] = None
    skills:             Optional[List[str]] = None
    languages:          Optional[List[str]] = None
    certifications:     Optional[List[str]] = None
    target_countries:   Optional[List[str]] = None
    target_programs:    Optional[List[str]] = None
    application_types:  Optional[List[str]] = None


def map_profile_to_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        nationality=profile.nationality,
        location=profile.location,
        degree=profile.degree,
        field_of_study=profile.field_of_study,
        university=profile.university,
        gpa=profile.gpa,
        graduation_year=profile.graduation_year,
        work_experience=profile.work_experience or [],
        skills=profile.skills or [],
        languages=profile.languages or [],
        certifications=profile.certifications or [],
        target_countries=profile.target_countries or [],
        target_programs=profile.target_programs or [],
        application_types=profile.application_types or [],
        cv_raw_text=profile.cv_raw_text,
        ai_summary=profile.ai_summary,
        ai_strengths=profile.ai_strengths or [],
        ai_gaps=profile.ai_gaps or [],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )

# --- Routes ---
@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return map_profile_to_response(profile)

@router.post("/me")
async def create_or_update_profile(
    data: ProfileUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if profile exists
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        # Create new profile
        profile = Profile(user_id=user_id)
        db.add(profile)

    # Update fields
    for field, value in data.model_dump(exclude_none=True).items():
        if field == "work_experience" and value:
            setattr(profile, field, [w.model_dump() for w in value])
        else:
            setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return {"message": "Profile saved", "profile_id": profile.id}

@router.delete("/me")
async def delete_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    await db.delete(profile)
    await db.commit()
    return {"message": "Profile deleted"}


@router.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    # Save file temporarily
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{user_id}_cv.pdf"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text
    raw_text = extract_text_from_pdf(file_path)

    # Save to profile
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)

    profile.cv_raw_text = raw_text
    await db.commit()

    return {
        "message": "CV uploaded and parsed",
        "characters_extracted": len(raw_text),
        "preview": raw_text[:300] + "..."
    }
