import { useNavigate } from 'react-router-dom'
import { useInterviewStore } from '../store/interviewStore'
import { useRef, useState, useCallback } from 'react'
import { api } from '../lib/api'
import {
  Sparkles, Video, Code2, BarChart3, Brain,
  ChevronRight, Clock, Award, TrendingUp, Zap,
  Upload, Search, ArrowUpRight, Loader2, FileText,
  Target, Briefcase, CheckCircle2, Trash2,
} from 'lucide-react'

const features = [
  {
    icon: Brain, title: 'AI Context Analysis',
    desc: 'Resume parsing, skill scoring & role inference powered by AI.',
    color: 'text-accent-amber', bg: 'bg-accent-amber/[0.10]',
  },
  {
    icon: Zap, title: 'Adaptive Interviews',
    desc: 'Realistic mock interviews that adapt to your confidence and skill level.',
    color: 'text-accent-amber', bg: 'bg-accent-amber/[0.10]',
  },
  {
    icon: Code2, title: 'Coding Challenges',
    desc: 'Solve algorithm problems with real-time AI evaluation and feedback.',
    color: 'text-accent-amber', bg: 'bg-accent-amber/[0.10]',
  },
  {
    icon: BarChart3, title: 'Multimodal Analytics',
    desc: 'Track technical depth, communication, and engagement with live insights.',
    color: 'text-accent-amber', bg: 'bg-accent-amber/[0.10]',
  },
]

