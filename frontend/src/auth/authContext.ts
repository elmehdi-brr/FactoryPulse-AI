import {
  createContext,
  useContext,
} from 'react'

import type {
  AuthenticatedUser,
  LoginCredentials,
} from '../types/auth'

export type AuthStatus =
  | 'checking'
  | 'authenticated'
  | 'unauthenticated'

export type AuthContextValue = {
  user: AuthenticatedUser | null
  status: AuthStatus
  isAuthenticated: boolean

  login: (
    credentials: LoginCredentials,
  ) => Promise<void>

  logout: () => void
}

export const AuthContext =
  createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error(
      'useAuth must be used inside AuthProvider',
    )
  }

  return context
}