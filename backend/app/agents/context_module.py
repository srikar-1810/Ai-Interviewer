"""
Context Understanding Module (Agent 1)
Advanced agentic resume parsing with:
1. Skill confidence scoring
2. Experience level classification
3. Missing skill detection
4. Project impact analysis
5. Resume weakness identification
6. Market-aligned role inference
7. Interview focus area generation
8. Candidate strength summary
9. Dynamic probing areas based on resume gaps
"""

from typing import Optional
from ..services.groq_client import groq_json

SKILL_KEYWORDS = {
    "frontend": ["react", "vue", "angular", "typescript", "javascript", "css", "html", "nextjs", "tailwind"],
    "backend": ["node", "python", "java", "go", "rust", "fastapi", "django", "flask", "spring", "graphql"],
    "devops": ["docker", "kubernetes", "ci/cd", "aws", "gcp", "azure", "terraform", "jenkins", "linux"],
    "data": ["sql", "pandas", "numpy", "tensorflow", "pytorch", "machine learning", "data analysis", "python"],
    "mobile": ["react native", "flutter", "swift", "kotlin", "ios", "android"],
    "product": ["product management", "agile", "scrum", "roadmap", "stakeholder", "strategy"],
    "qa": ["testing", "selenium", "cypress", "jest", "pytest", "unit test", "e2e"],
}

ROLE_INFERENCE_RULES = [
    {"role": "Frontend Engineer", "required": ["frontend"], "optional": ["backend"], "strength": 0.9},
    {"role": "Backend Engineer", "required": ["backend"], "optional": ["frontend", "devops"], "strength": 0.85},
    {"role": "Full Stack Developer", "required": ["frontend", "backend"], "optional": ["devops"], "strength": 0.95},
    {"role": "DevOps Engineer", "required": ["devops"], "optional": ["backend"], "strength": 0.85},
    {"role": "Data Analyst", "required": ["data"], "optional": ["backend"], "strength": 0.85},
    {"role": "Data Scientist / ML Engineer", "required": ["data"], "optional": ["backend", "devops"], "strength": 0.9},
    {"role": "Mobile Developer", "required": ["mobile"], "optional": ["frontend", "backend"], "strength": 0.85},
    {"role": "Product Manager", "required": ["product"], "optional": ["frontend", "backend", "data"], "strength": 0.8},
    {"role": "QA Engineer", "required": ["qa"], "optional": ["backend", "frontend"], "strength": 0.8},
    {"role": "Software Engineer (General)", "required": ["frontend", "backend"], "optional": ["devops", "data"], "strength": 0.7},
]


async def parse_resume_text_async(text: str) -> Optional[dict]:
    result = await groq_json(
        "resume_parser",
        f"Parse this resume and extract skills, experience, projects, and infer job roles:\n\n{text[:4000]}",
        temperature=0.2,
        max_tokens=2000,
    )
    if result and "skills" in result:
        if "inferredRoles" not in result:
            result["inferredRoles"] = _infer_roles(result.get("skills", []), result.get("experience", []))
        return result
    return None


def _detect_domains(skills: list[str]) -> dict[str, float]:
    scores: dict[str, float] = {}
    skills_lower = [s.lower() for s in skills]
    for domain, keywords in SKILL_KEYWORDS.items():
        matches = sum(1 for kw in keywords if any(kw in s for s in skills_lower))
        scores[domain] = min(matches / max(len(keywords) * 0.15, 1), 1.0)
    return scores


def _compute_seniority(experience: list[dict]) -> str:
    total_years = sum(int(exp.get("years", 0)) for exp in experience)
    if total_years >= 8:
        return "senior"
    elif total_years >= 3:
        return "mid"
    return "junior"


