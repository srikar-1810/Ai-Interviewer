import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  isAuthenticated: boolean
  user: { id: string; name: string; email: string } | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

async function authRequest(path: string, body: object) {
  const res = await fetch(`/api/auth/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || 'Authentication failed')
  }
  return data as { user: { id: string; name: string; email: string }; token: string }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      login: async (email, password) => {
        const data = await authRequest('login', { email, password })
        set({ isAuthenticated: true, user: data.user, token: data.token })
      },
      register: async (name, email, password) => {
        const data = await authRequest('register', { name, email, password })
        set({ isAuthenticated: true, user: data.user, token: data.token })
      },
      logout: () => {
        set({ isAuthenticated: false, user: null, token: null })
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
