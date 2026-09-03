import { apiRequest } from './api'
import type {
  ProductionLine,
  ProductionLineOEE,
  ProductionLineDowntime,
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