def _infer_roles(skills: list[str], experience: list[dict]) -> list[dict]:
    domain_scores = _detect_domains(skills)
    seniority = _compute_seniority(experience)
    results = []
    for rule in ROLE_INFERENCE_RULES:
        required_score = sum(domain_scores.get(d, 0) for d in rule["required"]) / max(len(rule["required"]), 1)
        optional_score = sum(domain_scores.get(d, 0) for d in rule["optional"]) / max(len(rule["optional"]), 1) if rule["optional"] else 0
        if required_score == 0:
            continue
        match = int((required_score * 0.7 + optional_score * 0.3) * rule["strength"] * 100)
        match = min(match, 99)
        seniority_labels = {"junior": "Junior ", "mid": "", "senior": "Senior "}
        label = f"{seniority_labels.get(seniority, '')}{rule['role']}"
        reason_parts = []
        matched_domains = [d for d in rule["required"] + rule["optional"] if domain_scores.get(d, 0) > 0.3]
        if matched_domains:
            reason_parts.append(f"Detected {', '.join(matched_domains)} expertise")
        if domain_scores.get("devops", 0) > 0.3:
            reason_parts.append("with DevOps exposure")
        reason = "; ".join(reason_parts) if reason_parts else "General engineering profile"
        if match > 20:
            results.append({"role": label, "match": match, "reason": reason.capitalize()})
    results.sort(key=lambda x: x["match"], reverse=True)
    return results[:5]


def parse_resume_text(text: str) -> dict:
    """Pure heuristic fallback — no asyncio calls."""
    text_lower = text.lower()
    sentences = [s.strip() for s in text.split("\n") if s.strip()]

    skills = []
    for domain, keywords in SKILL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower and kw not in skills:
                skills.append(kw.title())

    experience = []
    current_title = ""
    current_company = ""
    for line in sentences:
        if any(word in line.lower() for word in ["engineer", "developer", "intern", "manager", "analyst", "lead", "architect"]):
            current_title = line.strip()
        elif any(word in line.lower() for word in ["at ", "company:", "organization:" "inc", "corp", "ltd", "technologies", "tech"]):
            current_company = line.strip()
        if current_title and current_company:
            experience.append({"title": current_title[:60], "company": current_company[:60], "years": 2})
            current_title = ""
            current_company = ""

    if not experience:
        experience.append({"title": "Software Engineer", "company": "Previous Company", "years": 3})

    projects = []
    in_project = False
    for line in sentences:
        if "project" in line.lower() and (":" in line or "-" in line):
            parts = line.split(":", 1)
            name = parts[0].replace("-", "").strip()
            desc = parts[1].strip() if len(parts) > 1 else "Key project experience"
            if len(name) < 50:
                projects.append({"name": name[:50], "description": desc[:120]})
                in_project = True
        elif in_project and len(projects) > 0 and len(line) > 20:
            projects[-1]["description"] += " " + line[:100]

    if not skills:
        skills = ["JavaScript", "Python", "React", "Node.js", "SQL"]
    if not projects:
        projects.append({"name": "Sample Project", "description": "Built using modern tech stack"})

    inferred_roles = _infer_roles(skills, experience)

    return {
        "skills": list(set(skills))[:15],
        "experience": experience[:5],
        "projects": projects[:5],
        "inferredRoles": inferred_roles,
    }


# =============================================================================
# Advanced Context Understanding Functions
# =============================================================================

async def analyze_skill_confidence(text: str, skills: list[str]) -> list[dict]:
    """Score each skill on confidence (0-99) based on evidence in resume text."""
    result = await groq_json(
        "skill_confidence_scorer",
        f"Resume text:\n{text[:3000]}\n\nExtracted skills: {', '.join(skills)}\n\nScore each skill on confidence (0-99). For each skill, include a concise 'evidence' field (one short sentence describing how the skill was demonstrated in the resume, e.g. 'Built 3 REST APIs using the framework').",
        temperature=0.2,
        max_tokens=1500,
    )
    if result and "skillScores" in result:
        return result["skillScores"]
    return _heuristic_skill_scores(text, skills)


def _heuristic_skill_scores(text: str, skills: list[str]) -> list[dict]:
    """Fallback: score skills based on frequency and contextual depth."""
    text_lower = text.lower()
    scores = []
    for skill in skills:
        skill_lower = skill.lower()
        count = text_lower.count(skill_lower)
        score = min(count * 10 + 30, 95)
        if score < 30:
            score = max(count * 15, 10)
        category = "general"
        for domain, keywords in SKILL_KEYWORDS.items():
            if skill_lower in keywords:
                category = domain
                break
        scores.append({
            "skill": skill,
            "score": score,
            "category": category,
            "evidence": "Applied across resume with practical context" if count > 2 else ("Listed as a key skill with supporting experience" if count > 0 else "Listed but not elaborated"),
        })
    return scores


