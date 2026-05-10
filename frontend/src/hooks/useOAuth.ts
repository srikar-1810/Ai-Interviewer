import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export function useOAuthCallback() {
  const [searchParams] = useSearchParams()
  const [handled, setHandled] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const register = useAuthStore((s) => s.register)

  useEffect(() => {
    if (handled) return
    const token = searchParams.get('token')
    const userId = searchParams.get('user_id')
    const name = searchParams.get('name')
    const email = searchParams.get('email')

    if (token && userId) {
      useAuthStore.setState({
        isAuthenticated: true,
        user: { id: userId, name: name || 'User', email: email || '' },
      })
      setHandled(true)
      navigate('/')
    }
  }, [searchParams, handled, navigate, login])
}
