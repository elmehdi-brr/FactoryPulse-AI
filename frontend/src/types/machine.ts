export type MachineStatus = string

export type Machine = {
  id: number
  area_id: number
  production_line_id: number | null
  name: string
  code: string
  location: string | null
  status: MachineStatus
  created_at: string
}

export type MachineReliability = {
  machine_id: number

  start_at: string | null
  end_at: string | null

  failure_count: number

  total_failure_downtime_seconds: number

  mttr_seconds: number | null

  operating_exposure_seconds: number | null

  mtbf_seconds: number | null
}

export type MachineHealthStatus =
  | 'healthy'
  | 'attention'
  | 'critical'

export type MachineOperationalImpact = {
  recorded_downtime_event_count: number
  recorded_downtime_seconds: number
  recorded_downtime_share: number | null
}

export type MachineOperationalPriority = {
  priority_rank: number | null
  downtime_rank: number | null
  failure_rank: number | null
  mttr_rank: number | null
  mtbf_rank: number | null
}

export type MachineOperationalIntelligence = {
  machine_id: number

  start_at: string | null
  end_at: string | null

  health_status: MachineHealthStatus

  open_alert_count: number
  critical_alert_count: number
  attention_alert_count: number

  production_line_id: number | null

  failure_count: number
  total_failure_downtime_seconds: number
  mttr_seconds: number | null

  operating_exposure_seconds: number | null
  mtbf_seconds: number | null

  operational_impact:
    | MachineOperationalImpact
    | null

  operational_priority:
    | MachineOperationalPriority
    | null
}


export type MachineSensor = {
  id: number
  machine_id: number
  name: string
  sensor_type: string
  unit: string
  status: string
  created_at: string
}

export type MachineTelemetryReading = {
  id: number
  value: number
  recorded_at: string
}

export type MachineSensorTelemetry = {
  sensor_id: number
  name: string
  sensor_type: string
  unit: string
  status: string
  latest_reading: MachineTelemetryReading | null
  recent_readings: MachineTelemetryReading[]
}

export type MachineTelemetry = {
  machine_id: number
  sensors: MachineSensorTelemetry[]
}

export type MachinePrediction = {
  prediction_id: number

  sensor_id: number
  sensor_name: string
  sensor_type: string
  unit: string

  source_reading_id: number | null

  predicted_value: number
  anomaly_score: number | null
  is_anomaly: boolean

  model_name: string
  model_version: string | null

  predicted_at: string
}

export type MachinePredictions = {
  machine_id: number
  predictions: MachinePrediction[]
}

export type MachineMaintenanceRecord = {
  id: number

  machine_id: number
  alert_id: number | null
  performed_by_user_id: number | null

  maintenance_type:
    | 'preventive'
    | 'corrective'

  description: string

  status:
    | 'planned'
    | 'in_progress'
    | 'completed'
    | 'verified'
    | 'cancelled'

  performed_at: string | null
  created_at: string
}

export type MachineMaintenanceEffectiveness = {
  machine_id: number

  start_at: string | null
  end_at: string | null

  total_records: number

  preventive_count: number
  corrective_count: number
  preventive_share: number | null

  planned_count: number
  in_progress_count: number
  completed_count: number
  verified_count: number
  cancelled_count: number

  finished_count: number
  completion_rate: number | null
  verification_rate: number | null

  alert_linked_count: number
  alert_link_rate: number | null

  assigned_count: number
  assignment_rate: number | null

  total_alerts: number
  responded_alert_count: number
  unresponded_alert_count: number
  response_rate: number | null

  average_response_time_seconds: number | null
  median_response_time_seconds: number | null
  fastest_response_time_seconds: number | null
  slowest_response_time_seconds: number | null
}