async def classify_experience_level(experience: list[dict], text: str) -> Optional[dict]:
    """Classify overall experience level: beginner, intermediate, or advanced."""
    experience_str = "; ".join([f"{e.get('title', '')} at {e.get('company', '')} ({e.get('years', 0)} yrs)" for e in experience])
    result = await groq_json(
        "experience_classifier",
        f"Experience:\n{experience_str}\n\nResume text:\n{text[:2000]}\n\nClassify experience level.",
        temperature=0.2,
        max_tokens=500,
    )
    if result and "level" in result:
        return result
    total_years = sum(e.get("years", 0) for e in experience)
    if total_years >= 8:
        return {"level": "advanced", "totalYears": total_years, "reasoning": f"{total_years}+ years of experience with senior-level roles"}
    elif total_years >= 3:
        return {"level": "intermediate", "totalYears": total_years, "reasoning": f"{total_years} years with mid-level progression"}
    return {"level": "beginner", "totalYears": total_years, "reasoning": f"{total_years} years, early career stage"}


async def detect_missing_skills(skills: list[str], inferred_roles: list[dict]) -> list[dict]:
    """Detect important missing skills for each inferred job role."""
    roles_str = "; ".join([f"{r.get('role', '')} (match: {r.get('match', 0)}%)" for r in inferred_roles])
    result = await groq_json(
        "missing_skill_detector",
        f"Current skills: {', '.join(skills)}\n\nTarget roles: {roles_str}\n\nDetect missing skills.",
        temperature=0.3,
        max_tokens=1500,
    )
    if result and "missingSkills" in result:
        return result["missingSkills"]
    return _heuristic_missing_skills(skills, inferred_roles)


def _heuristic_missing_skills(skills: list[str], inferred_roles: list[dict]) -> list[dict]:
    """Fallback: detect missing skills based on role requirements."""
    skills_lower = [s.lower() for s in skills]
    role_skill_map = {
        "frontend": ["typescript", "react", "css", "testing"],
        "backend": ["python", "node", "sql", "docker", "api"],
        "devops": ["docker", "kubernetes", "aws", "ci/cd", "terraform"],
        "data": ["sql", "python", "machine learning", "statistics"],
        "mobile": ["react native", "swift", "api integration"],
        "product": ["analytics", "agile", "stakeholder management"],
        "qa": ["selenium", "automation", "test planning"],
    }
    domain_scores = _detect_domains(skills)
    missing = []
    top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for domain, score in top_domains:
        if score < 0.6:
            for req_skill in role_skill_map.get(domain, []):
                if req_skill not in skills_lower:
                    role_name = next((r["role"] for r in inferred_roles if domain in r.get("role", "").lower()), "Related role")
                    priority = "high" if score < 0.3 else "medium"
                    missing.append({
                        "skill": req_skill.title(),
                        "forRole": role_name,
                        "priority": priority,
                        "reason": f"Essential for {domain} roles, not detected in profile",
                    })
    return missing[:6]


async def analyze_project_impact(projects: list[dict]) -> list[dict]:
    """Evaluate each project's impact, complexity, and business value."""
    if not projects:
        return []
    projects_str = "\n".join([f"- {p.get('name', '')}: {p.get('description', '')}" for p in projects])
    result = await groq_json(
        "project_impact_analyzer",
        f"Projects:\n{projects_str}\n\nAnalyze each project's impact.",
        temperature=0.3,
        max_tokens=1500,
    )
    if result and "projectImpacts" in result:
        return result["projectImpacts"]
    return _heuristic_project_impact(projects)


def _heuristic_project_impact(projects: list[dict]) -> list[dict]:
    """Fallback: basic project impact assessment."""
    impacts = []
    for p in projects:
        desc = p.get("description", "").lower()
        if any(w in desc for w in ["scale", "million", "thousand", "percent", "%", "users", "traffic"]):
            complexity = "high"
        elif any(w in desc for w in ["api", "database", "pipeline", "distributed"]):
            complexity = "medium"
        else:
            complexity = "low"
        impacts.append({
            "name": p.get("name", "Project"),
            "impact": p.get("description", "")[:120],
            "technologies": [],
            "complexity": complexity,
            "businessValue": "Needs clarification" if complexity == "low" else "Demonstrated technical contribution",
        })
    return impacts


