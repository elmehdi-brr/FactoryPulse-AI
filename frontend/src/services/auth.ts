import type {
  AuthenticatedUser,
  LoginCredentials,
  TokenResponse,
} from '../types/auth'
import { apiRequest } from './api'
import {
  clearAccessToken,
  setAccessToken,
} from './authStorage'

export async function login(
  credentials: LoginCredentials,
): Promise<TokenResponse> {
  const formData = new URLSearchParams()

  formData.set(
    'username',
    credentials.email,
  )

  formData.set(
    'password',
    credentials.password,
  )

  const token = await apiRequest<TokenResponse>(
    '/auth/login',
    {
      method: 'POST',
      authenticated: false,
      headers: {
        'Content-Type':
          'application/x-www-form-urlencoded',
      },
      body: formData,
    },
  )

  setAccessToken(token.access_token)

  return token
}

export async function getCurrentUser(): Promise<AuthenticatedUser> {
  return apiRequest<AuthenticatedUser>(
    '/auth/me',
  )
}

export function logout(): void {
  clearAccessToken()
}