from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session
from ..models.db_models import Resume
from ..models.schemas import (
    DetailedJobRecommendation,
    DetailedJobResponse,
    JobFilterParams,
    JobRecommendationResponse,
    MatchBreakdown,
    SkillGapAnalysis,
)
from ..services.job_recommender import (
    semantic_match_jobs,
    semantic_match_single_job,
    get_all_jobs,
    filter_jobs_by_location,
    generate_location_jobs,
)
from ..services.groq_client import groq_json

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/recommend/{resume_id}", response_model=JobRecommendationResponse)
async def get_job_recommendations(resume_id: str, session: AsyncSession = Depends(get_session)):
    """Legacy endpoint: returns simple job recommendations."""
    result = await session.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found. Upload resume first.")
    exp_level = getattr(resume, "experience_level", None) or "mid"
    detailed = await semantic_match_jobs(
        skills=resume.skills or [],
        experience=resume.experience or [],
        inferred_roles=resume.inferred_roles or [],
        experience_level=exp_level,
    )
    jobs = [
        {"id": j["id"], "title": j["title"], "company": j["company"],
         "location": j["location"], "matchScore": j["matchScore"],
         "reason": j["reason"], "url": j["url"]}
        for j in detailed[:10]
    ]
    return JobRecommendationResponse(jobs=jobs)


