import { apiRequest } from './api'
import type {
  Alert,
  AlertSensorContext,
  AlertUpdatePayload,
} from '../types/alert'

export async function getAlerts(): Promise<
  Alert[]
> {
  return apiRequest<Alert[]>('/alerts')
}

export async function getAlertById(
  alertId: number,
): Promise<Alert> {
  return apiRequest<Alert>(
    `/alerts/${alertId}`,
  )
}

export async function getAlertSensors(): Promise<
  AlertSensorContext[]
> {
  return apiRequest<AlertSensorContext[]>(
    '/sensors',
  )
}

export async function updateAlert(
  alertId: number,
  payload: AlertUpdatePayload,
): Promise<Alert> {
  return apiRequest<Alert>(
    `/alerts/${alertId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}