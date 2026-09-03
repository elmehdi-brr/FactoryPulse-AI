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