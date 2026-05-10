import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Sparkles, Loader2, Eye, EyeOff, Brain, Zap, BarChart3, Shield, ArrowRight } from 'lucide-react'

const features = [
  { icon: Brain, label: 'AI Mock Interviews', desc: 'Realistic sessions with adaptive difficulty' },
  { icon: Zap, label: 'Instant Feedback', desc: 'Real-time analysis of your responses' },
  { icon: BarChart3, label: 'Performance Analytics', desc: 'Track your improvement over time' },
  { icon: Shield, label: 'Coding Challenges', desc: 'AI-evaluated algorithm problems' },
]

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const register = useAuthStore((s) => s.register)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const token = searchParams.get('token')
    const userId = searchParams.get('user_id')
    const nameParam = searchParams.get('name')
    const emailParam = searchParams.get('email')
    if (token && userId) {
      useAuthStore.setState({
        isAuthenticated: true,
        user: { id: userId, name: nameParam || 'User', email: emailParam || '' },
        token,
      })
      navigate('/')
    }
  }, [searchParams, navigate])

  const strength = password.length === 0 ? 0 : password.length < 6 ? 1 : password.length < 10 ? 2 : 3

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(name, email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.')
    } finally { setLoading(false) }
  }

  const handleOAuth = (provider: 'google' | 'github') => {
    window.location.href = `/api/auth/${provider}`
  }

  return (
    <div className="min-h-screen bg-surface flex relative overflow-hidden">

      {/* Background layers */}
      <div className="fixed inset-0 bg-dot-grid-sm pointer-events-none" />
      <div className="fixed top-0 right-0 w-[800px] h-[800px] rounded-full bg-accent-amber/[0.03] blur-[200px] pointer-events-none" />
      <div className="fixed bottom-0 left-0 w-[600px] h-[600px] rounded-full bg-accent-amber-bright/[0.02] blur-[150px] pointer-events-none" />

      {/* ── Left Panel: Brand Hero ── */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12">
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-amber to-accent-amber-bright shadow-glow-amber flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-heading font-bold text-lg text-white">InterviewAI</span>
          </div>

          <div className="space-y-8">
            <div>
              <h1 className="font-heading text-4xl font-bold text-white leading-tight tracking-tight">
                Start Your Journey to<br />
                <span className="text-gradient-accent">Land the Role</span>
              </h1>
              <p className="text-on-surface-muted mt-4 text-base leading-relaxed max-w-md">
                Join thousands of engineers who level up their interview game with AI-powered 
                practice sessions, real-time feedback, and personalized coaching.
              </p>
            </div>

            {/* Feature Grid */}
            <div className="grid grid-cols-2 gap-4 max-w-lg">
              {features.map((f) => (
                <div key={f.label} className="flex items-start gap-3 p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <div className="w-8 h-8 rounded-lg bg-accent-amber/[0.10] flex items-center justify-center shrink-0">
                    <f.icon className="w-4 h-4 text-accent-amber" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{f.label}</p>
                    <p className="text-xs text-on-surface-muted mt-0.5">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom */}
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-6 text-sm text-on-surface-dim">
            <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-accent-amber" /> 500+ Interview Sessions</span>
            <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-accent-amber" /> AI-Powered Analysis</span>
          </div>
          <p className="text-xs text-on-surface-dim/40">
            &copy; 2026 InterviewAI Coach. All rights reserved.
          </p>
        </div>

        {/* Decorative SVG */}
        <div className="absolute right-0 top-1/3 w-96 h-96 opacity-[0.04] pointer-events-none">
          <svg viewBox="0 0 200 200" fill="none" className="w-full h-full">
            <circle cx="100" cy="100" r="80" stroke="#d97706" strokeWidth="0.5" fill="none" />
            <circle cx="100" cy="100" r="60" stroke="#d97706" strokeWidth="0.5" fill="none" />
            <circle cx="100" cy="100" r="40" stroke="#d97706" strokeWidth="0.5" fill="none" />
            <path d="M100 20 L100 180 M20 100 L180 100" stroke="#d97706" strokeWidth="0.3" opacity="0.5" />
            <path d="M30 170 L170 30" stroke="#f59e0b" strokeWidth="0.3" opacity="0.3" />
            <path d="M30 30 L170 170" stroke="#f59e0b" strokeWidth="0.3" opacity="0.3" />
          </svg>
        </div>
      </div>

      {/* ── Right Panel: Auth Form ── */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 relative">
        <div className="w-full max-w-sm animate-fade-in-up relative z-10">

          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-accent-amber to-accent-amber-bright shadow-glow-amber mb-4">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="font-heading font-bold text-xl text-white tracking-tight">InterviewAI</h1>
            <p className="text-on-surface-muted text-sm mt-1">AI-Powered Interview Coaching</p>
          </div>

          {/* Card */}
          <div className="glass rounded-2xl p-7 space-y-5">
            <div className="text-center">
              <h2 className="font-heading font-bold text-xl text-white">Create account</h2>
              <p className="text-sm text-on-surface-muted mt-1">Start your AI-powered interview coaching</p>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-accent-rose/[0.10] border border-accent-rose/20">
                <p className="text-sm text-accent-rose text-center">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-sm text-on-surface-muted font-medium">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input"
                  placeholder="John Doe"
                  required
                  autoFocus
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm text-on-surface-muted font-medium">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm text-on-surface-muted font-medium">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input pr-10"
                    placeholder="Min 6 characters"
                    required
                    minLength={6}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-lg text-on-surface-dim hover:text-on-surface transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {password.length > 0 && (
                  <div className="mt-2">
                    <div className="flex gap-1.5">
                      {[1, 2, 3].map((i) => (
                        <div key={i}
                          className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                            i <= strength
                              ? strength === 1 ? 'bg-accent-rose'
                                : strength === 2 ? 'bg-accent-amber'
                                : 'bg-accent-amber-bright'
                              : 'bg-white/[0.06]'
                          }`}
                        />
                      ))}
                    </div>
                    <p className="text-xs text-on-surface-dim mt-1.5">
                      {strength === 1 ? 'Weak' : strength === 2 ? 'Medium' : 'Strong'} password
                    </p>
                  </div>
                )}
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center mt-2">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                {loading ? 'Creating account...' : 'Create Account'}
              </button>
            </form>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/[0.06]" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-3 backdrop-blur-xl text-on-surface-dim/60 bg-surface">or continue with</span>
              </div>
            </div>

            {/* OAuth */}
            <button type="button" onClick={() => handleOAuth('google')}
              className="btn-secondary text-sm justify-center w-full">
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.52a5.36 5.36 0 0 1-4.17 2.32v2.81h3.77c-.77 2.37-2.34 4.36-4.33 4.36z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.64l-3.77-2.81c-.98.66-2.23 1.09-3.51 1.09-2.7 0-4.98-1.82-5.8-4.37A5.39 5.39 0 0 1 12 5.25c0-.09 0-.17-.01-.25H4.23v2.87h3.83c-.74 1.45-1.14 3.07-1.14 4.68z" fill="#34A853"/>
                <path d="M7.19 14.11a5.82 5.82 0 0 1-.32-1.88c0-.62.11-1.22.32-1.88L3.83 8.48A9.39 9.39 0 0 1 12 5.25c1.52 0 2.9.52 3.98 1.54l3.83-2.87C17.46 2.46 14.97 1 12 1z" fill="#FBBC05"/>
                <path d="M12 5.25c1.52 0 2.9.52 3.98 1.54l3.83-2.87C17.46 2.46 14.97 1 12 1s-5.46.98-7.28 2.64l3.77 2.81c.74-1.45 1.14-3.07 1.14-4.68z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>

            <p className="text-center text-sm text-on-surface-muted">
              Already have an account?{' '}
              <Link to="/login" className="text-accent-amber hover:text-accent-amber/80 font-semibold transition-colors">Sign In</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
