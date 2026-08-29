export type DashboardPeriod = {
  start_at: string | null
  end_at: string | null
}

export type DashboardKPIs = {
  overall_oee: number | null
  availability: number | null
  active_alert_count: number
  fleet_mtbf_seconds: number | null
}

export type DashboardProductionLineSummary = {
  id: number
  name: string
  code: string
  oee: number | null
  availability: number | null
}

export type DashboardMachineHealth = {
  total_machines: number
  healthy_count: number
  attention_count: number
  critical_count: number
}

export type DashboardRecentAlert = {
  id: number

  machine_id: number
  machine_name: string
  machine_code: string

  severity: string
  title: string
  message: string

  created_at: string
}

export type DashboardOverviewResponse = {
  period: DashboardPeriod

  kpis: DashboardKPIs

  production_lines: DashboardProductionLineSummary[]

  machine_health: DashboardMachineHealth

  recent_alerts: DashboardRecentAlert[]
}