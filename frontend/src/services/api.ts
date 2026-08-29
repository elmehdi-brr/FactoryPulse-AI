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

type ApiErrorPayload = {
  detail?: string
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

      if (
        typeof errorBody.detail === 'string'
        && errorBody.detail
      ) {
        message = errorBody.detail
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