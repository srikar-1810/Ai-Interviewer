import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())[:8]


class User(Base):
    __tablename__ = "users"

    id = Column(String(8), primary_key=True, default=_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=True)
    salt = Column(String(32), nullable=True)
    provider = Column(String(20), nullable=True)  # google, github, local
    provider_id = Column(String(100), nullable=True)
    token = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(8), primary_key=True, default=_uuid)
    user_id = Column(String(8), ForeignKey("users.id"), nullable=True)
    raw_text = Column(Text, nullable=True)
    skills = Column(JSON, default=list)
    skill_scores = Column(JSON, default=dict)
    experience = Column(JSON, default=list)
    experience_level = Column(String(20), default="beginner")
    projects = Column(JSON, default=list)
    project_impact = Column(JSON, default=list)
    inferred_roles = Column(JSON, default=list)
    market_roles = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    resume_weaknesses = Column(JSON, default=list)
    candidate_summary = Column(JSON, default=dict)
    interview_focus_areas = Column(JSON, default=list)
    probing_areas = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=_now)

    user = relationship("User", back_populates="resumes")
    sessions = relationship("InterviewSession", back_populates="resume", cascade="all, delete-orphan")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(32), primary_key=True)
    user_id = Column(String(8), ForeignKey("users.id"), nullable=True)
    resume_id = Column(String(8), ForeignKey("resumes.id"), nullable=True)
    config = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    state = Column(JSON, default=dict)
    visual_metrics = Column(JSON, default=dict)
    metrics = Column(JSON, default=dict)
    adaptation_log = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    resume = relationship("Resume", back_populates="sessions")
    questions = relationship("InterviewQA", back_populates="session", cascade="all, delete-orphan")


class InterviewQA(Base):
    __tablename__ = "interview_qa"

    id = Column(String(8), primary_key=True, default=_uuid)
    session_id = Column(String(8), ForeignKey("interview_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="technical")
    difficulty = Column(String(20), default="medium")
    answer_text = Column(Text, nullable=True)
    technical_score = Column(Integer, default=0)
    communication_score = Column(Integer, default=0)
    confidence_score = Column(Integer, default=0)
    depth_score = Column(Integer, default=0)
    audio_metrics = Column(JSON, default=dict)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    session = relationship("InterviewSession", back_populates="questions")
