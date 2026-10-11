export type Alert = {
  id: number
  sensor_id: number
  prediction_id: number | null
  severity: string
  title: string
  message: string
  status: string
  created_at: string
}

export type AlertSensorContext = {
  id: number
  machine_id: number
  name: string
  sensor_type: string
  unit: string
  status: string
  created_at: string
}

export type AlertUpdatePayload = {
  severity?: string
  title?: string
  message?: string
  status?: string
}