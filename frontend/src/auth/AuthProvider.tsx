import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type {
  ReactNode,
} from 'react'

import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from '../services/auth'
import {
  subscribeToSessionInvalidation,
} from '../services/authEvents'
import {
  getAccessToken,
} from '../services/authStorage'
import type {
  AuthenticatedUser,
  LoginCredentials,
} from '../types/auth'
import {
  AuthContext,
} from './authContext'
import type {
  AuthContextValue,
  AuthStatus,
} from './authContext'

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] =
    useState<AuthenticatedUser | null>(null)

  const [status, setStatus] =
    useState<AuthStatus>('checking')

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      const token = getAccessToken()

      if (!token) {
        if (!cancelled) {
          setStatus('unauthenticated')
        }

        return
      }

      try {
        const currentUser =
          await getCurrentUser()

        if (!cancelled) {
          setUser(currentUser)
          setStatus('authenticated')
        }
      } catch {
        logoutRequest()

        if (!cancelled) {
          setUser(null)
          setStatus('unauthenticated')
        }
      }
    }

    void restoreSession()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    return subscribeToSessionInvalidation(() => {
      setUser(null)
      setStatus('unauthenticated')
    })
  }, [])

  const login = useCallback(
    async (
      credentials: LoginCredentials,
    ) => {
      await loginRequest(credentials)

      try {
        const currentUser =
          await getCurrentUser()

        setUser(currentUser)
        setStatus('authenticated')
      } catch (error) {
        logoutRequest()

        setUser(null)
        setStatus('unauthenticated')

        throw error
      }
    },
    [],
  )

  const logout = useCallback(() => {
    logoutRequest()

    setUser(null)
    setStatus('unauthenticated')
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      isAuthenticated:
        status === 'authenticated',
      login,
      logout,
    }),
    [
      user,
      status,
      login,
      logout,
    ],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}