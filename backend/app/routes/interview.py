from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session
from ..models.db_models import InterviewSession, InterviewQA, Resume, User
from ..auth_deps import require_user, get_current_user
from ..models.schemas import (
    InterviewStartRequest,
    AnswerRequest,
    QuestionResponse,
    AnalyzeResponse,
    InterviewMetrics,
    FeedbackResponse,
    CodingChallengeRequest, CodingChallengeResponse,
    CodingSubmitRequest, CodingEvaluationResponse,
    CodingChallengeProblem, CodingExecuteResponse, TestResult,
    CodingFollowUpRequest, CodingFollowUpResponse,
    CodingStartRequest, TopicBreakdownResponse,
)
from ..agents.orchestrator import OrchestratorAgent
from ..agents.technical_evaluator import evaluate_answer_async
from ..agents.feedback_agent import generate_feedback_async, generate_feedback
from ..agents.coding_evaluator import (
    generate_coding_challenge_async,
    get_challenge,
    evaluate_coding_solution_async,
    evaluate_coding_solution,
    load_all_problems,
    get_all_categories,
    select_problem_ai,
    generate_follow_up_async,
)
from ..agents.code_executor import run_code_with_test_cases, run_code_with_hidden_tests, check_code_safety
from ..agents.visual_intelligence import analyze_frame
from ..agents.audio_intelligence import analyze_audio_bytes, analyze_speech
from ..models.schemas import AudioMetrics, AnalyzeAudioResponse
import base64

_coding_sessions: dict[str, dict] = {}
_sessions: dict[str, OrchestratorAgent] = {}

router = APIRouter(prefix="/interview", tags=["interview"])


# ── Helpers ──


def _save_state(agent: OrchestratorAgent) -> dict:
    return {
        "session_state": agent.session_state,
        "current_difficulty": agent.current_difficulty,
        "consecutive_struggles": agent.consecutive_struggles,
        "consecutive_successes": agent.consecutive_successes,
        "encouragement_given": agent.encouragement_given,
        "last_confidence": agent.last_confidence,
        "streak_scores": agent.streak_scores,
    }


def _load_state(agent: OrchestratorAgent, state: dict):
    agent.session_state = state.get("session_state", {})
    agent.current_difficulty = state.get("current_difficulty", "medium")
    agent.consecutive_struggles = state.get("consecutive_struggles", 0)
    agent.consecutive_successes = state.get("consecutive_successes", 0)
    agent.encouragement_given = state.get("encouragement_given", 0)
    agent.last_confidence = state.get("last_confidence", 70)
    agent.streak_scores = state.get("streak_scores", [])


async def _get_agent(session_id: str, db: AsyncSession) -> OrchestratorAgent | None:
    agent = _sessions.get(session_id)
    if agent:
        return agent

    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    db_session = result.scalar_one_or_none()
    if not db_session or not db_session.state:
        return None

    agent = OrchestratorAgent()
    _load_state(agent, db_session.state)
    _sessions[session_id] = agent
    return agent


async def _commit_agent(session_id: str, agent: OrchestratorAgent, db: AsyncSession):
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    db_session = result.scalar_one_or_none()
    if db_session:
        db_session.state = _save_state(agent)
        await db.commit()


# ── Interview Endpoints ──


