import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ResumeData {
  id?: string
  skills: string[]
  skillScores?: Array<{ skill: string; score: number; category: string; evidence: string }>
  experience: Array<{ title: string; company: string; years: number }>
  experienceLevel?: { level: string; totalYears: number; reasoning: string } | null
  projects: Array<{ name: string; description: string }>
  projectImpact?: Array<{ name: string; impact: string; technologies: string[]; complexity: string; businessValue: string }>
  inferredRoles: Array<{ role: string; match: number; reason: string }>
  marketRoles?: Array<{ role: string; match: number; demand: string; growthPotential: string; reason: string }>
  missingSkills?: Array<{ skill: string; forRole: string; priority: string; reason: string }>
  resumeWeaknesses?: Array<{ area: string; severity: string; description: string; suggestion: string }>
  candidateSummary?: { title: string; strengths: string[]; experienceHighlight: string; recommendedRoles: string[]; overallAssessment: string } | null
  interviewFocusAreas?: Array<{ area: string; priority: string; reason: string; suggestedTopics: string[] }>
  probingAreas?: Array<{ area: string; trigger: string; probeDepth: string; suggestedQuestions: string[] }>
}

export interface JobRecommendation {
  id: string
  title: string
  company: string
  location: string
  matchScore: number
  reason: string
  url: string
}

export interface DetailedJobRecommendation {
  id: string
  title: string
  company: string
  location: string
  remote: string
  salary_min?: number
  salary_max?: number
  currency: string
  matchScore: number
  reason: string
  requiredSkills: string[]
  matchingSkills: string[]
  missingSkills: string[]
  domain: string
  seniority: string
  description: string
  url: string
  breakdown?: {
    skillScore: number
    experienceScore: number
    titleScore: number
    domainScore: number
  }
}

export interface JobFilters {
  remote?: string
  seniority?: string
  domain?: string
  salary_min?: number
  salary_max?: number
  search?: string
}

export interface CoachingConfig {
  focusAreas: string[]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  coachIntensity: number
  role: string
  maxQuestions?: number
}

export interface Question {
  id: string
  text: string
  type: 'technical' | 'behavioral' | 'system-design'
  difficulty: 'easy' | 'medium' | 'hard'
  topic?: string
  is_drill_down?: boolean
  phase?: string
}

export interface InterviewMetrics {
  technicalScore: number
  communicationScore: number
  confidenceScore: number
  engagementScore: number
  stressLevel: number
  depthOfKnowledge: number
}

export interface Feedback {
  strengths: string[]
  improvements: string[]
  technicalGaps: string[]
  communicationTips: string[]
  behavioralInsights: string[]
  overallScore: number
}

interface InterviewState {
  resume: ResumeData | null
  jobRecommendations: JobRecommendation[]
  detailedJobs: DetailedJobRecommendation[]
  jobFilters: JobFilters
  coachingConfig: CoachingConfig | null
  sessionId: string | null
  isInterviewActive: boolean
  currentQuestion: Question | null
  questions: Question[]
  questionIndex: number
  metrics: InterviewMetrics
  feedback: Feedback | null

  setResume: (data: ResumeData | null) => void
  setJobRecommendations: (jobs: JobRecommendation[]) => void
  setDetailedJobs: (jobs: DetailedJobRecommendation[]) => void
  setJobFilters: (filters: Partial<JobFilters>) => void
  resetJobFilters: () => void
  setCoachingConfig: (config: CoachingConfig) => void
  setSessionId: (id: string) => void
  startInterview: () => void
  endInterview: () => void
  setCurrentQuestion: (q: Question) => void
  setQuestions: (q: Question[] | ((prev: Question[]) => Question[])) => void
  nextQuestion: () => void
  updateMetrics: (m: Partial<InterviewMetrics>) => void
  setFeedback: (f: Feedback | null) => void
  reset: () => void
}

const defaultMetrics: InterviewMetrics = {
  technicalScore: 0,
  communicationScore: 0,
  confidenceScore: 0,
  engagementScore: 0,
  stressLevel: 0,
  depthOfKnowledge: 0,
}

export const useInterviewStore = create<InterviewState>()(
  persist(
    (set, get) => ({
      resume: null,
      jobRecommendations: [],
      detailedJobs: [],
      jobFilters: {},
      coachingConfig: null,
      sessionId: null,
      isInterviewActive: false,
      currentQuestion: null,
      questions: [],
      questionIndex: 0,
      metrics: { ...defaultMetrics },
      feedback: null,

  setResume: (data) => set({ resume: data }),
  setJobRecommendations: (jobs) => set({ jobRecommendations: jobs }),
  setDetailedJobs: (jobs) => set({ detailedJobs: jobs }),
  setJobFilters: (filters) => set((s) => ({ jobFilters: { ...s.jobFilters, ...filters } })),
  resetJobFilters: () => set({ jobFilters: {} }),
  setCoachingConfig: (config) => set({ coachingConfig: config }),
  setSessionId: (id) => set({ sessionId: id }),
  startInterview: () => set({
    sessionId: null,
    isInterviewActive: true,
    currentQuestion: null,
    questions: [],
    questionIndex: 0,
    metrics: { ...defaultMetrics },
    feedback: null,
  }),
  endInterview: () => set({ isInterviewActive: false }),
  setCurrentQuestion: (q) => set({ currentQuestion: q }),
  setQuestions: (q) => set((state) => ({
    questions: Array.isArray(q) ? q : q(state.questions)
  })),
  nextQuestion: () => {
    const { questionIndex, questions } = get()
    const next = questionIndex + 1
    if (next < questions.length) {
      set({ questionIndex: next, currentQuestion: questions[next] })
    }
  },
  updateMetrics: (m) => set((state) => ({ metrics: { ...state.metrics, ...m } })),
  setFeedback: (f) => set({ feedback: f }),
  reset: () =>
    set({
      resume: null,
      jobRecommendations: [],
      coachingConfig: null,
      sessionId: null,
      isInterviewActive: false,
      currentQuestion: null,
      questions: [],
      questionIndex: 0,
      metrics: { ...defaultMetrics },
      feedback: null,
    }),
    }),
    {
      name: 'interview-storage',
    }
  )
)
