import { apiRequest } from './api'

import type {
  DashboardOverviewResponse,
} from '../types/dashboard'

export type DashboardOverviewParams = {
  startAt?: string
  endAt?: string
}

export async function getDashboardOverview(
  params: DashboardOverviewParams = {},
): Promise<DashboardOverviewResponse> {
  const searchParams = new URLSearchParams()

  if (params.startAt) {
    searchParams.set(
      'start_at',
      params.startAt,
    )
  }

  if (params.endAt) {
    searchParams.set(
      'end_at',
      params.endAt,
    )
  }

  const query = searchParams.toString()

  return apiRequest<DashboardOverviewResponse>(
    `/dashboard/overview${
      query ? `?${query}` : ''
    }`,
  )
}