@router.get("/discover/{resume_id}", response_model=DetailedJobResponse)
async def discover_jobs(
    resume_id: str,
    location: Optional[str] = Query(None),
    remote: Optional[str] = Query(None),
    seniority: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Enhanced discovery: semantic match + filter + skill gap analysis.
    If location is provided, prioritizes jobs near that location
    and generates location-specific listings via AI."""
    result = await session.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    filters = {k: v for k, v in {
        "remote": remote,
        "seniority": seniority,
        "domain": domain,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "search": search,
    }.items() if v is not None}

    exp_level = getattr(resume, "experience_level", None) or "mid"
    jobs = await semantic_match_jobs(
        skills=resume.skills or [],
        experience=resume.experience or [],
        inferred_roles=resume.inferred_roles or [],
        experience_level=exp_level,
        filters=filters,
    )

    # If location provided, boost local + remote jobs and add AI-generated local listings
    if location:
        jobs = filter_jobs_by_location(jobs, location)
        try:
            local_jobs = await generate_location_jobs(
                skills=resume.skills or [],
                inferred_roles=resume.inferred_roles or [],
                location=location,
                experience_level=exp_level,
            )
            # Merge AI-generated jobs (with moderate match scores) into results
            for lj in local_jobs:
                lj["matchScore"] = 70
                lj["reason"] = f"AI-matched role in {location} based on your profile"
                lj["matchingSkills"] = [s for s in (resume.skills or []) if s.lower() in [rs.lower() for rs in lj.get("skills", [])]]
                lj["missingSkills"] = [s for s in lj.get("skills", []) if s.lower() not in [cs.lower() for cs in (resume.skills or [])]]
                lj["requiredSkills"] = lj.get("skills", [])
                lj["breakdown"] = {"skillScore": 30, "experienceScore": 15, "titleScore": 15, "domainScore": 10}
            jobs = local_jobs + jobs
        except Exception:
            pass

    detailed = []
    for j in jobs:
        detailed.append(DetailedJobRecommendation(
            id=j["id"],
            title=j["title"],
            company=j["company"],
            location=j["location"],
            remote=j.get("remote", "onsite"),
            salary_min=j.get("salary_min"),
            salary_max=j.get("salary_max"),
            currency=j.get("currency", "USD"),
            matchScore=j["matchScore"],
            reason=j["reason"],
            requiredSkills=j.get("requiredSkills", []),
            matchingSkills=j.get("matchingSkills", []),
            missingSkills=j.get("missingSkills", []),
            domain=j.get("domain", "general"),
            seniority=j.get("seniority", "mid"),
            description=j.get("description", ""),
            url=j.get("url", ""),
            breakdown=MatchBreakdown(**j["breakdown"]) if j.get("breakdown") else None,
        ))

    return DetailedJobResponse(
        jobs=detailed,
        total=len(detailed),
        filters=filters,
    )


@router.get("/browse", response_model=DetailedJobResponse)
async def browse_jobs(
    remote: Optional[str] = Query(None),
    seniority: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
):
    """Browse all jobs without candidate matching."""
    filters = {k: v for k, v in {
        "remote": remote,
        "seniority": seniority,
        "domain": domain,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "search": search,
    }.items() if v is not None}

    jobs = get_all_jobs(filters)
    detailed = []
    for j in jobs:
        detailed.append(DetailedJobRecommendation(
            id=j["id"],
            title=j["title"],
            company=j["company"],
            location=j["location"],
            remote=j.get("remote", "onsite"),
            salary_min=j.get("salary_min"),
            salary_max=j.get("salary_max"),
            currency=j.get("currency", "USD"),
            matchScore=0,
            reason="Browse mode — upload resume for personalized match scores",
            requiredSkills=j.get("skills", []),
            matchingSkills=[],
            missingSkills=[],
            domain=j.get("domain", "general"),
            seniority=j.get("seniority", "mid"),
            description=j.get("description", ""),
            url=j.get("url", ""),
        ))

    return DetailedJobResponse(jobs=detailed, total=len(detailed), filters=filters)


@router.get("/detail/{job_id}", response_model=DetailedJobRecommendation)
async def get_job_detail(job_id: str, resume_id: Optional[str] = Query(None), session: AsyncSession = Depends(get_session)):
    """Get detailed job info with optional resume-based matching."""
    candidate_skills = []
    if resume_id:
        result = await session.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        if resume:
            candidate_skills = resume.skills or []

    detail = await semantic_match_single_job(candidate_skills, job_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Job not found")

    return DetailedJobRecommendation(
        id=detail["id"],
        title=detail["title"],
        company=detail["company"],
        location=detail["location"],
        remote=detail.get("remote", "onsite"),
        salary_min=detail.get("salary_min"),
        salary_max=detail.get("salary_max"),
        currency=detail.get("currency", "USD"),
        matchScore=len(detail.get("matchingSkills", [])) * 10 if detail.get("matchingSkills") else 0,
        reason="Job detail view",
        requiredSkills=detail.get("requiredSkills", []),
        matchingSkills=detail.get("matchingSkills", []),
        missingSkills=detail.get("missingSkills", []),
        description=detail.get("description", ""),
        url=detail.get("url", ""),
    )


@router.post("/semantic-match", response_model=dict)
async def semantic_match(body: dict):
    """Use Groq to semantically evaluate a single resume-job pair."""
    skills = body.get("skills", [])
    experience = body.get("experience", [])
    job_id = body.get("job_id", "")

    for job in get_all_jobs({}):
        if job["id"] == job_id:
            exp_str = "; ".join([f"{e.get('title', '')} ({e.get('years', 0)} yrs)" for e in experience])
            prompt = (
                f"Candidate Skills: {', '.join(skills)}\n"
                f"Candidate Experience: {exp_str}\n\n"
                f"Job Title: {job['title']}\n"
                f"Company: {job['company']}\n"
                f"Required Skills: {', '.join(job['skills'])}\n"
                f"Description: {job['description']}\n\n"
                f"Evaluate the semantic fit between this candidate and job."
            )
            result = await groq_json("job_semantic_matcher", prompt, temperature=0.2, max_tokens=1000)
            return {
                "job_id": job_id,
                "semanticMatch": result or {},
            }
    raise HTTPException(status_code=404, detail="Job not found")


@router.get("/filters", response_model=dict)
async def get_filter_options():
    """Return all available filter options."""
    domains = list(set(j.get("domain", "general") for j in get_all_jobs({})))
    seniorities = list(set(j.get("seniority", "mid") for j in get_all_jobs({})))
    remote_types = list(set(j.get("remote", "onsite") for j in get_all_jobs({})))
    return {
        "domains": sorted(domains),
        "seniorities": sorted(seniorities),
        "remoteTypes": sorted(remote_types),
        "salaryRange": {"min": 75000, "max": 280000},
    }