export default function Home() {
  const navigate = useNavigate()
  const resume = useInterviewStore((s) => s.resume)
  const metrics = useInterviewStore((s) => s.metrics)
  const sessionId = useInterviewStore((s) => s.sessionId)
  const { setResume, setJobRecommendations } = useInterviewStore()
  const hasResume = !!resume
  const hasSessions = !!sessionId
  const overallScore = metrics ? Math.round(
    ((metrics.technicalScore || 0) + (metrics.communicationScore || 0) +
     (metrics.confidenceScore || 0) + (metrics.engagementScore || 0)) / 4
  ) : 0
  const [uploading, setUploading] = useState(false)
  const [removing, setRemoving] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(async (f: File) => {
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', f)
      const resumeData = await api.resume.upload(formData)
      setResume(resumeData)
      if (resumeData.id) {
        const jobsResp: any = await api.jobs.recommend(resumeData.id)
        setJobRecommendations(jobsResp.jobs || jobsResp)
      }
    } catch (_) { /* ignore */ }
    finally { setUploading(false) }
  }, [setResume, setJobRecommendations])

  const handleRemoveResume = async () => {
    setRemoving(true)
    try {
      await api.resume.delete()
    } catch (_) { /* ignore */ }
    setResume(null)
    setJobRecommendations([])
    setRemoving(false)
  }

  return (
    <div className="min-h-full">
      <input ref={fileRef} type="file" accept=".pdf,.docx,.doc,.txt" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 space-y-14">

        {/* ── Hero ── */}
        <section className="text-center space-y-6 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass text-accent-amber text-xs font-medium">
            <Sparkles className="w-3 h-3" />
            AI-Powered Interview Coach
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-bold text-gradient leading-[1.05] tracking-tight">
              Ace Your Next
              <br />
              <span className="text-gradient-accent">Technical Interview</span>
            </h1>
            <p className="text-on-surface-muted max-w-2xl mx-auto text-base sm:text-lg leading-relaxed">
              Practice real interview scenarios, get instant AI feedback with analytics,
              and improve with every session.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => hasResume ? navigate('/coaching') : fileRef.current?.click()}
              disabled={uploading}
              className="btn-primary inline-flex items-center gap-2"
            >
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {uploading ? 'Uploading...' : hasResume ? 'Start Practice' : 'Upload Resume'}
            </button>
            {hasResume && (
              <button onClick={() => navigate('/analytics')} className="btn-secondary inline-flex items-center gap-2">
                View Analytics <ChevronRight className="w-3 h-3" />
              </button>
            )}
          </div>
        </section>

        {/* ── Stats ── */}
        <section className="animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <div className="grid grid-cols-3 gap-4">
            {[
              { value: hasResume ? `${overallScore}%` : '—', label: 'Overall Score', icon: Award },
              { value: hasSessions ? '1' : '0', label: 'Sessions Completed', icon: TrendingUp },
              { value: hasResume ? '3' : '0', label: 'Coding Challenges', icon: Zap },
            ].map((stat) => (
              <div key={stat.label} className="glass rounded-2xl p-5 text-center">
                <stat.icon className="w-5 h-5 text-accent-amber mx-auto mb-2" />
                <p className="text-2xl sm:text-3xl font-bold text-white">{stat.value}</p>
                <p className="text-xs text-on-surface-muted mt-1">{stat.label}</p>
              </div>
            ))}
          </div>

          {!hasResume && (
            <div className="mt-4 glass rounded-2xl p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Upload className="w-5 h-5 text-on-surface-dim shrink-0" />
                <div>
                  <p className="text-sm font-medium text-on-surface">Upload your resume to unlock full features</p>
                  <p className="text-xs text-on-surface-muted mt-0.5">AI analyzes skills, experience, and matches you to roles</p>
                </div>
              </div>
              <button onClick={() => fileRef.current?.click()} disabled={uploading} className="btn-primary text-xs shrink-0">
                {uploading ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                {uploading ? 'Uploading...' : 'Upload Resume'}
              </button>
            </div>
          )}
        </section>

        {/* ── Resume Analysis ── */}
        {hasResume && resume && (
          <section className="animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
            <div className="glass rounded-2xl p-6 space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center">
                    <FileText className="w-4 h-4 text-accent-amber" />
                  </div>
                  <div>
                    <h2 className="font-heading font-bold text-lg text-white">AI Resume Intelligence</h2>
                    <p className="text-xs text-on-surface-muted">What the AI learned from your resume</p>
                  </div>
                </div>
                <button
                  onClick={handleRemoveResume}
                  disabled={removing}
                  className="flex items-center gap-1.5 text-xs text-on-surface-dim hover:text-rose-400 transition-colors font-medium"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  {removing ? 'Removing...' : 'Remove'}
                </button>
              </div>

              {/* Candidate Summary */}
              {resume.candidateSummary && (
                <div className="bg-white/[0.03] rounded-xl px-4 py-3">
                  <p className="text-sm text-on-surface leading-relaxed">
                    {resume.candidateSummary.overallAssessment ||
                     resume.candidateSummary.experienceHighlight ||
                     `${resume.candidateSummary.title} — ${resume.candidateSummary.strengths?.slice(0, 2).join(', ')}`}
                  </p>
                </div>
              )}

              {/* Inferred Roles */}
              {resume.inferredRoles && resume.inferredRoles.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-on-surface-muted mb-2">Matched Roles</p>
                  <div className="flex flex-wrap gap-2">
                    {resume.inferredRoles.slice(0, 4).map((r) => (
                      <span key={r.role} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg glass text-xs font-medium text-on-surface">
                        {r.role}
                        <span className="text-accent-amber">{r.match}%</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Top Skills */}
              {resume.skillScores && resume.skillScores.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-on-surface-muted mb-2">Top Skills</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {resume.skillScores.slice(0, 6).map((s) => (
                      <div key={s.skill} className="bg-white/[0.03] rounded-lg px-3 py-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-on-surface truncate">{s.skill}</span>
                          <span className="text-xs text-accent-amber font-medium">{s.score}%</span>
                        </div>
                        <div className="w-full h-1 rounded-full bg-white/[0.06] overflow-hidden">
                          <div className="h-full rounded-full bg-accent-amber transition-all" style={{ width: `${s.score}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Interview Focus Areas */}
              {resume.interviewFocusAreas && resume.interviewFocusAreas.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-on-surface-muted mb-2">AI-Recommended Focus Areas</p>
                  <div className="flex flex-wrap gap-1.5">
                    {resume.interviewFocusAreas.map((f) => (
                      <span key={f.area} className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
                        f.priority === 'high' ? 'bg-accent-amber/15 text-accent-amber' :
                        f.priority === 'medium' ? 'bg-accent-amber/10 text-accent-amber-bright' :
                        'bg-white/[0.04] text-on-surface-muted'
                      }`}>
                        {f.area}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* ── Core Features ── */}
        <section className="animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
          <div className="text-center mb-8">
            <h2 className="font-heading font-bold text-xl text-white">Core Features</h2>
            <p className="text-sm text-on-surface-muted mt-1">Everything you need to ace your interviews</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map((f) => (
              <div key={f.title} className="glass rounded-2xl p-5 hover:bg-white/[0.05] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-glass-lg group">
                <div className={`w-10 h-10 rounded-xl ${f.bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200`}>
                  <f.icon className={`w-5 h-5 ${f.color}`} />
                </div>
                <h3 className="font-semibold text-sm text-white mb-1.5">{f.title}</h3>
                <p className="text-xs text-on-surface-muted leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Quick Actions ── */}
        {hasResume && (
          <section className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="font-heading font-bold text-xl text-white">Quick Actions</h2>
                <p className="text-sm text-on-surface-muted mt-1">Continue where you left off</p>
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { to: '/coaching', icon: Video, label: 'Start Interview', desc: 'Adaptive practice' },
                { to: '/coding', icon: Code2, label: 'Coding', desc: 'Algorithm challenges' },
                { to: '/analytics', icon: BarChart3, label: 'Analytics', desc: 'Track progress' },
                { to: '/roles', icon: Briefcase, label: 'Browse Roles', desc: 'Matched positions' },
              ].map((item) => (
                <button
                  key={item.label}
                  onClick={() => navigate(item.to)}
                  className="glass rounded-2xl p-4 text-left hover:bg-white/[0.05] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-glass-lg group"
                >
                  <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
                    <item.icon className="w-4 h-4 text-accent-amber" />
                  </div>
                  <p className="text-sm font-semibold text-white">{item.label}</p>
                  <p className="text-xs text-on-surface-muted mt-0.5">{item.desc}</p>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* ── Recent Activity ── */}
        <section className="animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-heading font-bold text-xl text-white">Recent Activity</h2>
              <p className="text-sm text-on-surface-muted mt-1">Your latest sessions and progress</p>
            </div>
            {hasSessions && (
              <button onClick={() => navigate('/analytics')} className="text-xs text-accent-amber hover:text-accent-amber/80 font-medium transition-colors">
                View All
              </button>
            )}
          </div>

          {hasSessions ? (
            <button
              onClick={() => navigate('/analytics')}
              className="w-full glass rounded-2xl p-4 flex items-center gap-4 text-left hover:bg-white/[0.05] transition-all duration-200 group"
            >
              <div className="w-10 h-10 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center shrink-0">
                <Video className="w-5 h-5 text-accent-amber" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">Latest Interview Session</p>
                <p className="text-xs text-on-surface-muted mt-0.5">
                  Overall Score: {overallScore}% &middot; Technical: {metrics.technicalScore}% &middot; Communication: {metrics.communicationScore}%
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="badge-success">{overallScore}%</span>
                <ArrowUpRight className="w-4 h-4 text-on-surface-dim opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </button>
          ) : (
            <div className="glass rounded-2xl p-8 text-center">
              <div className="w-12 h-12 rounded-2xl bg-white/[0.04] flex items-center justify-center mx-auto mb-3">
                <Clock className="w-6 h-6 text-on-surface-dim" />
              </div>
              <p className="text-sm text-on-surface-muted">No sessions yet</p>
              <p className="text-xs text-on-surface-dim/40 mt-1">Complete an interview or coding challenge to see your activity here</p>
            </div>
          )}
        </section>

        {/* ── Footer ── */}
        <div className="text-center text-on-surface-dim/30 text-xs pb-4">
          Powered by Groq &middot; MediaPipe &middot; FastAPI &middot; React
        </div>
      </div>
    </div>
  )
}
