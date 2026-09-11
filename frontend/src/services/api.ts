import {
  clearAccessToken,
  getAccessToken,
} from './authStorage'

import {
  notifySessionInvalidated,
} from './authEvents'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL

if (!API_BASE_URL) {
  throw new Error(
    'VITE_API_BASE_URL is not configured',
  )
}

type ApiValidationIssue = {
  loc?: (string | number)[]
  msg?: string
}

type ApiErrorPayload = {
  detail?: string | ApiValidationIssue[]
}

// FastAPI returns a plain string for raised HTTPExceptions, but a list of
// issue objects for request-validation failures (422). Handle both so the
// user sees the real reason instead of a bare status code.
function readErrorDetail(
  detail: ApiErrorPayload['detail'],
): string | null {
  if (typeof detail === 'string') {
    return detail || null
  }

  if (!Array.isArray(detail)) {
    return null
  }

  const messages = detail.flatMap(
    (issue) => {
      if (!issue?.msg) {
        return []
      }

      const field = Array.isArray(issue.loc)
        ? issue.loc[issue.loc.length - 1]
        : undefined

      return [
        field === undefined
          ? issue.msg
          : `${field}: ${issue.msg}`,
      ]
    },
  )

  return messages.length > 0
    ? messages.join('; ')
    : null
}

export class ApiError extends Error {
  readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)

    this.name = 'ApiError'
    this.status = status
  }
}

export type ApiRequestOptions =
  Omit<RequestInit, 'headers'> & {
    headers?: HeadersInit
    authenticated?: boolean
  }

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const {
    authenticated = true,
    headers: providedHeaders,
    ...requestOptions
  } = options

  const headers = new Headers(
    providedHeaders,
  )

  if (authenticated) {
    const accessToken = getAccessToken()

    if (accessToken) {
      headers.set(
        'Authorization',
        `Bearer ${accessToken}`,
      )
    }
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...requestOptions,
      headers,
    },
  )

  if (!response.ok) {
    if (
      response.status === 401
      && authenticated
    ) {
      clearAccessToken()
      notifySessionInvalidated()
    }

    let message = `Request failed with status ${response.status}`

    try {
      const errorBody =
        (await response.json()) as ApiErrorPayload

      const detail = readErrorDetail(
        errorBody.detail,
      )

      if (detail) {
        message = detail
      }
    } catch {
      // The backend response did not contain JSON.
    }

    throw new ApiError(
      message,
      response.status,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}