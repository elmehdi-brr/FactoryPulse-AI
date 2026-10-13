export type SensorAIConfigValues = {
  is_enabled: boolean
  engine_name: 'statistical-zscore'
  anomaly_threshold: number
  min_history: number
  history_limit: number
  high_risk_threshold: number
  critical_risk_threshold: number
}

export type SensorAIConfig = SensorAIConfigValues & {
  id: number
  sensor_id: number
  created_at: string
}

export type SensorAIConfigUpdate =
  Partial<SensorAIConfigValues>