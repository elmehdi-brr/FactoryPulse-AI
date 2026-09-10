export type ProductionLine = {
  id: number
  area_id: number
  name: string
  code: string
  description: string | null
  created_at: string
}

export type ProductionLineOEE = {
  production_line_id: number
  start_at: string | null
  end_at: string | null

  run_count: number

  scheduled_time_seconds: number
  planned_downtime_seconds: number
  planned_production_time_seconds: number
  unplanned_downtime_seconds: number
  operating_time_seconds: number

  total_quantity: number
  good_quantity: number

  availability: number
  performance: number
  quality: number
  oee: number
}

export type ProductionLineDowntimeReason = {
  reason: string
  event_count: number
  duration_seconds: number
  percentage: number
}

export type ProductionLineDowntimeMachine = {
  machine_id: number | null
  event_count: number
  duration_seconds: number
  percentage: number
}

export type ProductionLineDowntime = {
  production_line_id: number
  start_at: string | null
  end_at: string | null

  run_count: number
  event_count: number

  recorded_downtime_seconds: number

  planned_downtime_seconds: number
  unplanned_downtime_seconds: number

  by_reason: ProductionLineDowntimeReason[]
  by_machine: ProductionLineDowntimeMachine[]
}

export type OperationalTrendDirection =
  | 'improved'
  | 'worsened'
  | 'unchanged'
  | 'not_comparable'

export type OperationalMetricTrend = {
  current_value: number | null
  previous_value: number | null
  delta: number | null
  direction: OperationalTrendDirection
}

export type MachineOperationalTrend = {
  machine_id: number
  machine_name: string
  machine_code: string

  recorded_downtime: OperationalMetricTrend
  failure_count: OperationalMetricTrend
  mttr: OperationalMetricTrend
  mtbf: OperationalMetricTrend
}

export type OperationalTrendSummary = {
  oee: OperationalMetricTrend
  availability: OperationalMetricTrend
  performance: OperationalMetricTrend
  quality: OperationalMetricTrend

  recorded_downtime: OperationalMetricTrend
  total_failure_count: OperationalMetricTrend

  machines: MachineOperationalTrend[]
}

export type ProductionLineOperationalTrends = {
  production_line_id: number

  current_period: {
    start_at: string
    end_at: string
  }

  previous_period: {
    start_at: string
    end_at: string
  }

  trends: OperationalTrendSummary
}

export type ProductionRunStatus =
  | 'running'
  | 'completed'
  | 'cancelled'

export type ProductionRun = {
  id: number
  production_line_id: number

  started_at: string
  ended_at: string | null

  status: ProductionRunStatus

  target_quantity: number | null
  total_quantity: number
  good_quantity: number
  reject_quantity: number

  ideal_cycle_time_seconds: number | null

  created_at: string
}

export type ProductionRunOEE = {
  production_run_id: number

  scheduled_time_seconds: number

  planned_downtime_seconds: number
  planned_production_time_seconds: number

  unplanned_downtime_seconds: number
  operating_time_seconds: number

  availability: number
  performance: number
  quality: number
  oee: number
}