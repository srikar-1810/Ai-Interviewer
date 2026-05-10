from pydantic import BaseModel
from typing import Optional

# Auth
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    user: dict
    token: str

# Resume - Base
class ResumeExperience(BaseModel):
    title: str
    company: str
    years: int

class ResumeProject(BaseModel):
    name: str
    description: str

class InferredRole(BaseModel):
    role: str
    match: int
    reason: str

# --- Advanced Context Understanding Schemas ---

class SkillConfidence(BaseModel):
    skill: str
    score: int
    category: str
    evidence: str

class ExperienceLevelInfo(BaseModel):
    level: str
    totalYears: int
    reasoning: str

class MissingSkill(BaseModel):
    skill: str
    forRole: str
    priority: str
    reason: str

class ProjectImpact(BaseModel):
    name: str
    impact: str
    technologies: list[str]
    complexity: str
    businessValue: str

class ResumeWeakness(BaseModel):
    area: str
    severity: str
    description: str
    suggestion: str

class MarketRole(BaseModel):
    role: str
    match: int
    demand: str
    growthPotential: str
    reason: str

class InterviewFocusArea(BaseModel):
    area: str
    priority: str
    reason: str
    suggestedTopics: list[str]

class CandidateSummary(BaseModel):
    title: str
    strengths: list[str]
    experienceHighlight: str
    recommendedRoles: list[str]
    overallAssessment: str

class ProbingArea(BaseModel):
    area: str
    trigger: str
    probeDepth: str
    suggestedQuestions: list[str]

class ResumeResponse(BaseModel):
    id: str
    skills: list[str]
    skillScores: list[SkillConfidence] = []
    experience: list[ResumeExperience]
    experienceLevel: Optional[ExperienceLevelInfo] = None
    projects: list[ResumeProject]
    projectImpact: list[ProjectImpact] = []
    inferredRoles: list[InferredRole]
    marketRoles: list[MarketRole] = []
    missingSkills: list[MissingSkill] = []
    resumeWeaknesses: list[ResumeWeakness] = []
    candidateSummary: Optional[CandidateSummary] = None
    interviewFocusAreas: list[InterviewFocusArea] = []
    probingAreas: list[ProbingArea] = []

class ContextAnalysisResponse(BaseModel):
    resumeId: str
    skillScores: list[SkillConfidence] = []
    experienceLevel: Optional[ExperienceLevelInfo] = None
    missingSkills: list[MissingSkill] = []
    projectImpact: list[ProjectImpact] = []
    resumeWeaknesses: list[ResumeWeakness] = []
    marketRoles: list[MarketRole] = []
    candidateSummary: Optional[CandidateSummary] = None
    interviewFocusAreas: list[InterviewFocusArea] = []
    probingAreas: list[ProbingArea] = []

# Jobs
class JobRecommendation(BaseModel):
    id: str
    title: str
    company: str
    location: str
    matchScore: int
    reason: str
    url: str

class JobRecommendationResponse(BaseModel):
    jobs: list[JobRecommendation]

# Enhanced Job Engine Schemas
class MatchBreakdown(BaseModel):
    skillScore: float
    experienceScore: float
    titleScore: float
    domainScore: float

class DetailedJobRecommendation(BaseModel):
    id: str
    title: str
    company: str
    location: str
    remote: str = "onsite"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "USD"
    matchScore: int
    reason: str
    requiredSkills: list[str] = []
    matchingSkills: list[str] = []
    missingSkills: list[str] = []
    domain: str = "general"
    seniority: str = "mid"
    description: str = ""
    url: str = ""
    breakdown: Optional[MatchBreakdown] = None

class DetailedJobResponse(BaseModel):
    jobs: list[DetailedJobRecommendation]
    total: int
    filters: dict = {}

class JobFilterParams(BaseModel):
    remote: Optional[str] = None
    seniority: Optional[str] = None
    domain: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    search: Optional[str] = None
    resume_id: Optional[str] = None

class SemanticMatchRequest(BaseModel):
    skills: list[str]
    job_id: str

class SkillGapAnalysis(BaseModel):
    skill: str
    forJob: str
    importance: str
    learningResource: str