@router.post("/start")
async def start_interview(
    req: InterviewStartRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    resume_data = {}
    if req.resumeId:
        result = await db.execute(select(Resume).where(Resume.id == req.resumeId, Resume.user_id == user.id))
        resume = result.scalar_one_or_none()
        if resume:
            resume_data = {
                "skills": resume.skills or [],
                "experience": resume.experience or [],
                "projects": resume.projects or [],
            }

    agent = OrchestratorAgent()
    result = agent.start_session(req.model_dump(), resume_data)
    _sessions[result["session_id"]] = agent

    q = await agent.generate_question_async()
    if not q:
        q = agent.generate_question()
    if not q:
        role = req.role or "this role"
        skills = resume_data.get("skills", [])
        skill_text = f", especially {skills[0]}" if skills else ""
        q = {
            "id": "q1", "text": f"Tell me about your background and what led you to {role}{skill_text}.",
            "type": "behavioral", "difficulty": "easy",
        }

    agent.session_state.setdefault("questions_asked", []).append(q)
    agent.session_state.setdefault("conversation_history", []).append({"role": "ai", "content": q["text"]})

    db_session = InterviewSession(
        id=result["session_id"],
        user_id=user.id,
        resume_id=req.resumeId,
        config=req.model_dump(),
        status="active",
        state=_save_state(agent),
    )
    db.add(db_session)
    await db.commit()

    return {
        "session_id": result["session_id"],
        "question": QuestionResponse(**q),
        "status": "started",
    }


@router.post("/next/{session_id}")
async def next_question(
    session_id: str,
    req: AnswerRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_agent(session_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    questions_so_far = len(agent.session_state.get("questions_asked", []))
    if questions_so_far >= agent._max_questions:
        return {"status": "complete", "message": "Interview complete"}

    q = await agent.generate_question_async(req.answer)
    if not q:
        q = agent.generate_question(req.answer)
    if not q:
        resume = agent.session_state.get("resume", {})
        skills = resume.get("skills", [])
        questions_asked = agent.session_state.get("questions_asked", [])
        last_q = questions_asked[-1].get("text", "") if questions_asked else ""
        if last_q:
            q = {"id": f"q{len(questions_asked)+1}", "text": f"Can you elaborate more on {last_q.lower()}?", "type": "follow-up", "difficulty": "medium"}
        elif skills:
            q = {"id": f"q{len(questions_asked)+1}", "text": f"Tell me more about your experience with {skills[0]}.", "type": "technical", "difficulty": "medium"}
        else:
            raise HTTPException(status_code=503, detail="Question generation unavailable (AI service unavailable)")

    agent.session_state.setdefault("questions_asked", []).append(q)
    agent.session_state.setdefault("conversation_history", []).append({"role": "ai", "content": q["text"]})

    await _commit_agent(session_id, agent, db)

    return {"question": QuestionResponse(**q)}


@router.post("/analyze/{session_id}", response_model=AnalyzeResponse)
async def analyze_answer(
    session_id: str,
    req: AnswerRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_agent(session_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = agent.session_state.get("questions_asked", [])
    qid = req.questionId or (questions[-1]["id"] if questions else "q1")
    question = next((q for q in questions if q["id"] == qid), None)

    if not question:
        raise HTTPException(status_code=404, detail=f"Question {qid} not found")

    groq_eval = await evaluate_answer_async(question["text"], req.answer or "", question["type"])
    result = agent.analyze_response(
        question_id=question["id"],
        answer=req.answer or "",
        groq_analysis=groq_eval,
    )
    if groq_eval and "correctnessScore" in groq_eval:
        result["metrics"]["technicalScore"] = groq_eval["correctnessScore"]
        result["metrics"]["depthOfKnowledge"] = groq_eval.get("depthOfKnowledge", 50)
        result["feedback"] = groq_eval.get("feedback", result.get("feedback", ""))

    agent.session_state.setdefault("conversation_history", []).append({"role": "user", "content": req.answer or ""})

    qa = InterviewQA(
        session_id=session_id,
        question_text=question["text"],
        question_type=question.get("type", "technical"),
        difficulty=question.get("difficulty", "medium"),
        answer_text=req.answer or "",
        technical_score=result["metrics"]["technicalScore"],
        communication_score=result["metrics"]["communicationScore"],
        confidence_score=result["metrics"]["confidenceScore"],
        depth_score=result["metrics"]["depthOfKnowledge"],
        feedback=result.get("feedback", ""),
    )
    db.add(qa)
    await _commit_agent(session_id, agent, db)
    await db.commit()

    return AnalyzeResponse(
        metrics=InterviewMetrics(**result["metrics"]),
        feedback=result.get("feedback", ""),
        weaknesses=result.get("weaknesses", []),
        missingConcepts=result.get("missingConcepts", []),
        strengths=result.get("strengths", []),
        drill_down_topic=result.get("drill_down_topic", ""),
        depth_analysis=result.get("depth_analysis", {}),
        adaptation=result.get("adaptation", ""),
        transition=result.get("transition", ""),
        encouragement=result.get("encouragement", ""),
    )


@router.post("/end/{session_id}")
async def end_interview(
    session_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_agent(session_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    result = agent.end_session()

    db_result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    db_session = db_result.scalar_one_or_none()
    if db_session:
        visual = db_session.visual_metrics or {}
        if visual.get("engagementScore"):
            vals = visual["engagementScore"]
            avg_vis_engagement = sum(vals) / len(vals)
            result["metrics"]["engagementScore"] = int(
                (result["metrics"].get("engagementScore", 50) + avg_vis_engagement) / 2
            )
        aggs = {}
        for k in ("eyeContactPct", "engagementScore", "attentionScore", "uprightPosturePct",
                  "stressLevel", "nervousnessIndicator", "smileConfidence"):
            vals = visual.get(k, [])
            if vals:
                aggs[k] = {"avg": round(sum(vals) / len(vals), 1), "min": min(vals), "max": max(vals), "count": len(vals)}
        db_session.status = "completed"
        db_session.metrics = result["metrics"]
        db_session.visual_metrics = aggs
        db_session.adaptation_log = result["adaptation_log"]
        db_session.ended_at = datetime.now(timezone.utc)
        db_session.state = _save_state(agent)
        await db.commit()

    _sessions.pop(session_id, None)

    return {"metrics": result["metrics"], "adaptation_log": result["adaptation_log"]}


@router.get("/feedback/{session_id}", response_model=FeedbackResponse)
async def get_feedback(
    session_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    db_result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    db_session = db_result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = _sessions.get(session_id)
    if not agent and db_session.state:
        agent = OrchestratorAgent()
        _load_state(agent, db_session.state)

    metrics = db_session.metrics or (agent.end_session()["metrics"] if agent else {})

    questions = agent.session_state.get("questions_asked", []) if agent else []
    answers = agent.session_state.get("answers_given", []) if agent else []
    adaptation_log = agent.session_state.get("adaptation_log", []) if agent else []

    groq_feedback = await generate_feedback_async(
        metrics=metrics,
        questions=questions,
        answers=answers,
        adaptation_log=adaptation_log,
    )
    if groq_feedback and all(k in groq_feedback for k in ["strengths", "improvements", "technicalGaps", "communicationTips", "behavioralInsights"]):
        groq_feedback["overallScore"] = groq_feedback.get("overallScore", int(
            (metrics.get("technicalScore", 0) + metrics.get("communicationScore", 0) +
             metrics.get("confidenceScore", 0) + metrics.get("engagementScore", 0)) / 4
        ))
        return FeedbackResponse(**groq_feedback)

    fallback = generate_feedback(metrics=metrics, questions=questions, answers=answers, adaptation_log=adaptation_log)
    return FeedbackResponse(**fallback)


# ── Session Listing ──


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == user.id)
        .order_by(InterviewSession.created_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "id": s.id,
                "status": s.status,
                "config": s.config,
                "metrics": s.metrics,
                "visual_metrics": s.visual_metrics,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "qa_count": len(s.questions) if s.questions else 0,
            }
            for s in sessions
        ]
    }


# ── Visual / Camera Intelligence ──


@router.post("/visual/analyze")
async def visual_analyze(body: dict):
    default = {
        "eyeContactPct": 0, "positiveExpressionPct": 0, "neutralExpressionPct": 0,
        "negativeExpressionPct": 0, "uprightPosturePct": 0,
        "engagementScore": 0, "stressLevel": 0, "nervousnessIndicator": 0,
        "dominantExpression": "neutral", "faceDetected": False,
        "smileConfidence": 0, "attentionScore": 0, "headYaw": 0, "headPitch": 0,
        "headRoll": 0, "headMovementVelocity": 0, "blinkDetected": False,
        "blinkRate": 0, "expressionConfidence": 0,
    }
    image_b64 = body.get("image", "")
    if not image_b64:
        return default

    try:
        image_data = base64.b64decode(image_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    r = analyze_frame(image_data)

    expression_map = {"positive": 3, "neutral": 2, "negative": 1}
    expr_val = expression_map.get(r["expression"], 2)

    return {
        "eyeContactPct": r["eye_contact_score"],
        "positiveExpressionPct": expr_val * 33 if r["expression"] == "positive" else 0,
        "neutralExpressionPct": expr_val * 33 if r["expression"] == "neutral" else 0,
        "negativeExpressionPct": expr_val * 33 if r["expression"] == "negative" else 0,
        "uprightPosturePct": r["posture_score"],
        "engagementScore": r["engagement_score"],
        "stressLevel": r["stress_indicator"],
        "nervousnessIndicator": r["nervousness_indicator"],
        "dominantExpression": r["expression"],
        "faceDetected": r["face_detected"],
        "smileConfidence": r["smile_score"],
        "attentionScore": r["attention_score"],
        "headYaw": r["head_yaw"],
        "headPitch": r["head_pitch"],
        "headRoll": r["head_roll"],
        "headMovementVelocity": r["head_movement_velocity"],
        "blinkDetected": r["blink_detected"],
        "blinkRate": r["blink_rate"],
        "expressionConfidence": r["expression_confidence"],
    }


# ── Session Detail (QA pairs for review) ──


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user.id,
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    qa_result = await db.execute(
        select(InterviewQA)
        .where(InterviewQA.session_id == session_id)
        .order_by(InterviewQA.created_at)
    )
    qas = qa_result.scalars().all()

    return {
        "id": s.id,
        "status": s.status,
        "config": s.config,
        "metrics": s.metrics,
        "visual_metrics": s.visual_metrics,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        "qa_pairs": [
            {
                "id": qa.id,
                "question_text": qa.question_text,
                "question_type": qa.question_type,
                "difficulty": qa.difficulty,
                "answer_text": qa.answer_text,
                "technical_score": qa.technical_score,
                "communication_score": qa.communication_score,
                "confidence_score": qa.confidence_score,
                "depth_score": qa.depth_score,
                "feedback": qa.feedback,
            }
            for qa in qas
        ],
    }


# ── Visual Metrics Save (attach to session) ──


@router.post("/visual-save/{session_id}")
async def save_visual_metrics(
    session_id: str,
    body: dict,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    existing = db_session.visual_metrics or {}
    for key in ("eyeContactPct", "engagementScore", "attentionScore", "uprightPosturePct",
                "stressLevel", "nervousnessIndicator", "smileConfidence"):
        val = body.get(key)
        if val is not None:
            running = existing.setdefault(key, [])
            running.append(val)
            if len(running) > 300:
                running[:50] = []

    db_session.visual_metrics = existing
    await db.commit()
    return {"ok": True}


# ── Audio Intelligence ──


@router.post("/audio/analyze", response_model=AnalyzeAudioResponse)
async def audio_analyze(body: dict):
    default_metrics = AudioMetrics(
        confidenceScore=50, communicationClarityScore=50, hesitationScore=0,
        pitchVariation=0.0, f0Mean=0.0, toneStability=50.0, energyStability=50.0,
        silenceRatio=0.0, speechRateWpm=0, duration=0.0,
    )
    audio_b64 = body.get("audio", "")
    transcript = body.get("transcript", "")

    if not audio_b64:
        result = analyze_speech(transcript)
        return AnalyzeAudioResponse(audioMetrics=AudioMetrics(
            confidenceScore=result["confidenceScore"],
            communicationClarityScore=result["communicationClarityScore"],
            hesitationScore=result["hesitationScore"],
            pitchVariation=result.get("pitchVariation", 0.0),
            f0Mean=result.get("f0Mean", 0.0),
            toneStability=result.get("toneStability", 50.0),
            energyStability=result.get("energyStability", 50.0),
            silenceRatio=result.get("silenceRatio", 0.0),
            speechRateWpm=result.get("speechRateWpm", 0),
            duration=result.get("duration", 0.0),
        ))

    try:
        audio_data = base64.b64decode(audio_b64)
    except Exception:
        return AnalyzeAudioResponse(audioMetrics=default_metrics, error="Invalid base64 audio data")

    result = analyze_audio_bytes(audio_data, transcript)

    return AnalyzeAudioResponse(audioMetrics=AudioMetrics(
        confidenceScore=result["confidenceScore"],
        communicationClarityScore=result["communicationClarityScore"],
        hesitationScore=result["hesitationScore"],
        pitchVariation=result["pitchVariation"],
        f0Mean=result.get("f0Mean", 0.0),
        toneStability=result["toneStability"],
        energyStability=result["energyStability"],
        silenceRatio=result["silenceRatio"],
        speechRateWpm=result["speechRateWpm"],
        duration=result["duration"],
    ))


# ====== CODING CHALLENGE ROUTES ======


CODING_CATEGORIES = get_all_categories()
LANGUAGES = [
    {"id": "python", "name": "Python", "extension": ".py", "template": "def solution(%s):\n    # Write your code here\n    pass"},
    {"id": "javascript", "name": "JavaScript", "extension": ".js", "template": "function solution(%s) {\n    // Write your code here\n}"},
]


@router.get("/coding/topics", response_model=TopicBreakdownResponse)
async def list_coding_topics():
    problems = load_all_problems()
    topics = []
    seen = set()
    for p in problems:
        cat = p.get("category", "general")
        diff = p.get("difficulty", "easy")
        key = f"{cat}-{diff}"
        if key not in seen:
            seen.add(key)
            topics.append({
                "category": cat,
                "difficulty": diff,
                "count": sum(1 for x in problems if x.get("category") == cat and x.get("difficulty") == diff),
            })
    return TopicBreakdownResponse(topics=topics)


@router.post("/coding/start", response_model=CodingChallengeResponse)
async def start_coding_challenge(req: CodingChallengeRequest):
    import uuid
    challenge_id = str(uuid.uuid4())[:8]

    # Try AI selection first
    challenge = await select_problem_ai(
        difficulty=req.difficulty,
        avoid_ids=req.avoid_ids,
        performance_history=req.performance_history,
        category=req.category,
    )
    if not challenge:
        challenge = get_challenge(req.difficulty, req.avoid_ids, req.category)

    _coding_sessions[challenge_id] = {
        "challenge": challenge,
        "difficulty": req.difficulty,
        "solution": None,
        "start_time": __import__("time").time(),
    }

    return CodingChallengeResponse(
        challenge_id=challenge_id,
        challenge=CodingChallengeProblem(**challenge),
        difficulty=req.difficulty,
    )


@router.post("/coding/submit/{challenge_id}", response_model=CodingEvaluationResponse)
async def submit_coding_solution(challenge_id: str, req: CodingSubmitRequest):
    session = _coding_sessions.get(challenge_id)
    if not session:
        raise HTTPException(status_code=404, detail="Coding challenge session not found")

    challenge = session["challenge"]
    problem_text = f"{challenge['title']}\n{challenge['description']}\n\nConstraints: {', '.join(challenge.get('constraints', []))}"

    groq_eval = await evaluate_coding_solution_async(problem_text, req.code)
    if groq_eval and "correctnessScore" in groq_eval:
        result = groq_eval
    else:
        result = evaluate_coding_solution(problem_text, req.code)

    # Run hidden test cases
    hidden_tests = challenge.get("hidden_test_cases", [])
    if hidden_tests and result.get("doesCompile", False):
        hidden_result = run_code_with_test_cases(req.code, hidden_tests, timeout=5)
        result["hiddenTestsPassed"] = hidden_result.get("passed", 0)
        result["hiddenTestsTotal"] = len(hidden_tests)

    # Generate follow-up questions
    follow_ups = await _generate_followups_async(challenge, req.code)
    if follow_ups:
        result["followUpQuestions"] = follow_ups

    session["solution"] = req.code
    session["last_score"] = result.get("correctnessScore", 0)
    return CodingEvaluationResponse(**result)


@router.post("/coding/execute/{challenge_id}", response_model=CodingExecuteResponse)
async def execute_coding_solution(challenge_id: str, req: CodingSubmitRequest):
    session = _coding_sessions.get(challenge_id)
    if not session:
        raise HTTPException(status_code=404, detail="Coding challenge session not found")

    challenge = session["challenge"]
    visible_tests = challenge.get("test_cases", [])
    hidden_tests = challenge.get("hidden_test_cases", [])

    if not visible_tests:
        return CodingExecuteResponse(success=False, error="No test cases available", results=[], passed=0, total=0)

    is_safe, error_msg = check_code_safety(req.code)
    if not is_safe:
        return CodingExecuteResponse(success=False, error=error_msg, results=[], passed=0, total=len(visible_tests))

    result = run_code_with_hidden_tests(req.code, visible_tests, hidden_tests, timeout=10)
    return CodingExecuteResponse(
        success=result["success"],
        error=result.get("error"),
        results=[TestResult(**r) for r in result.get("results", [])],
        passed=result.get("visiblePassed", result.get("passed", 0)),
        total=len(visible_tests),
        executionTimeMs=result.get("executionTimeMs"),
    )


async def _generate_followups_async(challenge: dict, code: str) -> list[str]:
    types = ["time_complexity", "space_complexity", "optimizations", "edge_cases"]
    questions = []
    for qtype in types[:2]:
        result = await generate_follow_up_async(challenge, code, qtype)
        if result and "question" in result:
            questions.append(result["question"])
    return questions
