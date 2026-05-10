import { useInterviewStore } from '../store/interviewStore'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import {
  BarChart3, Brain, MessageSquare, Target, TrendingUp,
  RefreshCw, ArrowLeft, CheckCircle2, AlertTriangle,
  Lightbulb, Sparkles, Loader2, Zap, Heart, Eye,
  Award, ChevronRight,
} from 'lucide-react'
import ScoreGauge from '../components/ScoreGauge'
import RadarGraph from '../components/RadarGraph'
import ScoreGraph from '../components/ScoreGraph'

export default function Analytics() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const { metrics, feedback: storeFeedback, setFeedback, coachingConfig } = useInterviewStore()
  const sessionId = searchParams.get('session_id')
  const initialized = useRef(false)

  useEffect(() => {
    if (!sessionId) return
    if (!initialized.current) {
      initialized.current = true
      setLoading(true)
      api.interview.feedback(sessionId)
        .then(setFeedback)
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }, [sessionId, setFeedback])

  const radarData = [
    { metric: 'Technical', score: metrics.technicalScore || 0 },
    { metric: 'Communication', score: metrics.communicationScore || 0 },
    { metric: 'Confidence', score: metrics.confidenceScore || 0 },
    { metric: 'Engagement', score: metrics.engagementScore || 0 },
    { metric: 'Depth', score: metrics.depthOfKnowledge || 0 },
    { metric: 'Calm', score: 100 - (metrics.stressLevel || 0) },
  ]

  const scoreHistory = [
    { label: 'Q1', value: Math.round(((metrics.technicalScore || 0) + (metrics.communicationScore || 0)) / 2) },
    { label: 'Q2', value: Math.round(((metrics.confidenceScore || 0) + (metrics.engagementScore || 0)) / 2) },
  ]

  if (loading) {
    return (
    <div className="min-h-full flex items-center justify-center">
      <div className="glass rounded-2xl p-8 text-center space-y-4 animate-scale-in">
        <Loader2 className="w-10 h-10 text-accent-amber animate-spin mx-auto" />
        <p className="text-on-surface-muted font-medium">Generating performance insights...</p>
      </div>
    </div>
    )
  }

  if (!sessionId && !storeFeedback) {
    return (
    <div className="min-h-full flex items-center justify-center animate-fade-in-up">
      <div className="text-center max-w-md space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-white/[0.04] flex items-center justify-center mx-auto">
          <BarChart3 className="w-8 h-8 text-on-surface-dim" />
        </div>
        <div>
          <h2 className="font-heading font-bold text-lg text-white">No Interview Data Yet</h2>
          <p className="text-sm text-on-surface-muted mt-2">Complete an interview session to see your performance analytics, scores, and personalized feedback.</p>
        </div>
        <button onClick={() => navigate('/coaching')} className="btn-primary inline-flex items-center gap-2">
          Start Your First Interview
        </button>
      </div>
    </div>
    )
  }

  const f = storeFeedback
  const overall = f?.overallScore || Math.round(
    ((metrics.technicalScore || 0) + (metrics.communicationScore || 0) +
     (metrics.confidenceScore || 0) + (metrics.engagementScore || 0)) / 4
  )

  return (
    <div className="space-y-12 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between animate-in">
        <div>
          <h1 className="font-heading text-2xl font-bold text-white tracking-tight">Performance Analytics</h1>
          <p className="text-on-surface-dim text-sm mt-0.5">AI-powered breakdown of your interview</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className="btn-ghost text-xs">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Home
          </button>
          <button onClick={() => navigate('/coaching')} className="btn-primary text-xs">
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> New Interview
          </button>
        </div>
      </div>

      {/* Overall Score */}
      <div className="card overflow-hidden animate-fade-in-up" style={{ animationDelay: '0.05s' }}>
        <div className="absolute top-0 right-0 w-72 h-72 bg-accent-amber/5 rounded-full blur-3xl pointer-events-none" />
        <div className="relative flex flex-col md:flex-row items-center gap-6 p-6">
          <ScoreGauge value={overall} label="OVERALL" size="lg" gradient="amber" sublabel="score" />
          <div className="flex-1 text-center md:text-left">
            <h2 className="font-heading font-bold text-lg text-white">Interview Performance</h2>
            <p className="text-on-surface-dim mt-1">
              {overall >= 80 ? 'Excellent — ready for real interviews!' :
               overall >= 60 ? 'Good foundation. Focus on the areas below.' :
               'Needs practice. Review the feedback and try again.'}
            </p>
            <div className="flex flex-wrap gap-2 mt-3 justify-center md:justify-start">
              <span className="badge-info">{coachingConfig?.role || 'Engineer'}</span>
              <span className="badge-primary">{(coachingConfig?.focusAreas || ['Technical']).join(', ')}</span>
              {sessionId && <span className="badge bg-white/[0.03] text-on-surface-dim border-white/[0.06]">{sessionId.slice(0, 8)}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Dimension Scores + Radar */}
      <div className="grid lg:grid-cols-3 gap-6 animate-in" style={{ animationDelay: '0.1s' }}>
        <div className="card p-6">
          <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-4">
            <Zap className="w-4 h-4 text-accent-amber" /> Dimension Scores
          </h3>
          <div className="grid grid-cols-3 gap-3">
            <ScoreGauge value={metrics.technicalScore} label="TECH" size="sm" gradient="amber" />
            <ScoreGauge value={metrics.communicationScore} label="COMM" size="sm" gradient="amber" />
            <ScoreGauge value={metrics.confidenceScore} label="CONF" size="sm" gradient="cyan" />
            <ScoreGauge value={metrics.engagementScore} label="ENGAGE" size="sm" gradient="amber" />
            <ScoreGauge value={metrics.depthOfKnowledge} label="DEPTH" size="sm" gradient="amber" />
            <ScoreGauge value={100 - (metrics.stressLevel || 0)} label="CALM" size="sm" gradient="slate" />
          </div>
        </div>

        <div className="card p-6 lg:col-span-2">
          <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-accent-amber" /> Competency Radar
          </h3>
          <RadarGraph data={radarData} height={280} />
        </div>
      </div>

      {/* Score Trend + Engagement */}
      <div className="grid lg:grid-cols-2 gap-6 animate-in" style={{ animationDelay: '0.15s' }}>
        <div className="card p-6">
          <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-accent-amber" /> Score Progression
          </h3>
          <ScoreGraph data={scoreHistory} height={180} />
        </div>

        <div className="card p-6">
          <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-4">
            <Eye className="w-4 h-4 text-accent-amber" /> Visual Engagement
          </h3>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Eye Contact', icon: Eye, value: metrics.engagementScore, color: 'from-accent-amber to-accent-amber-bright' },
              { label: 'Posture', icon: Target, value: Math.round((metrics.engagementScore + 100 - metrics.stressLevel) / 2), color: 'from-accent-amber to-accent-cyan' },
              { label: 'Attention', icon: Brain, value: Math.round((metrics.engagementScore + metrics.confidenceScore) / 2), color: 'from-accent-amber to-orange-500' },
              { label: 'Energy', icon: Heart, value: 100 - (metrics.stressLevel || 0), color: 'from-accent-rose to-rose-500' },
            ].map(item => (
              <div key={item.label} className="bg-white/[0.02] rounded-xl p-3 border border-white/[0.05]">
                <div className="flex items-center gap-2 mb-1">
                  <item.icon className="w-3 h-3 text-on-surface-dim" />
                  <span className="text-[10px] text-on-surface-dim uppercase tracking-wider">{item.label}</span>
                </div>
                <p className="text-xl font-bold text-white">{item.value}%</p>
                <div className="h-1 bg-white/[0.04] rounded-full mt-1 overflow-hidden">
                  <div className={`h-full rounded-full bg-gradient-to-r ${item.color}`}
                    style={{ width: `${item.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Feedback */}
      {f && (
        <div className="grid md:grid-cols-2 gap-6 animate-in" style={{ animationDelay: '0.2s' }}>
          <div className="space-y-4">
            <div className="card p-6 border-accent-amber/10">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-accent-amber" /> Strengths
              </h3>
              <ul className="space-y-2">
                {f.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-on-surface-muted">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-amber/50 shrink-0 mt-1.5" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-6 border-accent-amber/10">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-accent-amber" /> Improvements
              </h3>
              <ul className="space-y-2">
                {f.improvements.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-on-surface-muted">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-amber/50 shrink-0 mt-1.5" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="space-y-4">
            <div className="card p-6 border-accent-amber/10">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
                <Brain className="w-4 h-4 text-accent-amber" /> Technical Gaps
              </h3>
              <ul className="space-y-2">
                {f.technicalGaps.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-on-surface-muted">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-amber/50 shrink-0 mt-1.5" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-6 border-accent-cyan/10">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
                <Lightbulb className="w-4 h-4 text-accent-cyan" /> Coaching Insights
              </h3>
              <div className="space-y-3">
                {f.communicationTips.map((tip, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-on-surface-muted">
                    <Sparkles className="w-4 h-4 text-accent-amber shrink-0 mt-0.5" />
                    <p>{tip}</p>
                  </div>
                ))}
                {f.behavioralInsights.map((insight, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-on-surface-muted">
                    <Sparkles className="w-4 h-4 text-accent-amber shrink-0 mt-0.5" />
                    <p>{insight}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
