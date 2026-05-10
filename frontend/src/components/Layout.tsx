import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useInterviewStore } from '../store/interviewStore'
import {
  LayoutDashboard, Briefcase, GraduationCap, Video,
  BarChart3, Code2, LogOut, Sparkles, Search,
  Menu, X, ChevronDown,
} from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Home' },
  { to: '/roles', icon: Briefcase, label: 'Roles' },
  { to: '/jobs', icon: Search, label: 'Jobs' },
  { to: '/coaching', icon: GraduationCap, label: 'Coaching' },
  { to: '/interview', icon: Video, label: 'Interview' },
  { to: '/coding', icon: Code2, label: 'Coding' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const reset = useInterviewStore((s) => s.reset)
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const isHome = location.pathname === '/'

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleLogout = () => { reset(); logout(); navigate('/login') }

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 flex items-center justify-between h-12 px-4 lg:px-6 border-b border-white/[0.06] bg-surface/80 backdrop-blur-xl">
        {/* Left: Logo + Desktop Nav */}
        <div className="flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-2.5 shrink-0">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-accent-amber to-accent-amber-bright flex items-center justify-center shadow-glow-amber">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="font-heading font-bold text-sm text-white hidden sm:inline">InterviewAI</span>
          </NavLink>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-accent-amber/[0.08] text-accent-amber'
                      : 'text-on-surface-muted hover:text-on-surface hover:bg-white/[0.03]'
                  }`
                }
              >
                <item.icon className="w-3.5 h-3.5" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Right: User Menu */}
        <div className="flex items-center gap-2">
          {/* Mobile nav toggle */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-1.5 rounded-lg text-on-surface-dim hover:text-on-surface hover:bg-white/[0.04] transition-colors"
          >
            {menuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-white/[0.04] transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-accent-amber to-accent-amber-bright flex items-center justify-center text-white text-[10px] font-bold">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="text-xs text-on-surface-muted hidden sm:inline">{user?.name || 'User'}</span>
              <ChevronDown className="w-3 h-3 text-on-surface-dim hidden sm:block" />
            </button>

            {menuOpen && (
              <div className="absolute right-0 top-full mt-1 w-48 py-1 bg-surface-raised border border-white/[0.08] rounded-xl shadow-glass-lg backdrop-blur-2xl z-50 animate-scale-in">
                <div className="px-3 py-2 border-b border-white/[0.06]">
                  <p className="text-xs font-medium text-on-surface truncate">{user?.name}</p>
                  <p className="text-[10px] text-on-surface-dim truncate">{user?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-on-surface-dim hover:text-accent-rose hover:bg-accent-rose/[0.06] transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Nav Drawer */}
      {menuOpen && (
        <div className="md:hidden fixed inset-0 z-30">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMenuOpen(false)} />
          <div className="relative w-64 h-full bg-surface-raised border-r border-white/[0.06] flex flex-col z-10 animate-slide-right pt-12">
            <nav className="flex-1 p-2 space-y-0.5">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-accent-amber/[0.08] text-accent-amber'
                        : 'text-on-surface-muted hover:text-on-surface hover:bg-white/[0.03]'
                    }`
                  }
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
