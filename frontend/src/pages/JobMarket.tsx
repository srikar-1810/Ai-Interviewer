import { useState, useEffect, useCallback } from 'react'
import { useInterviewStore, DetailedJobRecommendation } from '../store/interviewStore'
import { api } from '../lib/api'
import { useGeolocation } from '../hooks/useGeolocation'
import {
  Briefcase, MapPin, Building2, ChevronRight, Search, Sliders,
  DollarSign, Globe, Filter, X, Sparkles, BarChart3,
  BookOpen, TrendingUp, Loader2, Star, Navigation,
} from 'lucide-react'

const REMOTE_LABELS: Record<string, string> = { remote: 'Remote', onsite: 'On-site', hybrid: 'Hybrid' }
const SENIORITY_LABELS: Record<string, string> = { junior: 'Junior', mid: 'Mid-Level', senior: 'Senior' }

function MatchScoreCircle({ score }: { score: number }) {
  const color = score >= 80 ? 'stroke-accent-amber' : score >= 60 ? 'stroke-accent-amber' : score >= 40 ? 'stroke-orange-400' : 'stroke-accent-rose'
  const r = 28
  const circumference = 2 * Math.PI * r
  const offset = circumference - (score / 100) * circumference
  return (
    <div className="relative w-16 h-16 shrink-0">
      <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
        <circle cx="32" cy="32" r={r} fill="none" stroke="currentColor" strokeWidth="4" strokeDasharray={circumference} strokeDashoffset={offset} className={color} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={`text-sm font-bold ${score >= 80 ? 'text-accent-amber' : score >= 60 ? 'text-accent-amber' : 'text-accent-rose'}`}>{score}</span>
      </div>
    </div>
  )
}