async def identify_resume_weaknesses(text: str) -> list[dict]:
    """Identify weaknesses in the resume that could hurt interview chances."""
    result = await groq_json(
        "resume_weakness_identifier",
        f"Analyze this resume for weaknesses:\n\n{text[:3000]}",
        temperature=0.3,
        max_tokens=1500,
    )
    if result and "weaknesses" in result:
        return result["weaknesses"]
    return _heuristic_weaknesses(text)


def _heuristic_weaknesses(text: str) -> list[dict]:
    """Fallback: detect common resume weaknesses."""
    weaknesses = []
    text_lower = text.lower()
    if not any(w in text_lower for w in ["%", "percent", "increased", "decreased", "reduced", "improved", "achieved"]):
        weaknesses.append({
            "area": "Quantifiable Impact",
            "severity": "high",
            "description": "No measurable outcomes or metrics found in resume",
            "suggestion": "Add specific metrics like 'Improved performance by X%' or 'Served Y users'",
        })
    short_tenure_count = 0
    years_mentioned = [int(s) for s in text.split() if s.isdigit() and 0 < int(s) < 5]
    if sum(1 for y in years_mentioned if y <= 1) > 2:
        weaknesses.append({
            "area": "Employment Stability",
            "severity": "medium",
            "description": "Multiple short tenures detected which may raise concerns",
            "suggestion": "Frame short stints as contract roles or emphasize achievements in each position",
        })
    if not weaknesses:
        weaknesses.append({
            "area": "Leadership Examples",
            "severity": "low",
            "description": "Limited evidence of leadership or mentoring",
            "suggestion": "Add examples of leading projects, mentoring juniors, or cross-team collaboration",
        })
    return weaknesses


async def infer_market_roles(skills: list[str], experience: list[dict], projects: list[dict]) -> list[dict]:
    """Market-aligned role inference considering current demand."""
    skills_str = ", ".join(skills)
    exp_str = "; ".join([f"{e.get('title', '')} ({e.get('years', 0)} yrs)" for e in experience])
    proj_str = "; ".join([p.get("name", "") for p in projects])
    result = await groq_json(
        "market_role_inferrer",
        f"Skills: {skills_str}\nExperience: {exp_str}\nProjects: {proj_str}\n\nInfer market-aligned roles.",
        temperature=0.3,
        max_tokens=1500,
    )
    if result and "marketRoles" in result:
        return result["marketRoles"]
    return _heuristic_market_roles(skills, experience)


def _heuristic_market_roles(skills: list[str], experience: list[dict]) -> list[dict]:
    """Fallback: market role inference based on domain detection."""
    domain_scores = _detect_domains(skills)
    seniority = _compute_seniority(experience)
    market_roles = []
    role_demand = {
        "frontend": {"demand": "high", "growth": "strong"},
        "backend": {"demand": "high", "growth": "strong"},
        "devops": {"demand": "high", "growth": "strong"},
        "data": {"demand": "high", "growth": "strong"},
        "mobile": {"demand": "medium", "growth": "moderate"},
        "product": {"demand": "medium", "growth": "moderate"},
        "qa": {"demand": "medium", "growth": "limited"},
    }
    seniority_label = {"junior": "Junior ", "mid": "", "senior": "Senior "}
    top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for domain, score in top_domains:
        if score > 0.3:
            role_title = next((r["role"] for r in ROLE_INFERENCE_RULES if r["required"] and r["required"][0] == domain), f"{domain.title()} Engineer")
            demand_info = role_demand.get(domain, {"demand": "medium", "growth": "moderate"})
            market_roles.append({
                "role": f"{seniority_label.get(seniority, '')}{role_title}",
                "match": int(score * 95),
                "demand": demand_info["demand"],
                "growthPotential": demand_info["growth"],
                "reason": f"Strong {domain} skill set with high market demand",
            })
    return market_roles[:5]


