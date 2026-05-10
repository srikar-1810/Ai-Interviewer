interface QuestionData {
  id: string
  text: string
  type: 'technical' | 'behavioral' | 'system-design'
  difficulty: 'easy' | 'medium' | 'hard'
}

interface StartResponse {
  session_id: string
  question: QuestionData
  status: string
}

interface NextQuestionResponse {
  question: QuestionData
}

interface Metrics {
  technicalScore: number
  communicationScore: number
  confidenceScore: number
  engagementScore: number
  stressLevel: number
  depthOfKnowledge: number
}

interface AnalyzeResponse {
  metrics: Metrics
  feedback: string
}

interface EndResponse {
  metrics: Metrics
  adaptation_log: string[]
}

interface FeedbackResponse {
  strengths: string[]
  improvements: string[]
  technicalGaps: string[]
  communicationTips: string[]
  behavioralInsights: string[]
  overallScore: number
}

const BASE = '/api'

function getToken(): string | null {
  try {
    const raw = localStorage.getItem('auth-storage')
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.state?.token ?? null
  } catch { return null }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { headers, ...options })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    if (res.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  auth: {
    register: (body: { name: string; email: string; password: string }) =>
      request<{ user: { id: string; name: string; email: string }; token: string }>('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
    login: (body: { email: string; password: string }) =>
      request<{ user: { id: string; name: string; email: string }; token: string }>('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  },
  resume: {
    upload: async (formData: FormData) => {
      const token = getToken()
      const headers: Record<string, string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch(`${BASE}/resume/upload`, { method: 'POST', body: formData, headers })
      if (!res.ok) {
        if (res.status === 401) { localStorage.removeItem('auth-storage'); window.location.href = '/login' }
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Upload failed')
      }
      return res.json()
    },
    analyze: (resumeId: string) => request(`/resume/analyze/${resumeId}`),
    delete: async () => {
      const token = getToken()
      const headers: Record<string, string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      await fetch(`${BASE}/resume`, { method: 'DELETE', headers })
    },
  },
  jobs: {
    recommend: (resumeId: string) => request(`/jobs/recommend/${resumeId}`),
    discover: (resumeId: string, params?: Record<string, string>) => {
      const qs = params ? '?' + new URLSearchParams(params).toString() : ''
      return request<any>(`/jobs/discover/${resumeId}${qs}`)
    },
    browse: (params?: Record<string, string>) => {
      const qs = params ? '?' + new URLSearchParams(params).toString() : ''
      return request<any>(`/jobs/browse${qs}`)
    },
    detail: (jobId: string, resumeId?: string) => {
      const qs = resumeId ? `?resume_id=${resumeId}` : ''
      return request<any>(`/jobs/detail/${jobId}${qs}`)
    },
    semanticMatch: (body: { skills: string[]; experience: any[]; job_id: string }) =>
      request<any>('/jobs/semantic-match', { method: 'POST', body: JSON.stringify(body) }),
    filters: () => request<any>('/jobs/filters'),
  },
  interview: {
    start: (config: { focusAreas: string[]; difficulty: string; role: string; resumeId?: string }) =>
      request<StartResponse>('/interview/start', { method: 'POST', body: JSON.stringify(config) }),
    nextQuestion: (sessionId: string, answer?: string) =>
      request<NextQuestionResponse>(`/interview/next/${sessionId}`, { method: 'POST', body: JSON.stringify({ answer }) }),
    analyzeResponse: (sessionId: string, answer: string, questionId: string, audioData?: string) =>
      request<AnalyzeResponse>(`/interview/analyze/${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({ answer, questionId, audioData }),
      }),
    end: (sessionId: string) => request<EndResponse>(`/interview/end/${sessionId}`, { method: 'POST' }),
    feedback: (sessionId: string) => request<FeedbackResponse>(`/interview/feedback/${sessionId}`),
    listSessions: () => request<{ sessions: any[] }>('/interview/sessions'),
    getSessionDetail: (sessionId: string) => request<any>(`/interview/sessions/${sessionId}`),
    saveVisualMetrics: (sessionId: string, metrics: Record<string, number>) =>
      request<{ ok: boolean }>(`/interview/visual-save/${sessionId}`, { method: 'POST', body: JSON.stringify(metrics) }),
    visual: {
      analyze: (body: { image: string }) =>
        request<any>('/interview/visual/analyze', { method: 'POST', body: JSON.stringify(body) }),
    },
    audio: {
      analyze: (body: { audio: string; transcript?: string }) =>
        request<any>('/interview/audio/analyze', { method: 'POST', body: JSON.stringify(body) }),
    },
    coding: {
      start: (params: { difficulty: string; category?: string; avoid_ids?: string[]; performance_history?: any }) =>
        request<any>('/interview/coding/start', { method: 'POST', body: JSON.stringify(params) }),
      submit: (challengeId: string, code: string) =>
        request<any>(`/interview/coding/submit/${challengeId}`, { method: 'POST', body: JSON.stringify({ code }) }),
      execute: (challengeId: string, code: string) =>
        request<any>(`/interview/coding/execute/${challengeId}`, { method: 'POST', body: JSON.stringify({ code }) }),
      topics: () =>
        request<any>('/interview/coding/topics'),
    },
  },
}