function BreakdownBar({ label, score }: { label: string; score: number }) {
  const width = Math.min(score * 2.5, 100)
  const color = score >= 30 ? 'bg-accent-amber' : 'bg-accent-amber'
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-on-surface-dim w-20 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${width}%` }} />
      </div>
      <span className="text-on-surface-dim w-8 text-right">{score.toFixed(0)}</span>
    </div>
  )
}

export default function JobMarket() {
  const { resume, detailedJobs, setDetailedJobs, jobFilters, setJobFilters, resetJobFilters } = useInterviewStore()
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [filterOptions, setFilterOptions] = useState<{ domains: string[]; seniorities: string[]; remoteTypes: string[] } | null>(null)
  const geo = useGeolocation()

  useEffect(() => {
    api.jobs.filters().then(setFilterOptions).catch(() => {})
  }, [])

  const loadJobs = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (geo.city) params.location = geo.city
      if (jobFilters.remote) params.remote = jobFilters.remote
      if (jobFilters.seniority) params.seniority = jobFilters.seniority
      if (jobFilters.domain) params.domain = jobFilters.domain
      if (jobFilters.salary_min) params.salary_min = String(jobFilters.salary_min)
      if (jobFilters.salary_max) params.salary_max = String(jobFilters.salary_max)
      if (jobFilters.search) params.search = jobFilters.search

      if (resume?.id) {
        const data = await api.jobs.discover(resume.id, Object.keys(params).length > 0 ? params : undefined)
        setDetailedJobs(data.jobs || [])
      } else {
        const data = await api.jobs.browse(Object.keys(params).length > 0 ? params : undefined)
        setDetailedJobs(data.jobs || [])
      }
    } catch { setDetailedJobs([]) }
    finally { setLoading(false) }
  }, [resume?.id, jobFilters, setDetailedJobs, geo.city])

  useEffect(() => { loadJobs() }, [loadJobs])

  const activeFilterCount = Object.values(jobFilters).filter(v => v !== undefined && v !== '' && v !== null).length

  return (
    <div className="space-y-12 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between animate-in">
        <div>
          <h1 className="font-heading text-2xl font-bold text-white tracking-tight">Job Market</h1>
          <p className="text-sm text-on-surface-muted flex items-center gap-1.5">
            {geo.loading ? 'Detecting your location...' : geo.city ? (
              <><Navigation className="w-3 h-3 text-accent-amber" /> {geo.city}</>
            ) : resume ? 'Personalized matches based on your resume' : 'Browse all opportunities'}
          </p>
        </div>
        <button onClick={() => setShowFilters(!showFilters)}
          className={`btn-ghost text-sm ${showFilters ? 'bg-accent-amber/10 text-accent-amber' : ''}`}>
          <Filter className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="badge-primary text-xs px-1.5 py-0">{activeFilterCount}</span>
          )}
        </button>
      </div>

      {/* Search + Quick Filters */}
      <div className="flex gap-3 animate-in" style={{ animationDelay: '0.05s' }}>
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-dim" />
          <input
            type="text"
            placeholder="Search jobs, skills, companies..."
            value={jobFilters.search || ''}
            onChange={(e) => setJobFilters({ search: e.target.value })}
            className="input pl-10"
          />
        </div>
        <select
          value={jobFilters.seniority || ''}
          onChange={(e) => setJobFilters({ seniority: e.target.value || undefined })}
          className="input w-36"
        >
          <option value="">All Levels</option>
          {filterOptions?.seniorities.map(s => (
            <option key={s} value={s}>{SENIORITY_LABELS[s] || s}</option>
          ))}
        </select>
        <select
          value={jobFilters.remote || ''}
          onChange={(e) => setJobFilters({ remote: e.target.value || undefined })}
          className="input w-36"
        >
          <option value="">All Types</option>
          {filterOptions?.remoteTypes.map(r => (
            <option key={r} value={r}>{REMOTE_LABELS[r] || r}</option>
          ))}
        </select>
      </div>

      {/* Expanded Filters */}
      {showFilters && (
        <div className="card p-5 space-y-4 animate-fade-in-up">
          <div className="flex items-center justify-between">
            <h3 className="font-heading font-semibold text-on-surface">All Filters</h3>
            <button onClick={resetJobFilters} className="text-sm text-accent-amber hover:underline">Reset</button>
          </div>
          <div className="grid md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-on-surface-dim mb-1.5">Domain</label>
              <select
                value={jobFilters.domain || ''}
                onChange={(e) => setJobFilters({ domain: e.target.value || undefined })}
                className="input"
              >
                <option value="">All Domains</option>
                {filterOptions?.domains.map(d => (
                  <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-on-surface-dim mb-1.5">Min Salary</label>
              <select
                value={jobFilters.salary_min || ''}
                onChange={(e) => setJobFilters({ salary_min: e.target.value ? Number(e.target.value) : undefined })}
                className="input"
              >
                <option value="">Any</option>
                <option value="80000">$80K+</option>
                <option value="100000">$100K+</option>
                <option value="130000">$130K+</option>
                <option value="150000">$150K+</option>
                <option value="180000">$180K+</option>
                <option value="200000">$200K+</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-accent-amber animate-spin" />
        </div>
      ) : detailedJobs.length === 0 ? (
        <div className="card p-12 text-center animate-in">
          <Briefcase className="w-12 h-12 text-on-surface-dim/20 mx-auto mb-4" />
          <p className="text-on-surface-dim">No jobs match your current filters</p>
          <button onClick={resetJobFilters} className="btn-ghost mt-3">Clear Filters</button>
        </div>
      ) : (
        <div className="space-y-4 animate-in" style={{ animationDelay: '0.1s' }}>
          <p className="text-sm text-on-surface-dim">{detailedJobs.length} jobs found</p>
          {detailedJobs.map((job) => (
            <JobCard key={job.id} job={job} resumeId={resume?.id} />
          ))}
        </div>
      )}
    </div>
  )
}

function JobCard({ job, resumeId }: { job: DetailedJobRecommendation; resumeId?: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card-hover overflow-hidden">
      <div className="flex items-start gap-4 p-5">
        <MatchScoreCircle score={job.matchScore} />

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="font-heading font-semibold text-on-surface text-lg">{job.title}</h3>
              <div className="flex items-center gap-3 text-sm text-on-surface-dim mt-0.5">
                <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5" />{job.company}</span>
                <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{job.location}</span>
                {job.remote && (
                  <span className={`flex items-center gap-1 ${job.remote === 'remote' ? 'text-accent-amber' : job.remote === 'hybrid' ? 'text-accent-amber' : ''}`}>
                    <Globe className="w-3.5 h-3.5" />{REMOTE_LABELS[job.remote] || job.remote}
                  </span>
                )}
              </div>
            </div>
            <span className={`badge shrink-0 ${job.seniority === 'senior' ? 'badge-success' : job.seniority === 'mid' ? 'badge-info' : 'badge-warning'}`}>
              {SENIORITY_LABELS[job.seniority] || job.seniority}
            </span>
          </div>

          {job.salary_min && job.salary_max && (
            <p className="text-sm text-on-surface-dim mt-2 flex items-center gap-1">
              <DollarSign className="w-3.5 h-3.5 text-accent-amber" />
              ${(job.salary_min / 1000).toFixed(0)}K - ${(job.salary_max / 1000).toFixed(0)}K <span className="text-xs">/yr</span>
            </p>
          )}

          <p className="text-sm text-on-surface-dim mt-2 line-clamp-2">{job.description}</p>

          <div className="flex flex-wrap gap-1.5 mt-3">
            {job.matchingSkills?.slice(0, 5).map((s, i) => (
              <span key={i} className="badge-success text-xs">{s}</span>
            ))}
            {job.missingSkills?.slice(0, 3).map((s, i) => (
              <span key={i} className="badge-error text-xs">{s}</span>
            ))}
            {job.requiredSkills?.filter(s => !job.matchingSkills?.includes(s) && !job.missingSkills?.includes(s)).slice(0, 2).map((s, i) => (
              <span key={i} className="badge text-xs bg-white/[0.03] text-on-surface-dim border-white/[0.06]">{s}</span>
            ))}
          </div>

          <button onClick={() => setExpanded(!expanded)}
            className="text-xs text-accent-amber hover:underline mt-2 flex items-center gap-1">
            {expanded ? 'Show less' : 'Show details'} <ChevronRight className={`w-3 h-3 transition-transform ${expanded ? 'rotate-90' : ''}`} />
          </button>

          {expanded && (
            <div className="mt-4 pt-4 border-t border-white/[0.05] space-y-4">
              {job.breakdown && (
                <div>
                  <p className="text-xs font-medium text-on-surface-dim mb-2 flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" /> Match Breakdown
                  </p>
                  <BreakdownBar label="Skills" score={job.breakdown.skillScore} />
                  <BreakdownBar label="Experience" score={job.breakdown.experienceScore} />
                  <BreakdownBar label="Title Match" score={job.breakdown.titleScore} />
                  <BreakdownBar label="Domain" score={job.breakdown.domainScore} />
                </div>
              )}

              {job.missingSkills && job.missingSkills.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-on-surface-dim mb-1 flex items-center gap-1">
                    <BookOpen className="w-3 h-3 text-accent-amber" /> Skills to Improve
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {job.missingSkills.map((s, i) => (
                      <span key={i} className="badge-warning text-xs">{s}</span>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-xs text-accent-amber flex items-start gap-1">
                <Sparkles className="w-3 h-3 shrink-0 mt-0.5" /> {job.reason}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
