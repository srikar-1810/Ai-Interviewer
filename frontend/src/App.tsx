import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Register from './pages/Register'
import Login from './pages/Login'
import Home from './pages/Home'
import RoleDiscovery from './pages/RoleDiscovery'
import JobMarket from './pages/JobMarket'
import CoachingSetup from './pages/CoachingSetup'
import InterviewSuite from './pages/InterviewSuite'
import Analytics from './pages/Analytics'
import CodingRound from './pages/CodingRound'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Home />} />
        <Route path="roles" element={<RoleDiscovery />} />
        <Route path="jobs" element={<JobMarket />} />
        <Route path="coaching" element={<CoachingSetup />} />
        <Route path="interview" element={<InterviewSuite />} />
        <Route path="coding" element={<CodingRound />} />
        <Route path="analytics" element={<Analytics />} />
      </Route>
    </Routes>
  )
}
