import {
  ApiError,
  apiRequest,
} from './api'

import type {
  MachineSensor,
} from '../types/machine'

import type {
  SensorAIConfig,
  SensorAIConfigUpdate,
  SensorAIConfigValues,
} from '../types/sensor-ai-config'

export async function getSensors(): Promise<
  MachineSensor[]
> {
  return apiRequest<MachineSensor[]>('/sensors')
}

export async function getSensorAIConfig(
  sensorId: number,
): Promise<SensorAIConfig | null> {
  try {
    return await apiRequest<SensorAIConfig>(
      `/sensors/${sensorId}/ai-config`,
    )
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 404 &&
      error.message === 'Sensor AI configuration not found'
    ) {
      return null
    }

    throw error
  }
}

export async function createSensorAIConfig(
  sensorId: number,
  payload: SensorAIConfigValues,
): Promise<SensorAIConfig> {
  return apiRequest<SensorAIConfig>(
    `/sensors/${sensorId}/ai-config`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export async function updateSensorAIConfig(
  sensorId: number,
  payload: SensorAIConfigUpdate,
): Promise<SensorAIConfig> {
  return apiRequest<SensorAIConfig>(
    `/sensors/${sensorId}/ai-config`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}