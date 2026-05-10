import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useInterviewStore } from '../store/interviewStore'
import { GraduationCap, ArrowRight, Sliders, Sparkles, Target, Lightbulb, Crosshair, Loader2 } from 'lucide-react'

const focusOptions = ['Technical', 'Behavioral', 'System Design', 'Algorithms', 'Leadership']
const difficultyOptions = [
  { value: 'beginner' as const, label: 'Beginner', desc: 'Fundamental concepts' },
  { value: 'intermediate' as const, label: 'Intermediate', desc: 'Applied knowledge' },
  { value: 'advanced' as const, label: 'Advanced', desc: 'Deep expertise' },
]

export default function CoachingSetup() {
  const { setCoachingConfig, startInterview, resume } = useInterviewStore()
  const navigate = useNavigate()

  const [selectedFocus, setSelectedFocus] = useState<string[]>(['Technical', 'Behavioral'])
  const [difficulty, setDifficulty] = useState<'beginner' | 'intermediate' | 'advanced'>('intermediate')
  const [intensity, setIntensity] = useState(65)
  const [starting, setStarting] = useState(false)

  const inferredRoles = resume?.inferredRoles?.map(r => r.role) || []
  const [selectedRole, setSelectedRole] = useState(inferredRoles[0] || 'Software Engineer')

  const suggestedFocusAreas = resume?.interviewFocusAreas || []
  const missingSkills = resume?.missingSkills || []
  const expLevel = resume?.experienceLevel

  const toggleFocus = (area: string) => {
    setSelectedFocus((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
    )
  }

  const handleStart = () => {
    setStarting(true)
    const config = {
      focusAreas: selectedFocus,
      difficulty,
      coachIntensity: intensity,
      role: selectedRole,
    }
    setCoachingConfig(config)
    startInterview()
    navigate('/interview')
  }

  return (
    <div className="space-y-12 animate-fade-in-up">
      <div className="animate-in">
        <h1 className="font-heading text-2xl font-bold text-white tracking-tight">Personalize Your Coaching</h1>
        <p className="text-sm text-on-surface-muted mt-1">Configure your interview focus areas and coaching style</p>
      </div>

      {suggestedFocusAreas.length > 0 && (
        <div className="card p-5 border-accent-amber/20" style={{ animationDelay: '0.05s' }}>
          <div className="flex items-start gap-3">
            <Crosshair className="w-5 h-5 text-accent-amber shrink-0 mt-0.5" />
            <div>
              <h3 className="font-heading font-semibold text-sm text-white">AI-Recommended Focus Areas</h3>
              <p className="text-xs text-on-surface-dim mt-1">
                Based on your resume analysis, consider these preparation priorities:
              </p>
              <div className="flex flex-wrap gap-2 mt-2">
                {suggestedFocusAreas.map((f, i) => (
                  <span
                    key={i}
                    onClick={() => {
                      if (!selectedFocus.includes(f.area)) {
                        setSelectedFocus([...selectedFocus, f.area])
                      }
                    }}
                    className="badge-primary cursor-pointer hover:bg-accent-amber/20 transition-all"
                  >
                    {f.area}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card p-6 space-y-6">
          <h2 className="font-heading font-bold text-lg text-white flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-accent-amber" />
            Focus Areas
          </h2>

          <div className="flex flex-wrap gap-2">
            {focusOptions.map((area) => (
              <button
                key={area}
                onClick={() => toggleFocus(area)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                  selectedFocus.includes(area)
                    ? 'bg-accent-amber/15 border-accent-amber/30 text-accent-amber'
                    : 'bg-white/[0.03] border-white/[0.06] text-on-surface-dim hover:border-white/[0.15]'
                }`}
              >
                {area}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-sm text-on-surface-dim mb-3">Difficulty Level</label>
            <div className="grid grid-cols-3 gap-2">
              {difficultyOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setDifficulty(opt.value)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    difficulty === opt.value
                      ? 'bg-accent-amber/15 border-accent-amber/30'
                      : 'bg-white/[0.03] border-white/[0.06] hover:border-white/[0.15]'
                  }`}
                >
                  <p className="text-sm font-medium text-on-surface">{opt.label}</p>
                  <p className="text-xs text-on-surface-dim mt-0.5">{opt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {inferredRoles.length > 0 && (
            <div>
              <label className="block text-sm text-on-surface-dim mb-3">Target Role (from Resume)</label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="input"
              >
                {inferredRoles.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
                <option value="Software Engineer">Other / Software Engineer</option>
              </select>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card p-6 space-y-6">
            <h2 className="font-heading font-bold text-lg text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-accent-amber" />
              Coach Intensity
            </h2>

            <div>
              <div className="flex justify-between text-sm text-on-surface-dim mb-2">
                <span>Gentle</span>
                <span>Challenging</span>
              </div>
              <input
                type="range"
                min="0" max="100"
                value={intensity}
                onChange={(e) => setIntensity(Number(e.target.value))}
                className="w-full h-1.5 bg-white/[0.06] rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent-amber
                  [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-accent-amber/30"
              />
              <p className="text-center text-sm text-on-surface-dim mt-2">
                {intensity < 33 ? 'Supportive coaching with hints' : intensity < 66 ? 'Balanced approach' : 'Tough but fair interview'}
              </p>
            </div>

            <div className="rounded-xl p-4 bg-accent-amber/[0.03] border border-accent-amber/10">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-accent-amber shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-white">AI Coach Summary</p>
                  <p className="text-xs text-on-surface-dim mt-1 leading-relaxed">
                    Your session will focus on <strong className="text-accent-amber">{selectedFocus.join(', ')}</strong> at{' '}
                    <strong className="text-accent-amber">{difficulty}</strong> level with{' '}
                    <strong className="text-accent-amber">{intensity < 33 ? 'supportive' : intensity < 66 ? 'balanced' : 'challenging'}</strong> intensity.
                    {expLevel && <> Experience level: <strong className="text-accent-amber">{expLevel.level}</strong>.</>}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {missingSkills.length > 0 && (
            <div className="card p-5 border-accent-amber/20 bg-accent-amber/[0.02]">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-accent-amber shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-white">Preparation Tips</p>
                  <p className="text-xs text-on-surface-dim mt-1">
                    Your profile shows skill gaps in these areas. Consider reviewing them before the interview:
                  </p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {missingSkills.filter(m => m.priority === 'high').map((m, i) => (
                      <span key={i} className="badge-error text-xs">{m.skill}</span>
                    ))}
                    {missingSkills.filter(m => m.priority === 'medium').map((m, i) => (
                      <span key={i} className="badge-warning text-xs">{m.skill}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end animate-in" style={{ animationDelay: '0.15s' }}>
        <button onClick={handleStart} disabled={starting}
          className="btn-primary flex items-center gap-2 text-base px-8 py-3">
          {starting ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
          Start Interview <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
