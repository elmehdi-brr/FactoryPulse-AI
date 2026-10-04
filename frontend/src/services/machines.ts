import { apiRequest } from './api'
import type {
  Machine,
  MachineOperationalIntelligence,
  MachineReliability,
  MachineSensor,
  MachineTelemetry,
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

export async function getMachineOperationalIntelligence(
  machineId: number,
  startAt?: Date,
  endAt?: Date,
): Promise<MachineOperationalIntelligence> {
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

  return apiRequest<MachineOperationalIntelligence>(
    `/machines/${machineId}/operational-intelligence${
      query ? `?${query}` : ''
    }`,
  )
}

export async function getMachineSensors(
  machineId: number,
): Promise<MachineSensor[]> {
  return apiRequest<MachineSensor[]>(
    `/machines/${machineId}/sensors`,
  )
}


export async function getMachineTelemetry(
  machineId: number,
  limitPerSensor = 12,
): Promise<MachineTelemetry> {
  const searchParams = new URLSearchParams({
    limit_per_sensor: String(limitPerSensor),
  })

  return apiRequest<MachineTelemetry>(
    `/machines/${machineId}/telemetry?${searchParams.toString()}`,
  )
}