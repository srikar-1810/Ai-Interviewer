from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session
from ..models.db_models import Resume, User
from ..auth_deps import require_user, get_current_user
from ..models.schemas import ResumeResponse, ContextAnalysisResponse
from ..services.resume_parser import extract_text
from ..agents.context_module import parse_resume_text_async, parse_resume_text, analyze_context_full

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(select(Resume).where(Resume.user_id == user.id))
    old = existing.scalar_one_or_none()
    if old:
        await session.delete(old)
        await session.commit()
    contents = await file.read()
    text = extract_text(contents, file.filename or "resume.pdf")
    if not text:
        raise HTTPException(status_code=400, detail="Could not parse resume file. Supported formats: PDF, DOCX, TXT")

    parsed = await parse_resume_text_async(text)
    if not parsed:
        parsed = parse_resume_text(text)

    skills = parsed.get("skills", [])
    experience = parsed.get("experience", [])
    projects = parsed.get("projects", [])
    inferred_roles = parsed.get("inferredRoles", [])

    advanced = await analyze_context_full(text, skills, experience, projects)

    exp_level_info = advanced.get("experienceLevel", {})
    if isinstance(exp_level_info, dict) and "level" in exp_level_info:
        stored_exp_level = exp_level_info
    else:
        total_years = sum(e.get("years", 0) for e in experience)
        if total_years >= 8:
            stored_exp_level = {"level": "advanced", "totalYears": total_years, "reasoning": f"{total_years}+ years experience"}
        elif total_years >= 3:
            stored_exp_level = {"level": "intermediate", "totalYears": total_years, "reasoning": f"{total_years} years experience"}
        else:
            stored_exp_level = {"level": "beginner", "totalYears": total_years, "reasoning": f"{total_years} years experience"}

    resume = Resume(
        user_id=user.id,
        raw_text=text[:5000] if text else "",
        skills=skills,
        skill_scores=advanced.get("skillScores", []),
        experience=experience,
        experience_level=stored_exp_level.get("level", "beginner"),
        projects=projects,
        project_impact=advanced.get("projectImpact", []),
        inferred_roles=inferred_roles,
        market_roles=advanced.get("marketRoles", []),
        missing_skills=advanced.get("missingSkills", []),
        resume_weaknesses=advanced.get("resumeWeaknesses", []),
        candidate_summary=advanced.get("candidateSummary", {}),
        interview_focus_areas=advanced.get("interviewFocusAreas", []),
        probing_areas=advanced.get("probingAreas", []),
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)

    return ResumeResponse(
        id=resume.id,
        skills=resume.skills or [],
        skillScores=resume.skill_scores or [],
        experience=resume.experience or [],
        experienceLevel=stored_exp_level,
        projects=resume.projects or [],
        projectImpact=resume.project_impact or [],
        inferredRoles=resume.inferred_roles or [],
        marketRoles=resume.market_roles or [],
        missingSkills=resume.missing_skills or [],
        resumeWeaknesses=resume.resume_weaknesses or [],
        candidateSummary=resume.candidate_summary or None,
        interviewFocusAreas=resume.interview_focus_areas or [],
        probingAreas=resume.probing_areas or [],
    )


@router.delete("", status_code=204)
async def delete_resume(user: User = Depends(require_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Resume).where(Resume.user_id == user.id))
    resume = result.scalar_one_or_none()
    if resume:
        await session.delete(resume)
        await session.commit()


@router.get("/analyze/{resume_id}", response_model=ContextAnalysisResponse)
async def get_resume_analysis(resume_id: str, user: User = Depends(require_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if resume.skill_scores:
        cached_exp = resume.experience or []
        total_years = sum(e.get("years", 0) for e in cached_exp)
        return ContextAnalysisResponse(
            resumeId=resume.id,
            skillScores=resume.skill_scores or [],
            experienceLevel={"level": resume.experience_level or "beginner", "totalYears": total_years, "reasoning": "From saved analysis"},
            missingSkills=resume.missing_skills or [],
            projectImpact=resume.project_impact or [],
            resumeWeaknesses=resume.resume_weaknesses or [],
            marketRoles=resume.market_roles or [],
            candidateSummary=resume.candidate_summary or None,
            interviewFocusAreas=resume.interview_focus_areas or [],
            probingAreas=resume.probing_areas or [],
        )

    text = resume.raw_text or ""
    skills = resume.skills or []
    experience = resume.experience or []
    projects = resume.projects or []

    advanced = await analyze_context_full(text, skills, experience, projects)

    new_exp_level = advanced.get("experienceLevel", {})
    if isinstance(new_exp_level, dict) and "level" in new_exp_level:
        level_str = new_exp_level.get("level", "beginner")
    else:
        total_years = sum(e.get("years", 0) for e in experience)
        level_str = "advanced" if total_years >= 8 else "intermediate" if total_years >= 3 else "beginner"

    resume.skill_scores = advanced.get("skillScores", [])
    resume.experience_level = level_str
    resume.missing_skills = advanced.get("missingSkills", [])
    resume.project_impact = advanced.get("projectImpact", [])
    resume.resume_weaknesses = advanced.get("resumeWeaknesses", [])
    resume.market_roles = advanced.get("marketRoles", [])
    resume.candidate_summary = advanced.get("candidateSummary", {})
    resume.interview_focus_areas = advanced.get("interviewFocusAreas", [])
    resume.probing_areas = advanced.get("probingAreas", [])
    await session.commit()

    total_years = sum(e.get("years", 0) for e in experience)
    return ContextAnalysisResponse(
        resumeId=resume.id,
        skillScores=resume.skill_scores or [],
        experienceLevel={"level": level_str, "totalYears": total_years, "reasoning": "From re-analysis"},
        missingSkills=resume.missing_skills or [],
        projectImpact=resume.project_impact or [],
        resumeWeaknesses=resume.resume_weaknesses or [],
        marketRoles=resume.market_roles or [],
        candidateSummary=resume.candidate_summary or None,
        interviewFocusAreas=resume.interview_focus_areas or [],
        probingAreas=resume.probing_areas or [],
    )
