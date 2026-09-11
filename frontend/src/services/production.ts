import { apiRequest } from './api'
import type {
  ProductionLine,
  ProductionLineDowntime,
  ProductionLineOEE,
  ProductionLineOperationalTrends,
  ProductionRun,
  ProductionRunOEE,
} from '../types/production'

export async function getProductionLines(): Promise<
  ProductionLine[]
> {
  return apiRequest<ProductionLine[]>(
    '/production-lines',
  )
}

export async function getProductionLineOEE(
  productionLineId: number,
): Promise<ProductionLineOEE> {
  return apiRequest<ProductionLineOEE>(
    `/production-lines/${productionLineId}/oee`,
  )
}

export async function getProductionLineDowntime(
  productionLineId: number,
): Promise<ProductionLineDowntime> {
  return apiRequest<ProductionLineDowntime>(
    `/production-lines/${productionLineId}/downtime-analytics`,
  )
}

export type ProductionPeriod = {
  startAt: Date
  endAt: Date
}

export async function getProductionLineOperationalTrends(
  productionLineId: number,
  period: ProductionPeriod,
): Promise<ProductionLineOperationalTrends> {
  const query = new URLSearchParams({
    start_at: period.startAt.toISOString(),
    end_at: period.endAt.toISOString(),
  })

  return apiRequest<ProductionLineOperationalTrends>(
    `/production-lines/${productionLineId}`
    + `/operational-trends?${query.toString()}`,
  )
}

export async function getProductionLineRuns(
  productionLineId: number,
): Promise<ProductionRun[]> {
  return apiRequest<ProductionRun[]>(
    `/production-lines/${productionLineId}/production-runs`,
  )
}

export async function getProductionRunOEE(
  productionRunId: number,
): Promise<ProductionRunOEE> {
  return apiRequest<ProductionRunOEE>(
    `/production-runs/${productionRunId}/oee`,
  )
}