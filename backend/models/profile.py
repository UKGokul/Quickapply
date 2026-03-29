from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Profile(Base):
    __tablename__ = "profiles"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id         = Column(String, nullable=False, index=True)

    # Basic info
    full_name       = Column(String, nullable=True)
    email           = Column(String, nullable=True)
    phone           = Column(String, nullable=True)
    nationality     = Column(String, nullable=True)
    location        = Column(String, nullable=True)

    # Academic
    degree          = Column(String, nullable=True)
    field_of_study  = Column(String, nullable=True)
    university      = Column(String, nullable=True)
    gpa             = Column(String, nullable=True)
    graduation_year = Column(String, nullable=True)

    # Experience & Skills
    work_experience = Column(JSON, nullable=True)   # list of jobs
    skills          = Column(JSON, nullable=True)   # list of skills
    languages       = Column(JSON, nullable=True)   # list of languages
    certifications  = Column(JSON, nullable=True)   # list of certs

    # Application targets
    target_countries   = Column(JSON, nullable=True)
    target_programs    = Column(JSON, nullable=True)
    application_types  = Column(JSON, nullable=True)  # job, phd, masters

    # Raw CV text (extracted from uploaded PDF)
    cv_raw_text     = Column(Text, nullable=True)

    # AI generated summary
    ai_summary      = Column(Text, nullable=True)
    ai_strengths    = Column(JSON, nullable=True)
    ai_gaps         = Column(JSON, nullable=True)

    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at      = Column(DateTime, default=datetime.utcnow)