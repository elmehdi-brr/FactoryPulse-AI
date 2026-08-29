export type TokenResponse = {
  access_token: string
  token_type: string
}

export type AuthenticatedUser = {
  id: number
  email: string
  full_name: string
  role_id: number | null
  is_active: boolean
  created_at: string
}

export type LoginCredentials = {
  email: string
  password: string
}