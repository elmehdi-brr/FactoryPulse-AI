import {
  Activity,
} from 'lucide-react'
import {
  motion,
} from 'motion/react'
import {
  Navigate,
  Outlet,
  useLocation,
} from 'react-router-dom'

import { useAuth } from '../auth/authContext'

export function ProtectedRoute() {
  const {
    status,
    isAuthenticated,
  } = useAuth()

  const location = useLocation()

  if (status === 'checking') {
    return (
      <div className="session-loading">
        <motion.div
          className="session-loading-mark"
          initial={{
            opacity: 0,
            scale: 0.86,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
        >
          <Activity size={22} />
        </motion.div>

        <motion.div
          className="session-loading-pulse"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            delay: 0.15,
          }}
        >
          <strong>FactoryPulse</strong>
          <span>Restoring secure session...</span>
        </motion.div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location,
        }}
      />
    )
  }

  return <Outlet />
}