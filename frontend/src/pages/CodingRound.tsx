import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import {
  Code2, Loader2, Send, Sparkles, ChevronDown, ChevronUp,
  CheckCircle2, AlertTriangle, ArrowLeft, Terminal,
  Lightbulb, Play, XCircle, Clock, Award, Layers,
  BookOpen, ChevronRight, Zap, SkipForward,
} from 'lucide-react'

const TOPIC_ICONS: Record<string, string> = {
  arrays: '[]',
  strings: 'Aa',
  hashmaps: '#',
  linkedlists: '->',
  trees: '/\\',
  graphs: '○',
  dp: 'DP',
  slidingwindow: '|\u2192|',
  greedy: 'G',
  recursion: 'R',
  backtracking: 'BT',
}

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'text-accent-amber bg-accent-amber/10 border-accent-amber/20',
  medium: 'text-accent-amber bg-accent-amber/10 border-accent-amber/20',
  hard: 'text-accent-rose bg-accent-rose/10 border-accent-rose/20',
}

interface CodingProblem {
  id: string
  title: string
  category: string
  difficulty: string
  description: string
  example: string
  starter_code: string
  constraints: string[]
  test_cases: { input: string; expected: string }[]
  hidden_test_cases: { input: string; expected: string }[]
  hints: string[]
}

interface EvaluationResult {
  correctnessScore: number
  timeComplexity: string
  spaceComplexity: string
  feedback: string
  suggestions: string[]
  doesCompile: boolean
  hiddenTestsPassed: number
  hiddenTestsTotal: number
  followUpQuestions: string[]
}

interface TestResult {
  test_index: number
  status: string
  actual?: string
  expected?: string
  error?: string
}

interface ExecutionResult {
  success: boolean
  error?: string
  results: TestResult[]
  passed: number
  total: number
  executionTimeMs?: number
}

const LANGUAGES = [
  { id: 'python', name: 'Python', extension: '.py' },
  { id: 'javascript', name: 'JavaScript', extension: '.js' },
]

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy', desc: 'Fundamental' },
  { value: 'medium', label: 'Medium', desc: 'Applied' },
  { value: 'hard', label: 'Hard', desc: 'Complex' },
]

