import { apiRequest } from './api'
import type {
  MachineMaintenanceRecord,
} from '../types/machine'

export async function getMaintenanceRecords(): Promise<
  MachineMaintenanceRecord[]
> {
  return apiRequest<MachineMaintenanceRecord[]>(
    '/maintenance-records',
  )
}

export async function getMaintenanceRecordById(
  recordId: number,
): Promise<MachineMaintenanceRecord> {
  return apiRequest<MachineMaintenanceRecord>(
    `/maintenance-records/${recordId}`,
  )
}

export async function updateMaintenanceRecord(
  recordId: number,
  payload: Pick<MachineMaintenanceRecord, 'status'>,
): Promise<MachineMaintenanceRecord> {
  return apiRequest<MachineMaintenanceRecord>(
    `/maintenance-records/${recordId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}