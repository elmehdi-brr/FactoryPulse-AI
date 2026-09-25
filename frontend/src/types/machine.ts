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