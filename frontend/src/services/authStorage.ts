const ACCESS_TOKEN_KEY = 'factorypulse_access_token'

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(
  token: string,
): void {
  sessionStorage.setItem(
    ACCESS_TOKEN_KEY,
    token,
  )
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
}