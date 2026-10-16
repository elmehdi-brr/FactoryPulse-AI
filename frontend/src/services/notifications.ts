import { apiRequest } from './api'

import type {
  AppNotification,
  NotificationUpdatePayload,
} from '../types/notification'

export async function getUserNotifications(
  userId: number,
): Promise<AppNotification[]> {
  return apiRequest<AppNotification[]>(
    `/users/${userId}/notifications`,
  )
}

export async function updateNotification(
  notificationId: number,
  payload: NotificationUpdatePayload,
): Promise<AppNotification> {
  return apiRequest<AppNotification>(
    `/notifications/${notificationId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}