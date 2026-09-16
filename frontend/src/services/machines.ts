import { apiRequest } from './api'
import type {
  Machine,
  MachineReliability,
} from '../types/machine'

export async function getMachines(): Promise<
  Machine[]
> {
  return apiRequest<Machine[]>(
    '/machines',
  )
}

export async function getMachineReliability(
  machineId: number,
  startAt?: Date,
  endAt?: Date,
): Promise<MachineReliability> {
  const searchParams = new URLSearchParams()

  if (startAt) {
    searchParams.set(
      'start_at',
      startAt.toISOString(),
    )
  }

  if (endAt) {
    searchParams.set(
      'end_at',
      endAt.toISOString(),
    )
  }

  const query =
    searchParams.toString()

  return apiRequest<MachineReliability>(
    `/machines/${machineId}/reliability${
      query ? `?${query}` : ''
    }`,
  )
}