from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # What are you applying for
    type = Column(String, nullable=False)  # job, phd, masters, postdoc
    position_title = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    location = Column(String, nullable=True)

    # The raw job ad text the user pastes in
    job_ad_text = Column(Text, nullable=True)

    # Status pipeline
    status = Column(String, default="draft")
    # draft → applied → acknowledged → interview → offer → rejected

    # Key dates
    deadline = Column(DateTime, nullable=True)
    applied_date = Column(DateTime, nullable=True)

    # Contact
    contact_email = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)

    # Generated documents (stored as text)
    generated_cv = Column(Text, nullable=True)
    generated_cover_letter = Column(Text, nullable=True)
    generated_sop = Column(Text, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    reminders = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