async def generate_focus_areas(skills: list[str], missing_skills: list[dict], experience_level: str) -> list[dict]:
    """Generate interview focus areas based on profile."""
    skills_str = ", ".join(skills)
    missing_str = "; ".join([f"{m.get('skill', '')} ({m.get('priority', '')})" for m in missing_skills])
    result = await groq_json(
        "interview_focus_generator",
        f"Skills: {skills_str}\nMissing skills: {missing_str}\nExperience level: {experience_level}\n\nGenerate interview focus areas.",
        temperature=0.3,
        max_tokens=1500,
    )
    if result and "focusAreas" in result:
        return result["focusAreas"]
    return _heuristic_focus_areas(skills, experience_level)


def _heuristic_focus_areas(skills: list[str], experience_level: str) -> list[dict]:
    """Fallback: generate focus areas based on skill domains and level."""
    domain_scores = _detect_domains(skills)
    focus_areas = []
    if experience_level == "senior" or experience_level == "advanced":
        focus_areas.append({
            "area": "System Design & Architecture",
            "priority": "high",
            "reason": "Senior-level interviews heavily test architectural thinking",
            "suggestedTopics": ["Distributed systems", "Microservices", "Database design", "Scalability patterns"],
        })
    if domain_scores.get("backend", 0) > 0.3:
        focus_areas.append({
            "area": "Backend Engineering Deep Dive",
            "priority": "high",
            "reason": "Backend skills detected — expect in-depth technical questions",
            "suggestedTopics": ["API design", "Database optimization", "Caching", "Authentication"],
        })
    if domain_scores.get("frontend", 0) > 0.3:
        focus_areas.append({
            "area": "Frontend Architecture",
            "priority": "medium",
            "reason": "Frontend skills present — prepare for component design questions",
            "suggestedTopics": ["State management", "Performance optimization", "Component architecture", "Build tooling"],
        })
    if experience_level in ("intermediate", "advanced"):
        focus_areas.append({
            "area": "Behavioral & Leadership",
            "priority": "medium",
            "reason": "Mid-to-senior interviews evaluate soft skills and leadership",
            "suggestedTopics": ["Conflict resolution", "Project ownership", "Cross-team collaboration", "Mentoring"],
        })
    focus_areas.append({
        "area": "Data Structures & Algorithms",
        "priority": "high",
        "reason": "Standard for most technical interviews",
        "suggestedTopics": ["Arrays & strings", "Trees & graphs", "Dynamic programming", "Complexity analysis"],
    })
    return focus_areas


async def generate_candidate_summary(skills: list[str], experience: list[dict], projects: list[dict]) -> Optional[dict]:
    """Generate a concise candidate profile summary."""
    skills_str = ", ".join(skills)
    exp_str = "; ".join([f"{e.get('title', '')} at {e.get('company', '')} ({e.get('years', 0)} yrs)" for e in experience])
    proj_str = "; ".join([f"{p.get('name', '')}: {p.get('description', '')[:60]}" for p in projects])
    result = await groq_json(
        "candidate_summarizer",
        f"Skills: {skills_str}\nExperience: {exp_str}\nProjects: {proj_str}\n\nGenerate candidate summary.",
        temperature=0.3,
        max_tokens=1000,
    )
    if result and "summary" in result:
        return result["summary"]
    return _heuristic_candidate_summary(skills, experience)


def _heuristic_candidate_summary(skills: list[str], experience: list[dict]) -> dict:
    """Fallback: generate summary from available data."""
    domain_scores = _detect_domains(skills)
    top_domains = [d for d, s in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True) if s > 0.3][:2]
    total_years = sum(e.get("years", 0) for e in experience)
    if total_years >= 8:
        level = "senior"
    elif total_years >= 3:
        level = "mid-level"
    else:
        level = "junior"
    domain_str = " and ".join(top_domains) if top_domains else "software engineering"
    role = f"{level.title()} {domain_str.title()} Engineer"
    return {
        "title": role,
        "strengths": [f"Proficient in {', '.join(skills[:4])}"],
        "experienceHighlight": f"{total_years}+ years in {domain_str} development" if total_years > 0 else "Building software solutions",
        "recommendedRoles": [r.get("role", "") for r in _infer_roles(skills, experience)[:3]],
        "overallAssessment": f"{level.title()} engineer with strong {domain_str} skills ready for technical interviews",
    }


