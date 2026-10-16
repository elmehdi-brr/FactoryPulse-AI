export type AppNotification = {
  id: number
  user_id: number
  alert_id: number | null
  title: string
  message: string
  channel: string
  is_read: boolean
  created_at: string
}

export type NotificationUpdatePayload = {
  is_read: boolean
}