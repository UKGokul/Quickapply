from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models.profile import Profile
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.pdf_parser import extract_text_from_pdf
import os
from uuid import uuid4

router = APIRouter(prefix="/profile", tags=["Profile"])
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"
ALLOWED_CV_MIME_TYPE = "application/pdf"
MAX_CV_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

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

# --- Routes ---
@router.get("/me")
async def get_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        return {"message": "No profile yet", "user_id": user_id}

    return profile

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
    # Validate MIME type
    if file.content_type != ALLOWED_CV_MIME_TYPE:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": "Only PDF files are allowed.",
                "field": "file",
                "expected_mime_type": ALLOWED_CV_MIME_TYPE
            }
        )

    # Save file temporarily using a unique filename while enforcing max size
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", f"{uuid4().hex}.pdf")
    total_size = 0

    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)  # 1 MB chunks
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > MAX_CV_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "code": "FILE_TOO_LARGE",
                            "message": "File exceeds the maximum allowed size.",
                            "field": "file",
                            "max_size_bytes": MAX_CV_FILE_SIZE_BYTES
                        }
                    )

                buffer.write(chunk)

        # Extract text
        raw_text = extract_text_from_pdf(file_path)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

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