class SalaryEstimate(BaseModel):
    role: str
    seniority: str
    location: str
    remote: str
    salary_min: int
    salary_max: int
    currency: str = "USD"

# Interview
class InterviewStartRequest(BaseModel):
    focusAreas: list[str]
    difficulty: str
    role: str
    resumeId: Optional[str] = None

class AnswerRequest(BaseModel):
    answer: Optional[str] = ""
    questionId: Optional[str] = ""
    audioData: Optional[str] = ""

class QuestionResponse(BaseModel):
    id: str
    text: str
    type: str
    difficulty: str

class InterviewMetrics(BaseModel):
    technicalScore: int
    communicationScore: int
    confidenceScore: int
    engagementScore: int
    stressLevel: int
    depthOfKnowledge: int

class AnalyzeResponse(BaseModel):
    metrics: InterviewMetrics
    feedback: str
    weaknesses: list[str] = []
    missingConcepts: list[str] = []
    strengths: list[str] = []
    drill_down_topic: str = ""
    depth_analysis: dict = {}
    adaptation: str = ""
    transition: str = ""
    encouragement: str = ""

class AudioMetrics(BaseModel):
    confidenceScore: int
    communicationClarityScore: int
    hesitationScore: int
    pitchVariation: float
    f0Mean: float
    toneStability: float
    energyStability: float
    silenceRatio: float
    speechRateWpm: int
    duration: float


class AnalyzeAudioResponse(BaseModel):
    audioMetrics: AudioMetrics
    error: str = ""


class FeedbackResponse(BaseModel):
    strengths: list[str]
    improvements: list[str]
    technicalGaps: list[str]
    communicationTips: list[str]
    behavioralInsights: list[str]
    overallScore: int

# Coding Challenge
class CodingChallengeRequest(BaseModel):
    difficulty: str = "medium"
    category: Optional[str] = None
    avoid_ids: list[str] = []
    performance_history: Optional[dict] = None

class CodingChallengeProblem(BaseModel):
    id: Optional[str] = None
    title: str
    category: str = "general"
    difficulty: str = "easy"
    description: str
    example: str
    starter_code: str
    constraints: list[str]
    time_complexity_expected: str = ""
    space_complexity_expected: str = ""
    test_cases: list[dict]
    hidden_test_cases: list[dict] = []
    hints: list[str] = []

class CodingChallengeResponse(BaseModel):
    challenge_id: str
    challenge: CodingChallengeProblem
    difficulty: str

class CodingSubmitRequest(BaseModel):
    code: str

class CodingEvaluationResponse(BaseModel):
    correctnessScore: int
    timeComplexity: str = "N/A"
    spaceComplexity: str = "N/A"
    feedback: str
    suggestions: list[str] = []
    doesCompile: bool = False
    hiddenTestsPassed: int = 0
    hiddenTestsTotal: int = 0
    followUpQuestions: list[str] = []

class TestResult(BaseModel):
    test_index: int
    status: str
    actual: Optional[str] = None
    expected: Optional[str] = None
    error: Optional[str] = None

class CodingExecuteResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    results: list[TestResult] = []
    passed: int = 0
    total: int = 0
    executionTimeMs: Optional[int] = None

class CodingFollowUpRequest(BaseModel):
    challenge_id: str
    code: str
    questionType: str = "time_complexity"

class CodingFollowUpResponse(BaseModel):
    question: str
    expectedAnswer: str
    hint: str = ""

class LanguageOption(BaseModel):
    id: str
    name: str
    extension: str
    template: str

class CodingStartRequest(BaseModel):
    difficulty: str = "medium"
    topic: Optional[str] = None
    language: str = "python"
    avoid_ids: list[str] = []

class CodingProblemInfo(BaseModel):
    id: str
    title: str
    category: str
    difficulty: str
    description: str
    example: str
    starter_code: str
    constraints: list[str]
    time_complexity_expected: str = ""
    space_complexity_expected: str = ""
    test_cases: list[dict] = []
    hidden_test_cases: list[dict] = []
    hints: list[str] = []

class TopicBreakdownResponse(BaseModel):
    topics: list[dict]