export default function CodingRound() {
  const navigate = useNavigate()
  const [challenge, setChallenge] = useState<CodingProblem | null>(null)
  const [challengeId, setChallengeId] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [difficulty, setDifficulty] = useState('medium')
  const [category, setCategory] = useState<string>('')
  const [language, setLanguage] = useState('python')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [started, setStarted] = useState(false)
  const [showHints, setShowHints] = useState(false)
  const [showTestCases, setShowTestCases] = useState(true)
  const [showFollowUp, setShowFollowUp] = useState(false)
  const [timer, setTimer] = useState(0)
  const [timerRunning, setTimerRunning] = useState(false)
  const [round, setRound] = useState(1)
  const [completedProblems, setCompletedProblems] = useState<{ title: string; score: number }[]>([])
  const [avoidIds, setAvoidIds] = useState<string[]>([])
  const [performanceHistory, setPerformanceHistory] = useState<Record<string, number>>({})
  const [topics, setTopics] = useState<{ category: string; difficulty: string; count: number }[]>([])
  const [activeTab, setActiveTab] = useState<'problem' | 'tests' | 'results'>('problem')
  const [showAllCases, setShowAllCases] = useState(false)
  const codeRef = useRef<HTMLTextAreaElement>(null)
  const startTimeRef = useRef<number>(0)
  const timerRef = useRef<number>(0)

  useEffect(() => {
    api.interview.coding.topics().then((res) => setTopics(res.topics || [])).catch(() => {})
  }, [])

  useEffect(() => {
    if (!timerRunning) return
    const interval = window.setInterval(() => {
      setTimer(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
    return () => window.clearInterval(interval)
  }, [timerRunning])

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  }

  const handleStart = async (cat?: string) => {
    setLoading(true)
    setEvaluation(null)
    setExecutionResult(null)
    setShowFollowUp(false)
    try {
      const res = await api.interview.coding.start({
        difficulty,
        category: cat || category || undefined,
        avoid_ids: avoidIds,
        performance_history: Object.keys(performanceHistory).length > 0 ? performanceHistory : undefined,
      })
      const prob: CodingProblem = res.challenge
      setChallenge(prob)
      setChallengeId(res.challenge_id)
      setCode(prob.starter_code || '')
      setStarted(true)
      setTimerRunning(true)
      setTimer(0)
      startTimeRef.current = Date.now()
      setActiveTab('problem')
    } catch (e) {
      console.error('Failed to start coding challenge:', e)
    } finally { setLoading(false) }
  }

  const handleSubmit = async () => {
    if (!challengeId || !code.trim()) return
    setSubmitting(true)
    setEvaluation(null)
    try {
      const res = await api.interview.coding.submit(challengeId, code)
      setEvaluation(res)
      setShowFollowUp(true)
      setTimerRunning(false)
      if (challenge) {
        setCompletedProblems(prev => [...prev, { title: challenge.title, score: res.correctnessScore || 0 }])
        setAvoidIds(prev => [...prev, challenge.id])
        setPerformanceHistory(prev => ({ ...prev, [challenge.id]: res.correctnessScore || 0 }))
      }
      setActiveTab('results')
    } catch (e) {
      console.error('Failed to submit solution:', e)
    } finally { setSubmitting(false) }
  }

  const handleExecute = async () => {
    if (!challengeId || !code.trim()) return
    setExecuting(true)
    setExecutionResult(null)
    try {
      const res = await api.interview.coding.execute(challengeId, code)
      setExecutionResult(res)
      setActiveTab('results')
    } catch (e) {
      console.error('Failed to execute code:', e)
      setExecutionResult({
        success: false,
        error: 'Failed to connect to execution service',
        results: [],
        passed: 0,
        total: challenge?.test_cases?.length || 0,
      })
    } finally { setExecuting(false) }
  }

  const handleNextRound = () => {
    setRound(prev => prev + 1)
    setChallenge(null)
    setChallengeId(null)
    setCode('')
    setEvaluation(null)
    setExecutionResult(null)
    setStarted(false)
    setTimerRunning(false)
    setShowFollowUp(false)
    setActiveTab('problem')
  }

  const handleBack = () => {
    if (started) {
      setStarted(false)
      setChallenge(null)
      setEvaluation(null)
      setExecutionResult(null)
      setTimerRunning(false)
    } else {
      navigate('/coaching')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const start = (e.target as HTMLTextAreaElement).selectionStart
      const end = (e.target as HTMLTextAreaElement).selectionEnd
      const newCode = code.substring(0, start) + '    ' + code.substring(end)
      setCode(newCode)
      setTimeout(() => {
        if (codeRef.current) {
          codeRef.current.selectionStart = codeRef.current.selectionEnd = start + 4
        }
      }, 0)
    }
  }

  // ── Setup Screen ──
  if (!started) {
    const uniqueCategories = [...new Set(topics.map(t => t.category))]

    return (
      <div className="space-y-8 animate-in animate-fade-in-up">
        <div>
          <h1 className="font-heading text-3xl font-semibold text-white">Coding Interview</h1>
          <p className="text-on-surface-dim mt-1">FAANG-style algorithmic coding challenges with AI evaluation</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Setup */}
          <div className="lg:col-span-2 card p-6 space-y-6">
            <h2 className="font-heading text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <Code2 className="w-5 h-5 text-accent-amber" />
              Challenge Setup
            </h2>

            <div>
              <label className="block text-sm text-on-surface-dim mb-3">Difficulty Level</label>
              <div className="grid grid-cols-3 gap-2">
                {DIFFICULTIES.map((opt) => (
                  <button key={opt.value}
                    onClick={() => setDifficulty(opt.value)}
                    className={`p-3 rounded-xl border text-center transition-all ${
                      difficulty === opt.value
                        ? 'bg-accent-amber/15 border-accent-amber/30'
                        : 'bg-white/[0.03] border-white/[0.06] hover:border-white/[0.15]'
                    }`}>
                    <p className="text-sm font-medium text-on-surface">{opt.label}</p>
                    <p className="text-xs text-on-surface-dim mt-0.5">{opt.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-on-surface-dim mb-3">Topic (optional)</label>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => setCategory('')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    !category ? 'bg-accent-amber/15 border-accent-amber/30 text-accent-amber'
                      : 'bg-white/[0.03] border-white/[0.06] text-on-surface-dim hover:border-white/[0.15]'
                  }`}>
                  Any Topic
                </button>
                {uniqueCategories.map((cat) => (
                  <button key={cat} onClick={() => setCategory(cat)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all flex items-center gap-1.5 ${
                      category === cat ? 'bg-accent-amber/15 border-accent-amber/30 text-accent-amber'
                        : 'bg-white/[0.03] border-white/[0.06] text-on-surface-dim hover:border-white/[0.15]'
                    }`}>
                    <span className="font-mono text-[10px]">{TOPIC_ICONS[cat] || '?'}</span>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    <span className="text-[10px] opacity-50">
                      ({topics.filter(t => t.category === cat && t.difficulty === difficulty).reduce((s, t) => s + t.count, 0)})
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-on-surface-dim mb-3">Language</label>
              <div className="flex gap-2">
                {LANGUAGES.map((lang) => (
                  <button key={lang.id} onClick={() => setLanguage(lang.id)}
                    className={`px-4 py-2 rounded-xl border text-sm transition-all ${
                      language === lang.id
                        ? 'bg-accent-amber/15 border-accent-amber/30 text-accent-amber'
                        : 'bg-white/[0.03] border-white/[0.06] text-on-surface-dim hover:border-white/[0.15]'
                    }`}>
                    {lang.name}
                  </button>
                ))}
              </div>
            </div>

            {completedProblems.length > 0 && (
              <div className="rounded-xl p-4 bg-accent-amber/[0.03] border border-accent-amber/10">
                <p className="text-sm font-medium text-white mb-2 flex items-center gap-2">
                  <Award className="w-4 h-4 text-accent-amber" />
                  Previous Rounds ({round - 1})
                </p>
                <div className="space-y-1">
                  {completedProblems.map((p, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-on-surface-dim">{i + 1}. {p.title}</span>
                      <span className={`font-medium ${p.score >= 70 ? 'text-accent-amber' : p.score >= 40 ? 'text-accent-amber' : 'text-accent-rose'}`}>
                        {p.score}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button onClick={() => handleStart()} disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2">
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Loading Challenge...</>
              ) : (
                <><Code2 className="w-4 h-4" /> Start Coding Challenge</>
              )}
            </button>
          </div>

          {/* Info panel */}
          <div className="card p-6 space-y-4">
            <h2 className="font-heading font-semibold text-lg text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-accent-amber" />
              Available Topics
            </h2>
            <div className="space-y-2">
              {uniqueCategories.map((cat) => (
                <div key={cat} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-on-surface flex items-center gap-2">
                      <span className="font-mono text-[10px] text-accent-amber">{TOPIC_ICONS[cat] || '?'}</span>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </p>
                    <span className="text-[10px] text-on-surface-dim">
                      {topics.filter(t => t.category === cat).reduce((s, t) => s + t.count, 0)} problems
                    </span>
                  </div>
                  <div className="flex gap-1">
                    {['easy', 'medium', 'hard'].map(d => {
                      const count = topics.filter(t => t.category === cat && t.difficulty === d).reduce((s, t) => s + t.count, 0)
                      return count > 0 ? (
                        <span key={d} className={`text-[10px] px-1.5 py-0.5 rounded ${DIFFICULTY_COLORS[d]}`}>
                          {d}: {count}
                        </span>
                      ) : null
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="rounded-xl p-4 bg-accent-amber/[0.03] border border-accent-amber/10">
              <p className="text-xs text-on-surface-dim leading-relaxed">
                Each round selects a problem based on your performance. Hidden test cases check for edge cases after submission.
                AI evaluates your solution and asks follow-up questions about complexity and optimization.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Coding Interview UI ──
  return (
    <div className="space-y-4 animate-in animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 min-w-0">
          <button onClick={handleBack} className="btn-ghost !p-2">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <h1 className="font-heading text-xl font-semibold text-white truncate">{challenge?.title}</h1>
              <span className={`badge text-[10px] ${challenge ? DIFFICULTY_COLORS[challenge.difficulty] : ''}`}>
                {challenge?.difficulty}
              </span>
              <span className="badge-primary text-[10px]">
                {challenge?.category}
              </span>
            </div>
            <p className="text-on-surface-dim text-xs capitalize">Round {round} | {language}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.06]">
            <Clock className={`w-3.5 h-3.5 ${timer > 1800 ? 'text-accent-rose' : 'text-on-surface-dim'}`} />
            <span className={`text-sm font-mono font-medium ${timer > 1800 ? 'text-accent-rose' : 'text-on-surface'}`}>
              {formatTime(timer)}
            </span>
          </div>
          {challenge?.test_cases && (
            <span className="badge-info text-[10px]">{challenge.test_cases.length} tests</span>
          )}
          {challenge?.hidden_test_cases && challenge.hidden_test_cases.length > 0 && (
            <span className="badge-warning text-[10px]">{challenge.hidden_test_cases.length} hidden</span>
          )}
        </div>
      </div>

      {/* Main grid */}
      <div className="grid lg:grid-cols-5 gap-4" style={{ minHeight: 'calc(100vh - 220px)' }}>
        {/* Left: Problem */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          {/* Problem tabs */}
          <div className="card overflow-hidden flex-1 flex flex-col">
            <div className="flex border-b border-white/[0.06]">
              {(['problem', 'tests', 'results'] as const).map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-2.5 text-xs font-medium transition-all ${
                    activeTab === tab
                      ? 'text-accent-amber border-b-2 border-accent-amber bg-accent-amber/[0.03]'
                      : 'text-on-surface-dim hover:text-on-surface'
                  }`}>
                  {tab === 'problem' ? 'Problem' : tab === 'tests' ? 'Test Cases' : 'Results'}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {activeTab === 'problem' && (
                <div className="space-y-5">
                  <div>
                    <p className="text-sm text-on-surface leading-relaxed">{challenge?.description}</p>
                  </div>

                  <div className="rounded-xl p-4 bg-white/[0.02] border border-white/[0.05]">
                    <p className="text-xs text-on-surface-dim mb-2 font-medium">Example</p>
                    <pre className="text-xs text-on-surface font-mono whitespace-pre-wrap">{challenge?.example}</pre>
                  </div>

                  {challenge?.constraints && challenge.constraints.length > 0 && (
                    <div>
                      <p className="text-xs text-on-surface-dim mb-2 font-medium">Constraints</p>
                      <ul className="space-y-1">
                        {challenge.constraints.map((c, i) => (
                          <li key={i} className="text-xs text-on-surface flex items-start gap-2">
                            <span className="w-1 h-1 rounded-full bg-accent-amber shrink-0 mt-1.5" />
                            {c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <button onClick={() => setShowHints(!showHints)}
                      className="btn-ghost text-xs flex items-center gap-1">
                      <Lightbulb className="w-3 h-3" />
                      {showHints ? 'Hide' : 'Show'} Hints
                      {showHints ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                    <button onClick={() => setShowTestCases(!showTestCases)}
                      className="btn-ghost text-xs flex items-center gap-1">
                      <BookOpen className="w-3 h-3" />
                      {showTestCases ? 'Hide' : 'Show'} Test Cases
                    </button>
                  </div>

                  {showHints && challenge?.hints && challenge.hints.length > 0 && (
                    <div className="space-y-2">
                      {challenge.hints.map((hint, i) => (
                        <div key={i} className="rounded-xl p-3 bg-accent-amber/[0.03] border border-accent-amber/20 text-xs text-on-surface">
                          <span className="text-accent-amber font-medium">Hint {i + 1}:</span> {hint}
                        </div>
                      ))}
                    </div>
                  )}

                  {showTestCases && challenge?.test_cases && (
                    <div className="space-y-2">
                      <p className="text-xs text-on-surface-dim font-medium">Sample Test Cases</p>
                      {challenge.test_cases.map((tc, i) => (
                        <div key={i} className="rounded-xl p-3 bg-white/[0.02] border border-white/[0.05] text-xs font-mono">
                          <p className="text-on-surface-dim mb-0.5">Test {i + 1}:</p>
                          <p className="text-on-surface">Input: {tc.input}</p>
                          <p className="text-accent-amber">Expected: {tc.expected}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'tests' && (
                <div className="space-y-3">
                  <p className="text-xs text-on-surface-dim font-medium">All Test Cases</p>
                  {challenge?.test_cases.map((tc, i) => (
                    <div key={i} className="rounded-xl p-3 bg-white/[0.02] border border-white/[0.05] text-xs font-mono">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-on-surface-dim">Test {i + 1} (Visible)</span>
                        <span className="text-[10px] text-accent-amber">visible</span>
                      </div>
                      <p className="text-on-surface">Input: {tc.input}</p>
                      <p className="text-accent-amber">Expected: {tc.expected}</p>
                    </div>
                  ))}
                  {challenge?.hidden_test_cases?.map((tc, i) => (
                    <div key={`h-${i}`} className="rounded-xl p-3 bg-accent-amber/[0.03] border border-accent-amber/20 text-xs font-mono">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-on-surface-dim">Test {i + 1} (Hidden)</span>
                        <span className="text-[10px] text-accent-amber">hidden</span>
                      </div>
                      {evaluation ? (
                        <>
                          <p className="text-on-surface">Input: {tc.input}</p>
                          <p className="text-accent-amber">Expected: {tc.expected}</p>
                        </>
                      ) : (
                        <p className="text-on-surface-dim italic">Hidden until submission</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'results' && (
                <div className="space-y-4">
                  {executionResult && (
                    <div className="space-y-3">
                      <div className={`rounded-xl p-4 ${executionResult.success ? 'bg-white/[0.02]' : 'bg-accent-rose/10 border border-accent-rose/20'}`}>
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-heading font-bold text-lg text-white flex items-center gap-2">
                            <Play className="w-4 h-4 text-accent-amber" />
                            Test Execution
                          </h3>
                          <div className="flex items-center gap-3">
                            {executionResult.executionTimeMs !== undefined && (
                              <span className="text-[10px] text-on-surface-dim">
                                {executionResult.executionTimeMs}ms
                              </span>
                            )}
                            <span className={`text-sm font-bold ${
                              executionResult.passed === executionResult.total ? 'text-accent-amber' : 'text-accent-amber'
                            }`}>
                              {executionResult.passed}/{executionResult.total}
                            </span>
                          </div>
                        </div>

                        {executionResult.error && (
                          <div className="mb-3 p-3 bg-accent-rose/10 rounded-xl">
                            <p className="text-xs text-accent-rose font-mono">{executionResult.error}</p>
                          </div>
                        )}

                        {executionResult.results.length > 0 && (
                          <div className="space-y-2">
                            {executionResult.results.map((tr, i) => (
                              <div key={i} className={`rounded-xl p-3 text-xs ${
                                tr.status === 'passed' ? 'bg-accent-amber/10 border border-accent-amber/20'
                                  : tr.status === 'failed' ? 'bg-accent-amber/10 border border-accent-amber/20'
                                  : 'bg-accent-rose/10 border border-accent-rose/20'
                              }`}>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-medium text-on-surface">Test {i + 1}</span>
                                  {tr.status === 'passed' ? (
                                    <span className="flex items-center gap-1 text-accent-amber"><CheckCircle2 className="w-3 h-3" /> Passed</span>
                                  ) : tr.status === 'failed' ? (
                                    <span className="flex items-center gap-1 text-accent-amber"><XCircle className="w-3 h-3" /> Failed</span>
                                  ) : (
                                    <span className="flex items-center gap-1 text-accent-rose"><AlertTriangle className="w-3 h-3" /> Error</span>
                                  )}
                                </div>
                                {tr.actual !== undefined && (
                                  <p className="text-on-surface-dim mt-1">Actual: <span className="font-mono text-on-surface">{tr.actual}</span></p>
                                )}
                                {tr.expected !== undefined && (
                                  <p className="text-on-surface-dim">Expected: <span className="font-mono text-on-surface">{tr.expected}</span></p>
                                )}
                                {tr.error && <p className="text-accent-rose mt-1 font-mono text-[10px]">{tr.error}</p>}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {evaluation && (
                    <div className="space-y-4">
                      <div className="rounded-xl p-4 bg-white/[0.02] border border-white/[0.05]">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="font-heading font-bold text-lg text-white flex items-center gap-2">
                            <Award className="w-4 h-4 text-accent-amber" />
                            AI Evaluation
                          </h3>
                          <div className={`text-2xl font-bold font-heading ${
                            evaluation.correctnessScore >= 70 ? 'text-accent-amber'
                              : evaluation.correctnessScore >= 40 ? 'text-accent-amber' : 'text-accent-rose'
                          }`}>
                            {evaluation.correctnessScore}%
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3 mb-4">
                          <div className="bg-white/[0.03] rounded-xl p-3">
                            <p className="text-[10px] text-on-surface-dim">Time Complexity</p>
                            <p className="text-sm font-mono text-on-surface">{evaluation.timeComplexity}</p>
                          </div>
                          <div className="bg-white/[0.03] rounded-xl p-3">
                            <p className="text-[10px] text-on-surface-dim">Space Complexity</p>
                            <p className="text-sm font-mono text-on-surface">{evaluation.spaceComplexity}</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 mb-4">
                          {evaluation.doesCompile ? (
                            <span className="flex items-center gap-1 text-xs text-accent-amber">
                              <CheckCircle2 className="w-3 h-3" /> Compiles
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-xs text-accent-amber">
                              <AlertTriangle className="w-3 h-3" /> May not compile
                            </span>
                          )}
                          {evaluation.hiddenTestsTotal > 0 && (
                            <span className={`flex items-center gap-1 text-xs ${
                              evaluation.hiddenTestsPassed === evaluation.hiddenTestsTotal ? 'text-accent-amber' : 'text-accent-amber'
                            }`}>
                              <Zap className="w-3 h-3" />
                              Hidden: {evaluation.hiddenTestsPassed}/{evaluation.hiddenTestsTotal}
                            </span>
                          )}
                        </div>

                        <p className="text-sm text-on-surface mb-4">{evaluation.feedback}</p>

                        {evaluation.suggestions.length > 0 && (
                          <div className="mb-4">
                            <p className="text-xs text-on-surface-dim mb-2 font-medium">Suggestions</p>
                            <ul className="space-y-1">
                              {evaluation.suggestions.map((s, i) => (
                                <li key={i} className="text-xs text-on-surface flex items-start gap-2">
                                  <Lightbulb className="w-3 h-3 text-accent-amber shrink-0 mt-0.5" />
                                  {s}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {evaluation.followUpQuestions.length > 0 && (
                          <div className="rounded-xl p-4 bg-accent-amber/[0.03] border border-accent-amber/10">
                            <p className="text-xs font-medium text-white mb-3 flex items-center gap-2">
                              <Sparkles className="w-3.5 h-3.5 text-accent-amber" />
                              Follow-up Questions
                            </p>
                            <ul className="space-y-2">
                              {evaluation.followUpQuestions.map((q, i) => (
                                <li key={i} className="text-xs text-on-surface flex items-start gap-2">
                                  <ChevronRight className="w-3 h-3 text-accent-amber shrink-0 mt-0.5" />
                                  {q}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      <button onClick={handleNextRound}
                        className="btn-primary w-full flex items-center justify-center gap-2">
                        <SkipForward className="w-4 h-4" /> Next Challenge
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Code Editor */}
        <div className="lg:col-span-3 flex flex-col gap-4">
          {/* Language selector */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-on-surface-dim">Language:</span>
              {LANGUAGES.map(lang => (
                <button key={lang.id} onClick={() => setLanguage(lang.id)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                    language === lang.id
                      ? 'bg-accent-amber/15 border-accent-amber/30 text-accent-amber'
                      : 'bg-white/[0.03] border-white/[0.06] text-on-surface-dim'
                  }`}
                >
                  {lang.name}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <button onClick={handleExecute} disabled={executing || !code.trim()}
                className="btn-secondary text-xs">
                {executing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                {executing ? 'Running...' : 'Run Tests'}
              </button>
              <button onClick={handleSubmit} disabled={submitting || !code.trim() || !!evaluation}
                className="btn-primary text-xs">
                {submitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                {submitting ? 'Evaluating...' : 'Submit'}
              </button>
            </div>
          </div>

          {/* Code textarea */}
          <div className="card overflow-hidden flex-1 flex flex-col">
            <div className="px-4 py-2 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-xs text-on-surface-dim font-mono">solution{language === 'python' ? '.py' : '.js'}</span>
              <span className="text-[10px] text-on-surface-dim">{code.split('\n').length} lines</span>
            </div>
            <div className="flex-1 relative">
              {/* Line numbers */}
              <div className="absolute left-0 top-0 bottom-0 w-10 py-4 flex flex-col items-center text-[11px] text-on-surface-dim/30 font-mono select-none pointer-events-none overflow-hidden">
                {code.split('\n').map((_, i) => (
                  <div key={i} className="leading-5 h-5">{i + 1}</div>
                ))}
              </div>
              <textarea
                ref={codeRef}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full h-full bg-transparent text-sm font-mono text-on-surface p-4 pl-12 resize-none focus:outline-none placeholder:text-on-surface-dim/20"
                placeholder="Write your solution here..."
                spellCheck={false}
                style={{ lineHeight: '1.25rem' }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
