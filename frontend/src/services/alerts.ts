import { apiRequest } from './api'
import type {
  Alert,
  AlertSensorContext,
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