from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from database import get_db
from models.profile import Profile
from services.writing_agent import (
    generate_cover_letter,
    generate_motivation_letter,
    generate_sop,
    detect_document_type
)
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

router = APIRouter(prefix="/documents", tags=["Documents"])
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

class GenerateRequest(BaseModel):
    job_ad: str
    document_type: str = "auto"  # auto, cover_letter, motivation_letter, sop

@router.post("/generate")
async def generate_document(
    data: GenerateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get user profile
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No profile found. Please create your profile first."
        )

    # Convert profile to dict
    profile_dict = {
        "full_name": profile.full_name,
        "degree": profile.degree,
        "field_of_study": profile.field_of_study,
        "university": profile.university,
        "gpa": profile.gpa,
        "graduation_year": profile.graduation_year,
        "skills": profile.skills,
        "languages": profile.languages,
        "certifications": profile.certifications,
        "work_experience": profile.work_experience,
        "target_countries": profile.target_countries,
        "cv_raw_text": profile.cv_raw_text
    }

    # Auto detect document type if not specified
    doc_type = data.document_type
    if doc_type == "auto":
        doc_type = detect_document_type(data.job_ad)

    # Generate the right document
    if doc_type == "cover_letter":
        content = generate_cover_letter(profile_dict, data.job_ad)
    elif doc_type == "motivation_letter":
        content = generate_motivation_letter(profile_dict, data.job_ad)
    elif doc_type == "sop":
        content = generate_sop(profile_dict, data.job_ad)
    else:
        content = generate_cover_letter(profile_dict, data.job_ad)

    return {
        "document_type": doc_type,
        "content": content,
        "profile_used": profile.full_name
    }