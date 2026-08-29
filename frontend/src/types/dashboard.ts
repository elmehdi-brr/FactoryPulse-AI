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

export type DashboardOverviewResponse = {
  period: DashboardPeriod
  kpis: DashboardKPIs
  production_lines: DashboardProductionLineSummary[]
}