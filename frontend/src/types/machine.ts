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

  operating_exposure_seconds: number

  mtbf_seconds: number | null
}