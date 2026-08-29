import {
  Activity,
  ArrowRight,
  Eye,
  EyeOff,
  Factory,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from 'lucide-react'
import { motion } from 'motion/react'
import {
  useState,
} from 'react'
import type {
  FormEvent,
} from 'react'
import {
  Navigate,
  useLocation,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from '../auth/authContext'
import { ApiError } from '../services/api'

type LoginLocationState = {
  from?: {
    pathname?: string
  }
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()

  const {
    login,
    status,
    isAuthenticated,
  } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [
    passwordVisible,
    setPasswordVisible,
  ] = useState(false)

  const [submitting, setSubmitting] =
    useState(false)

  const [error, setError] =
    useState<string | null>(null)

  if (status === 'checking') {
    return (
      <div className="session-loading">
        <motion.div
          className="session-loading-mark"
          initial={{
            opacity: 0,
            scale: 0.88,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
        >
          <Activity size={22} />
        </motion.div>

        <div className="session-loading-pulse">
          <strong>FactoryPulse</strong>
          <span>Restoring secure session...</span>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to="/overview"
        replace
      />
    )
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (submitting) {
      return
    }

    setError(null)
    setSubmitting(true)

    try {
      await login({
        email: email.trim(),
        password,
      })

      const state =
        location.state as
          | LoginLocationState
          | null

      const destination =
        state?.from?.pathname
        ?? '/overview'

      navigate(destination, {
        replace: true,
      })
    } catch (loginError) {
      if (loginError instanceof ApiError) {
        setError(loginError.message)
      } else {
        setError(
          'Unable to connect to FactoryPulse. Please try again.',
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-visual">
        <div className="login-grid" />

        <motion.div
          className="login-brand"
          initial={{
            opacity: 0,
            y: -12,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
        >
          <span className="login-brand-mark">
            <Activity
              size={20}
              strokeWidth={2.3}
            />
          </span>

          <div>
            <strong>FactoryPulse</strong>
            <span>Industrial AI</span>
          </div>
        </motion.div>

        <motion.div
          className="login-visual-content"
          initial={{
            opacity: 0,
            y: 24,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            delay: 0.12,
            duration: 0.55,
            ease: [0.22, 1, 0.36, 1],
          }}
        >
          <p className="login-eyebrow">
            Industrial Intelligence Platform
          </p>

          <h1>
            See the factory.
            <br />
            Understand the operation.
          </h1>

          <p className="login-visual-description">
            Production, reliability, maintenance,
            alerts, and operational intelligence
            connected in one secure workspace.
          </p>

          <div className="login-capabilities">
            <div>
              <span>
                <Factory size={18} />
              </span>

              <div>
                <strong>
                  Production intelligence
                </strong>

                <p>
                  OEE, downtime, line performance,
                  and operational trends.
                </p>
              </div>
            </div>

            <div>
              <span>
                <ShieldCheck size={18} />
              </span>

              <div>
                <strong>
                  Secure operational access
                </strong>

                <p>
                  Role-based access to industrial
                  data and workflows.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        <div className="login-ambient login-ambient-one" />
        <div className="login-ambient login-ambient-two" />
      </section>

      <section className="login-form-side">
        <motion.div
          className="login-form-container"
          initial={{
            opacity: 0,
            x: 20,
          }}
          animate={{
            opacity: 1,
            x: 0,
          }}
          transition={{
            delay: 0.08,
            duration: 0.48,
            ease: [0.22, 1, 0.36, 1],
          }}
        >
          <div className="login-form-heading">
            <span className="login-security-mark">
              <LockKeyhole size={18} />
            </span>

            <div>
              <p>Secure workspace</p>
              <h2>Welcome back</h2>
            </div>
          </div>

          <p className="login-form-description">
            Sign in with your FactoryPulse account
            to continue to the operational command
            center.
          </p>

          <form
            className="login-form"
            onSubmit={handleSubmit}
          >
            <label className="login-field">
              <span>Email address</span>

              <div className="login-input-shell">
                <Mail size={18} />

                <input
                  type="email"
                  value={email}
                  onChange={(event) => {
                    setEmail(
                      event.target.value,
                    )
                  }}
                  placeholder="you@company.com"
                  autoComplete="email"
                  required
                  disabled={submitting}
                />
              </div>
            </label>

            <label className="login-field">
              <span>Password</span>

              <div className="login-input-shell">
                <LockKeyhole size={18} />

                <input
                  type={
                    passwordVisible
                      ? 'text'
                      : 'password'
                  }
                  value={password}
                  onChange={(event) => {
                    setPassword(
                      event.target.value,
                    )
                  }}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  disabled={submitting}
                />

                <button
                  type="button"
                  className="password-toggle"
                  aria-label={
                    passwordVisible
                      ? 'Hide password'
                      : 'Show password'
                  }
                  onClick={() => {
                    setPasswordVisible(
                      (current) => !current,
                    )
                  }}
                >
                  {passwordVisible ? (
                    <EyeOff size={17} />
                  ) : (
                    <Eye size={17} />
                  )}
                </button>
              </div>
            </label>

            {error && (
              <motion.div
                className="login-error"
                role="alert"
                initial={{
                  opacity: 0,
                  y: -5,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
              >
                {error}
              </motion.div>
            )}

            <motion.button
              type="submit"
              className="login-submit"
              disabled={submitting}
              whileHover={
                submitting
                  ? undefined
                  : {
                      y: -1,
                    }
              }
              whileTap={
                submitting
                  ? undefined
                  : {
                      scale: 0.99,
                    }
              }
            >
              {submitting ? (
                <>
                  <span className="login-spinner" />
                  Authenticating...
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight size={18} />
                </>
              )}
            </motion.button>
          </form>

          <div className="login-form-footer">
            <ShieldCheck size={15} />

            <span>
              Protected by FactoryPulse secure
              authentication
            </span>
          </div>
        </motion.div>
      </section>
    </main>
  )
}