async def generate_probing_areas(text: str, skills: list[str], missing_skills: list[dict]) -> list[dict]:
    """Generate dynamic probing areas based on resume gaps."""
    missing_str = "; ".join([f"{m.get('skill', '')} ({m.get('priority', '')})" for m in missing_skills]) if missing_skills else "None identified"
    result = await groq_json(
        "probing_area_generator",
        f"Resume text:\n{text[:2000]}\n\nSkills: {', '.join(skills)}\nMissing skills: {missing_str}\n\nGenerate probing areas.",
        temperature=0.3,
        max_tokens=1500,
    )
    if result and "probingAreas" in result:
        return result["probingAreas"]
    return _heuristic_probing_areas(text, skills)


def _heuristic_probing_areas(text: str, skills: list[str]) -> list[dict]:
    """Fallback: identify probing areas from text patterns."""
    probing_areas = []
    text_lower = text.lower()
    vague_terms = ["responsible for", "involved in", "participated in", "helped with"]
    has_vague = any(t in text_lower for t in vague_terms)
    if has_vague:
        probing_areas.append({
            "area": "Role clarity and ownership",
            "trigger": "Resume uses passive/vague language suggesting limited ownership",
            "probeDepth": "medium",
            "suggestedQuestions": [
                "What was your specific role and contribution?",
                "Can you describe a technical decision you owned?",
                "What was the hardest problem you solved in this role?",
            ],
        })
    if any(s.lower() in text_lower for s in skills):
        probing_areas.append({
            "area": f"Technical depth verification",
            "trigger": f"Candidate lists {skills[0] if skills else 'key skills'} — needs depth validation",
            "probeDepth": "deep",
            "suggestedQuestions": [
                f"Walk me through a project where you used {skills[0] if skills else 'your primary skill'}",
                "What trade-offs did you consider?",
                "How would you design it differently today?",
            ],
        })
    if not probing_areas:
        probing_areas.append({
            "area": "General experience exploration",
            "trigger": "Standard resume pattern detected",
            "probeDepth": "medium",
            "suggestedQuestions": [
                "Tell me about your most challenging project",
                "What technology would you like to learn next?",
                "Describe a time you had to debug a complex issue",
            ],
        })
    return probing_areas


async def analyze_context_full(text: str, skills: list[str], experience: list[dict], projects: list[dict]) -> dict:
    """Orchestrate all advanced context analyses.

    Independent analyses run concurrently. Dependent ones run sequentially.
    """
    inferred = _infer_roles(skills, experience)

    import asyncio
    indep_results = await asyncio.gather(
        identify_resume_weaknesses(text),
        analyze_skill_confidence(text, skills),
        classify_experience_level(experience, text),
        detect_missing_skills(skills, inferred),
        analyze_project_impact(projects),
        infer_market_roles(skills, experience, projects),
        generate_candidate_summary(skills, experience, projects),
        return_exceptions=True,
    )

    results = [r if not isinstance(r, Exception) else None for r in indep_results]
    weaknesses = results[0] if results[0] is not None else []
    skill_scores = results[1] if results[1] is not None else []
    exp_level = results[2] if results[2] is not None else {"level": "beginner", "totalYears": 0, "reasoning": "Analysis failed"}
    missing = results[3] if results[3] is not None else []
    impact = results[4] if results[4] is not None else []
    market_roles = results[5] if results[5] is not None else []
    summary = results[6] if results[6] is not None else {}

    exp_level_val = exp_level.get("level", "beginner") if isinstance(exp_level, dict) else "beginner"
    focus_areas = await generate_focus_areas(skills, missing, exp_level_val)
    probing_areas = await generate_probing_areas(text, skills, missing)

    return {
        "skillScores": skill_scores if isinstance(skill_scores, list) else [],
        "experienceLevel": exp_level if isinstance(exp_level, dict) else {"level": "beginner", "totalYears": 0, "reasoning": "Fallback"},
        "missingSkills": missing,
        "projectImpact": impact if isinstance(impact, list) else [],
        "resumeWeaknesses": weaknesses if isinstance(weaknesses, list) else [],
        "marketRoles": market_roles if isinstance(market_roles, list) else [],
        "candidateSummary": summary if isinstance(summary, dict) else {},
        "interviewFocusAreas": focus_areas if isinstance(focus_areas, list) else [],
        "probingAreas": probing_areas if isinstance(probing_areas, list) else [],
    }
