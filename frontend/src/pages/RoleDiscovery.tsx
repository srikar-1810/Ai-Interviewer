import { useNavigate, Link } from 'react-router-dom'
import { useInterviewStore } from '../store/interviewStore'
import { api } from '../lib/api'
import {
  Briefcase, MapPin, Building2, ChevronRight, TrendingUp, Sparkles,
  ArrowRight, AlertCircle, Brain, Target, Shield, BarChart3,
  Lightbulb, Search, Zap, Star, GraduationCap, Layers,
  Crosshair, FileWarning, ExternalLink, DollarSign, Globe,
  ChevronDown, ChevronUp,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { DetailedJobRecommendation } from '../store/interviewStore'
import { useGeolocation } from '../hooks/useGeolocation'

const defaultRoles = [
  { role: 'Frontend Engineer', match: 92, reason: 'Strong React & TypeScript experience with UI portfolio' },
  { role: 'Full Stack Developer', match: 85, reason: 'Combined frontend skills with Node.js backend work' },
  { role: 'Software Engineer (General)', match: 78, reason: 'Solid CS fundamentals and problem-solving signals' },
  { role: 'DevOps Engineer', match: 65, reason: 'CI/CD and cloud deployment experience detected' },
]

const defaultJobs = [
  { id: '1', title: 'Senior Frontend Engineer', company: 'TechCorp', location: 'San Francisco, CA', matchScore: 94, reason: 'React, TypeScript, and system design requirements align with your profile', url: '#' },
  { id: '2', title: 'Full Stack Developer', company: 'StartupXYZ', location: 'Remote', matchScore: 88, reason: 'Your full-stack project experience matches their stack', url: '#' },
  { id: '3', title: 'Frontend Lead', company: 'BigCo Inc.', location: 'New York, NY', matchScore: 82, reason: 'Leadership potential detected from project ownership signals', url: '#' },
  { id: '4', title: 'UI Engineer', company: 'Designify', location: 'Austin, TX', matchScore: 76, reason: 'Strong UI portfolio with design system experience', url: '#' },
  { id: '5', title: 'Software Engineer II', company: 'GlobalTech', location: 'Seattle, WA', matchScore: 71, reason: 'Generalist role matching core CS fundamentals', url: '#' },
  { id: '6', title: 'Cloud Engineer', company: 'CloudNative Inc.', location: 'Remote', matchScore: 63, reason: 'Basic cloud exposure; upskilling recommended', url: '#' },
]

function SectionGlow({ className }: { className?: string }) {
  return (
    <div
      className={`absolute pointer-events-none rounded-full blur-3xl will-change-transform ${className || ''}`}
      style={{ transform: 'translateZ(0)' }}
    />
  )
}

function Badge({ label, variant }: { label: string; variant: 'high' | 'medium' | 'low' | 'success' | 'warning' | 'error' | 'info' | 'primary' | 'amber' }) {
  const cls: Record<string, string> = {
    high: 'bg-accent-rose/15 text-accent-rose border border-accent-rose/20',
    medium: 'bg-accent-amber/15 text-accent-amber border border-accent-amber/20',
    low: 'bg-cyan/10 text-cyan border border-cyan/20',
    success: 'bg-emerald/15 text-emerald border border-emerald/20',
    warning: 'bg-accent-amber/15 text-accent-amber border border-accent-amber/20',
    error: 'bg-accent-rose/15 text-accent-rose border border-accent-rose/20',
    info: 'bg-cyan/10 text-cyan border border-cyan/20',
    primary: 'bg-accent-amber/15 text-accent-amber border border-accent-amber/20',
    amber: 'bg-accent-amber/15 text-accent-amber border border-accent-amber/20',
  }
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-lg ${cls[variant] || cls.info}`}>{label}</span>
}

function ScoreBar({ score, label, sublabel }: { score: number; label: string; sublabel?: string }) {
  return (
    <div className="group">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-on-surface">{label}</span>
        <span className="text-xs text-on-surface-dim">{score}/99</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent-amber/70 to-accent-amber transition-all duration-500 will-change-transform"
          style={{ width: `${score}%`, transform: 'translateZ(0)' }}
        />
      </div>
      {sublabel && <p className="text-xs text-on-surface-dim/60 mt-1 leading-relaxed">{sublabel}</p>}
    </div>
  )
}

function ExpansionPanel({ title, icon: Icon, badge, defaultOpen = false, delay, children }: {
  title: string; icon: any; badge?: string; defaultOpen?: boolean; delay?: string; children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="animate-fade-in-up" style={{ animationDelay: delay || '0s' }}>
      <div className="glass rounded-2xl overflow-hidden" style={{ transform: 'translateZ(0)' }}>
        <button
          onClick={() => setOpen(!open)}
          className="w-full flex items-center justify-between p-5 hover:bg-white/[0.02] transition-colors duration-150"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center shrink-0">
              <Icon className="w-4 h-4 text-accent-amber" />
            </div>
            <div className="text-left">
              <h2 className="font-heading font-bold text-sm text-white">{title}</h2>
              {badge && <p className="text-xs text-on-surface-muted mt-0.5">{badge}</p>}
            </div>
          </div>
          <div className="text-on-surface-dim transition-transform duration-200" style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}>
            <ChevronDown className="w-4 h-4" />
          </div>
        </button>
        <div
          className="overflow-hidden transition-all duration-300 ease-out-expo"
          style={{ maxHeight: open ? '2000px' : '0px', opacity: open ? 1 : 0 }}
        >
          <div className="px-5 pb-5 pt-1">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function RoleDiscovery() {
  const navigate = useNavigate()
  const jobs = useInterviewStore((s) => s.jobRecommendations)
  const resume = useInterviewStore((s) => s.resume)
  const roles = resume?.inferredRoles || defaultRoles
  const displayJobs = jobs.length > 0 ? jobs : defaultJobs

  const summary = resume?.candidateSummary
  const skillScores = resume?.skillScores || []
  const marketRoles = resume?.marketRoles || []
  const missingSkills = resume?.missingSkills || []
  const weaknesses = resume?.resumeWeaknesses || []
  const focusAreas = resume?.interviewFocusAreas || []
  const probingAreas = resume?.probingAreas || []
  const projectImpacts = resume?.projectImpact || []
  const expLevel = resume?.experienceLevel
  const [topJobs, setTopJobs] = useState<DetailedJobRecommendation[]>([])
  const geo = useGeolocation()
  useEffect(() => {
    if (resume?.id) {
      const params: Record<string, string> = {}
      if (geo.city) params.location = geo.city
      api.jobs.discover(resume.id, params).then(d => setTopJobs((d.jobs || []).slice(0, 3))).catch(() => {})
    }
  }, [resume?.id, geo.city])

  const profileScore = skillScores.length > 0
    ? Math.round(skillScores.reduce((a, s) => a + s.score, 0) / skillScores.length)
    : 0

  const weakCount = weaknesses.filter(w => w.severity === 'high').length
  const gapCount = missingSkills.filter(m => m.priority === 'high').length

  return (
    <div className="space-y-10 animate-fade-in-up pb-12">

      {/* ── No Resume Banner ── */}
      {!resume && (
        <div className="animate-fade-in-up">
          <div className="glass rounded-2xl p-5 flex items-start gap-4 border border-accent-amber/20">
            <AlertCircle className="w-5 h-5 text-accent-amber shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-accent-amber text-sm">Personalization Off</h3>
              <p className="text-sm text-on-surface-dim mt-1">
                The data below is generic.
                <Link to="/" className="text-accent-amber hover:underline ml-1">Upload your resume</Link> for personalized insights.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Header Hero ── */}
      <div className="animate-fade-in-up relative">
        <SectionGlow className="w-[500px] h-[500px] bg-accent-amber/5 -top-40 -right-20 opacity-60" />
        <div className="glass rounded-2xl p-6 lg:p-8 relative overflow-hidden" style={{ transform: 'translateZ(0)' }}>
          <SectionGlow className="w-80 h-80 bg-accent-amber/8 -bottom-20 -left-20 opacity-40" />
          <div className="relative flex flex-col lg:flex-row items-start gap-6">
            <div className="w-14 h-14 rounded-2xl bg-accent-amber/10 border border-accent-amber/20 flex items-center justify-center shrink-0">
              <Star className="w-7 h-7 text-accent-amber" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <h1 className="font-heading text-2xl font-bold text-white tracking-tight">
                  {summary?.title || 'Profile Intelligence'}
                </h1>
                {expLevel && (
                  <span className="bg-accent-amber/15 text-accent-amber text-xs font-medium px-2.5 py-0.5 rounded-lg border border-accent-amber/20">
                    {expLevel.level}
                  </span>
                )}
              </div>
              <p className="text-sm text-on-surface-muted max-w-2xl leading-relaxed">
                {summary?.overallAssessment || 'AI-powered context analysis of your resume and career profile'}
              </p>
              {summary && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {summary.strengths.slice(0, 4).map((s, i) => (
                    <span key={i} className="inline-flex items-center gap-1 text-xs bg-emerald/10 text-emerald px-2.5 py-0.5 rounded-lg border border-emerald/20">
                      <Zap className="w-3 h-3" />{s}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {profileScore > 0 && (
              <div className="flex items-center gap-3 shrink-0 pt-2 lg:pt-0">
                <div className="text-right">
                  <p className="text-2xl font-bold text-accent-amber">{profileScore}%</p>
                  <p className="text-xs text-on-surface-dim">profile strength</p>
                </div>
                <svg className="w-14 h-14 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="2.5" />
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="#d97706" strokeWidth="2.5"
                    strokeDasharray={`${profileScore} ${100 - profileScore}`}
                    strokeLinecap="round" className="transition-all duration-700"
                    style={{ filter: 'drop-shadow(0 0 6px rgba(217,119,6,0.3))' }}
                  />
                </svg>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Skills + Career Paths ── */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <div className="glass rounded-2xl p-6 h-full relative" style={{ transform: 'translateZ(0)' }}>
            <SectionGlow className="w-60 h-60 bg-accent-amber/5 -top-10 -right-10 opacity-30" />
            <div className="relative">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center">
                  <BarChart3 className="w-4 h-4 text-accent-amber" />
                </div>
                <div>
                  <h2 className="font-heading font-bold text-sm text-white">Skill Confidence</h2>
                  <p className="text-xs text-on-surface-muted">AI-scored proficiency levels</p>
                </div>
              </div>
              {skillScores.length > 0 ? (
                <div className="space-y-4">
                  {skillScores.map((s, i) => (
                    <ScoreBar key={i} score={s.score} label={s.skill} sublabel={s.evidence} />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-on-surface-dim">No skill scores available</p>
              )}
            </div>
          </div>
        </div>

        <div className="animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
          <div className="glass rounded-2xl p-6 h-full relative" style={{ transform: 'translateZ(0)' }}>
            <SectionGlow className="w-60 h-60 bg-accent-amber/5 -bottom-10 -right-10 opacity-30" />
            <div className="relative">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-accent-amber" />
                </div>
                <div>
                  <h2 className="font-heading font-bold text-sm text-white">Inferred Career Paths</h2>
                  <p className="text-xs text-on-surface-muted">Best-fit roles based on your profile</p>
                </div>
              </div>
              <div className="space-y-2">
                {roles.map((r, i) => (
                  <div key={i}
                    className="flex items-center gap-4 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] hover:border-accent-amber/20 transition-all duration-200 group cursor-pointer"
                    style={{ transform: 'translateZ(0)' }}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-on-surface text-sm">{r.role}</p>
                      <p className="text-xs text-on-surface-dim truncate mt-0.5">{r.reason}</p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        <p className="text-sm font-semibold text-accent-amber">{r.match}%</p>
                        <p className="text-xs text-on-surface-dim">match</p>
                      </div>
                      <div className="w-16 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-accent-amber to-accent-amber-bright rounded-full transition-all duration-500"
                          style={{ width: `${r.match}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Market Roles ── */}
      {marketRoles.length > 0 && (
        <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <div className="glass rounded-2xl p-6 relative" style={{ transform: 'translateZ(0)' }}>
            <SectionGlow className="w-96 h-96 bg-accent-amber/5 -top-20 -left-20 opacity-25" />
            <div className="relative">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center">
                  <Search className="w-4 h-4 text-accent-amber" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-heading font-bold text-sm text-white">Market-Aligned Roles</h2>
                    <span className="bg-emerald/15 text-emerald text-2xs font-medium px-1.5 py-0.5 rounded border border-emerald/20">Live</span>
                  </div>
                  <p className="text-xs text-on-surface-muted">Roles with strong market demand matching your profile</p>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                {marketRoles.map((r, i) => (
                  <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] hover:border-accent-amber/20 transition-all duration-200"
                    style={{ transform: 'translateZ(0)' }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-on-surface text-sm">{r.role}</p>
                      <span className="text-sm font-semibold text-accent-amber">{r.match}%</span>
                    </div>
                    <p className="text-xs text-on-surface-dim leading-relaxed mb-3">{r.reason}</p>
                    <div className="flex flex-wrap gap-1.5">
                      <Badge label={`${r.demand} demand`} variant={r.demand === 'high' ? 'success' : r.demand === 'medium' ? 'warning' : 'error'} />
                      <Badge label={`${r.growthPotential} growth`} variant={r.growthPotential === 'high' ? 'success' : r.growthPotential === 'medium' ? 'info' : 'warning'} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Gaps & Weaknesses ── */}
      {(missingSkills.length > 0 || weaknesses.length > 0) && (
        <div className="grid lg:grid-cols-2 gap-6">
          {missingSkills.length > 0 && (
            <div className="animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
              <div className="glass rounded-2xl p-6 relative" style={{ transform: 'translateZ(0)' }}>
                <SectionGlow className="w-60 h-60 bg-accent-rose/5 -top-10 -right-10 opacity-30" />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-9 h-9 rounded-xl bg-accent-rose/[0.10] flex items-center justify-center">
                      <Target className="w-4 h-4 text-accent-rose" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="font-heading font-bold text-sm text-white">Skill Gaps</h2>
                        {gapCount > 0 && (
                          <span className="bg-accent-rose/15 text-accent-rose text-2xs font-medium px-1.5 py-0.5 rounded border border-accent-rose/20">
                            {gapCount} high
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-on-surface-muted">Missing skills for target roles</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {missingSkills.map((m, i) => (
                      <div key={i} className="flex items-start gap-3 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-all duration-200"
                        style={{ transform: 'translateZ(0)' }}
                      >
                        <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                          m.priority === 'high' ? 'bg-accent-rose' : m.priority === 'medium' ? 'bg-accent-amber' : 'bg-cyan'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <p className="text-sm font-medium text-on-surface">{m.skill}</p>
                            <Badge label={m.priority} variant={m.priority as any} />
                          </div>
                          <p className="text-xs text-on-surface-dim/70">{m.forRole} &middot; {m.reason}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {weaknesses.length > 0 && (
            <div className="animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
              <div className="glass rounded-2xl p-6 relative" style={{ transform: 'translateZ(0)' }}>
                <SectionGlow className="w-60 h-60 bg-accent-rose/5 -bottom-10 -left-10 opacity-30" />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-9 h-9 rounded-xl bg-accent-rose/[0.10] flex items-center justify-center">
                      <FileWarning className="w-4 h-4 text-accent-rose" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="font-heading font-bold text-sm text-white">Resume Weaknesses</h2>
                        {weakCount > 0 && (
                          <span className="bg-accent-rose/15 text-accent-rose text-2xs font-medium px-1.5 py-0.5 rounded border border-accent-rose/20">
                            {weakCount} critical
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-on-surface-muted">Areas that need improvement</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {weaknesses.map((w, i) => (
                      <div key={i} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-all duration-200"
                        style={{ transform: 'translateZ(0)' }}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-medium text-on-surface">{w.area}</p>
                          <Badge label={w.severity} variant={w.severity as any} />
                        </div>
                        <p className="text-xs text-on-surface-dim leading-relaxed mb-1.5">{w.description}</p>
                        <p className="text-xs text-accent-amber flex items-center gap-1">
                          <Lightbulb className="w-3 h-3 shrink-0" />{w.suggestion}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Project Impact ── */}
      {projectImpacts.length > 0 && (
        <div className="animate-fade-in-up" style={{ animationDelay: '0.35s' }}>
          <div className="glass rounded-2xl p-6 relative" style={{ transform: 'translateZ(0)' }}>
            <SectionGlow className="w-80 h-80 bg-accent-amber/5 -bottom-10 -right-10 opacity-25" />
            <div className="relative">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center">
                  <Layers className="w-4 h-4 text-accent-amber" />
                </div>
                <div>
                  <h2 className="font-heading font-bold text-sm text-white">Project Impact Analysis</h2>
                  <p className="text-xs text-on-surface-muted">AI evaluation of your project portfolio</p>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                {projectImpacts.map((p, i) => (
                  <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] hover:border-accent-amber/20 transition-all duration-200"
                    style={{ transform: 'translateZ(0)' }}
                  >
                    <p className="font-medium text-on-surface text-sm mb-1.5">{p.name}</p>
                    <p className="text-xs text-on-surface-dim leading-relaxed mb-3">{p.impact}</p>
                    <div className="flex flex-wrap gap-1 mb-3">
                      {p.technologies?.slice(0, 5).map((t, j) => (
                        <span key={j} className="text-xs bg-accent-amber/10 text-accent-amber px-2 py-0.5 rounded border border-accent-amber/10">{t}</span>
                      ))}
                    </div>
                    <div className="flex gap-1.5">
                      <Badge label={`${p.complexity} complexity`} variant={p.complexity as any} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Collapsible: Focus Areas + Probing ── */}
      {focusAreas.length > 0 && (
        <ExpansionPanel title="Interview Focus Areas" icon={Crosshair} badge="AI-prioritized topics" defaultOpen delay="0.4s">
          <div className="grid md:grid-cols-2 gap-3">
            {focusAreas.map((f, i) => (
              <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-all duration-200"
                style={{ transform: 'translateZ(0)' }}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <p className="font-medium text-on-surface text-sm">{f.area}</p>
                  <Badge label={f.priority} variant={f.priority as any} />
                </div>
                <p className="text-xs text-on-surface-dim leading-relaxed mb-3">{f.reason}</p>
                <div className="flex flex-wrap gap-1">
                  {f.suggestedTopics?.map((t, j) => (
                    <span key={j} className="text-xs bg-accent-amber/10 text-accent-amber px-2 py-0.5 rounded border border-accent-amber/10">{t}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ExpansionPanel>
      )}

      {probingAreas.length > 0 && (
        <ExpansionPanel title="Dynamic Probing Areas" icon={Brain} badge="Resume gaps the AI will explore" delay="0.45s">
          <div className="space-y-3">
            {probingAreas.map((p, i) => (
              <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-all duration-200"
                style={{ transform: 'translateZ(0)' }}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <p className="font-medium text-on-surface text-sm">{p.area}</p>
                  <Badge label={`${p.probeDepth} probe`} variant={p.probeDepth as any} />
                </div>
                <p className="text-xs text-on-surface-dim/70 mb-3">Trigger: {p.trigger}</p>
                <div className="space-y-1.5">
                  {p.suggestedQuestions?.slice(0, 3).map((q, j) => (
                    <p key={j} className="text-xs text-accent-amber/80 flex items-start gap-2">
                      <span className="text-on-surface-dim shrink-0 font-medium">Q{j + 1}:</span>
                      <span>{q}</span>
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ExpansionPanel>
      )}

      {/* ── Recommended Jobs ── */}
      <div className="animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
        <div className="glass rounded-2xl p-6 relative" style={{ transform: 'translateZ(0)' }}>
          <SectionGlow className="w-80 h-80 bg-accent-amber/5 -top-10 -right-10 opacity-20" />
          <div className="relative">
              <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-accent-amber/[0.10] flex items-center justify-center">
                  <Briefcase className="w-4 h-4 text-accent-amber" />
                </div>
                <div>
                  <h2 className="font-heading font-bold text-sm text-white">Recommended Jobs</h2>
                  <p className="text-xs text-on-surface-muted">
                    {geo.loading ? 'Detecting your location...' : geo.city ? `Near ${geo.city}` : 'Matched to your skill profile'}
                  </p>
                </div>
              </div>
              <Link to="/jobs" className="text-xs text-accent-amber hover:text-accent-amber/80 font-medium transition-colors flex items-center gap-1 shrink-0">
                Full Market <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
            {topJobs.length > 0 ? (
              <div className="space-y-3">
                {topJobs.map((job) => <JobListItem key={job.id} job={job} />)}
              </div>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {displayJobs.slice(0, 4).map((job) => (
                  <div key={job.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] hover:-translate-y-0.5 hover:shadow-glass transition-all duration-200"
                    style={{ transform: 'translateZ(0)' }}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="min-w-0">
                        <h3 className="font-heading font-semibold text-on-surface text-sm">{job.title}</h3>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-on-surface-dim mt-1">
                          <span className="flex items-center gap-1"><Building2 className="w-3 h-3" />{job.company}</span>
                          <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>
                        </div>
                      </div>
                      <div className="text-right shrink-0 ml-3">
                        <p className="text-lg font-bold text-accent-amber">{job.matchScore}%</p>
                        <p className="text-2xs text-on-surface-dim">match</p>
                      </div>
                    </div>
                    <p className="text-xs text-on-surface-dim leading-relaxed mb-3">{job.reason}</p>
                    <div className="flex items-center justify-between">
                      <Badge label={
                        job.matchScore >= 80 ? 'Strong Fit' : job.matchScore >= 70 ? 'Good Fit' : 'Potential'
                      } variant={job.matchScore >= 80 ? 'success' : job.matchScore >= 70 ? 'info' : 'warning'} />
                      <Link to="/jobs" className="text-xs text-accent-amber hover:text-accent-amber/80 font-medium transition-colors flex items-center gap-1">
                        View All <ChevronRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── CTA ── */}
      <div className="flex justify-end pt-2 animate-fade-in-up" style={{ animationDelay: '0.55s' }}>
        <button onClick={() => navigate('/coaching')} className="btn-primary flex items-center gap-2">
          Continue to Coaching Setup <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

function JobListItem({ job }: { job: DetailedJobRecommendation }) {
  return (
    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] hover:-translate-y-0.5 hover:shadow-glass transition-all duration-200"
      style={{ transform: 'translateZ(0)' }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0">
          <h3 className="font-heading font-semibold text-on-surface text-sm">{job.title}</h3>
          <div className="flex flex-wrap items-center gap-2 text-xs text-on-surface-dim mt-1">
            <span className="flex items-center gap-1"><Building2 className="w-3 h-3" />{job.company}</span>
            <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>
            {job.remote && (
              <span className="flex items-center gap-1"><Globe className="w-3 h-3" />{job.remote}</span>
            )}
          </div>
        </div>
        <div className="text-right shrink-0 ml-3">
          <p className="text-lg font-bold text-accent-amber">{job.matchScore}%</p>
          <p className="text-2xs text-on-surface-dim">match</p>
        </div>
      </div>
      {job.salary_min && job.salary_max && (
        <p className="text-xs text-accent-amber flex items-center gap-1 mb-2">
          <DollarSign className="w-3 h-3" />${(job.salary_min / 1000).toFixed(0)}K - ${(job.salary_max / 1000).toFixed(0)}K /yr
        </p>
      )}
      <p className="text-xs text-on-surface-dim leading-relaxed mb-3">{job.reason}</p>
      <div className="flex flex-wrap gap-1 mb-3">
        {job.matchingSkills?.slice(0, 4).map((s, i) => (
          <span key={i} className="text-xs bg-emerald/10 text-emerald px-2 py-0.5 rounded border border-emerald/20">{s}</span>
        ))}
        {job.missingSkills?.slice(0, 2).map((s, i) => (
          <span key={i} className="text-xs bg-accent-rose/10 text-accent-rose px-2 py-0.5 rounded border border-accent-rose/20">{s}</span>
        ))}
      </div>
      <div className="flex items-center justify-between">
        <Badge label={
          job.matchScore >= 80 ? 'Strong Fit' : job.matchScore >= 60 ? 'Good Fit' : 'Potential'
        } variant={job.matchScore >= 80 ? 'success' : job.matchScore >= 60 ? 'info' : 'warning'} />
        <Link to="/jobs" className="text-xs text-accent-amber hover:text-accent-amber/80 font-medium transition-colors flex items-center gap-1">
          View Details <ChevronRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  )
}
