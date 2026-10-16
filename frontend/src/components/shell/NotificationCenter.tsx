import {
  AlertTriangle,
  ArrowUpRight,
  BellRing,
  CheckCheck,
  CircleAlert,
  Info,
  X,
} from 'lucide-react'
import {
  AnimatePresence,
  motion,
} from 'motion/react'
import {
  useEffect,
  useMemo,
  useState,
} from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '../../services/api'
import { updateNotification } from '../../services/notifications'
import type {
  DashboardRecentAlert,
} from '../../types/dashboard'
import type {
  AppNotification,
} from '../../types/notification'
import { formatRelativeTime } from '../../utils/time'

type NotificationSeverity =
  | 'critical'
  | 'high'
  | 'info'

type NotificationItem = {
  id: number
  severity: NotificationSeverity
  title: string
  message: string
  source: string
  time: string
  read: boolean
}

type NotificationCenterProps = {
  open: boolean
  onClose: () => void
  onUnreadCountChange: (count: number) => void
  alerts: DashboardRecentAlert[]
  notifications: AppNotification[]
  onNotificationUpdated: (
    notification: AppNotification,
  ) => void
  loading?: boolean
  error?: string | null
}

function toNotificationSeverity(
  severity: string,
): NotificationSeverity {
  const normalized = severity.trim().toLowerCase()

  if (normalized === 'critical') {
    return 'critical'
  }

  if (
    normalized === 'high' ||
    normalized === 'medium'
  ) {
    return 'high'
  }

  return 'info'
}

function getSeverityIcon(
  severity: NotificationSeverity,
) {
  if (severity === 'critical') {
    return CircleAlert
  }

  if (severity === 'high') {
    return AlertTriangle
  }

  return Info
}

export function NotificationCenter({
  open,
  onClose,
  onUnreadCountChange,
  alerts,
  notifications,
  onNotificationUpdated,
  loading = false,
  error = null,
}: NotificationCenterProps) {
  const navigate = useNavigate()

  const [updatingIds, setUpdatingIds] =
    useState<number[]>([])

  const [markingAllRead, setMarkingAllRead] =
    useState(false)

  const [actionError, setActionError] =
    useState<string | null>(null)

  const notificationItems: NotificationItem[] =
    useMemo(
      () =>
        notifications.map((notification) => {
          const linkedAlert =
            notification.alert_id === null
              ? undefined
              : alerts.find(
                  (alert) =>
                    alert.id === notification.alert_id,
                )

          const severityFromTitle =
            /^\[([^\]]+)\]/.exec(
              notification.title,
            )?.[1]

          return {
            id: notification.id,
            severity: toNotificationSeverity(
              severityFromTitle ??
                linkedAlert?.severity ??
                'info',
            ),
            title: notification.title.replace(
              /^\[[^\]]+\]\s*/,
              '',
            ),
            message: notification.message,
            source:
              linkedAlert?.machine_name ??
              (notification.alert_id !== null
                ? `Alert #${notification.alert_id}`
                : 'FactoryPulse'),
            time: formatRelativeTime(
              notification.created_at,
            ),
            read: notification.is_read,
          }
        }),
      [alerts, notifications],
    )

  const unreadCount = notifications.filter(
    (notification) => !notification.is_read,
  ).length

  useEffect(() => {
    onUnreadCountChange(unreadCount)
  }, [onUnreadCountChange, unreadCount])

  async function markNotificationRead(
    notificationId: number,
  ): Promise<boolean> {
    const notification = notifications.find(
      (item) => item.id === notificationId,
    )

    if (!notification) {
      return false
    }

    if (notification.is_read) {
      return true
    }

    if (
      markingAllRead ||
      updatingIds.includes(notificationId)
    ) {
      return false
    }

    setActionError(null)

    setUpdatingIds((current) =>
      current.includes(notificationId)
        ? current
        : [...current, notificationId],
    )

    try {
      const updated = await updateNotification(
        notificationId,
        { is_read: true },
      )

      onNotificationUpdated(updated)

      return true
    } catch (requestError) {
      setActionError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Unable to mark the notification as read.',
      )

      return false
    } finally {
      setUpdatingIds((current) =>
        current.filter(
          (id) => id !== notificationId,
        ),
      )
    }
  }

  async function markAllRead() {
    const unreadNotifications = notifications.filter(
      (notification) => !notification.is_read,
    )

    if (
      unreadNotifications.length === 0 ||
      markingAllRead ||
      updatingIds.length > 0
    ) {
      return
    }

    setActionError(null)
    setMarkingAllRead(true)

    try {
      const results = await Promise.allSettled(
        unreadNotifications.map((notification) =>
          updateNotification(
            notification.id,
            { is_read: true },
          ),
        ),
      )

      const successfulUpdates = results.flatMap(
        (result) =>
          result.status === 'fulfilled'
            ? [result.value]
            : [],
      )

      successfulUpdates.forEach(
        onNotificationUpdated,
      )

      const failureCount = results.filter(
        (result) => result.status === 'rejected',
      ).length

      if (failureCount > 0) {
        setActionError(
          `${failureCount} notification(s) could not be marked as read. Please retry.`,
        )
      }
    } catch {
      setActionError(
        'Unable to update notifications. Please retry.',
      )
    } finally {
      setMarkingAllRead(false)
    }
  }

  async function openNotification(
    notificationId: number,
  ) {
    const notification = notifications.find(
      (item) => item.id === notificationId,
    )

    const saved = await markNotificationRead(
      notificationId,
    )

    if (!saved) {
      return
    }

    if (notification?.alert_id != null) {
      navigate(`/alerts?alertId=${notification.alert_id}`)
    } else {
      navigate('/alerts')
    }

    onClose()
  }

  function openAllAlerts() {
    navigate('/alerts')
    onClose()
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="notification-center-layer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            type="button"
            className="notification-center-backdrop"
            aria-label="Close notification center"
            onClick={onClose}
          />

          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label="Notification center"
            className="notification-center"
            initial={{
              opacity: 0,
              x: 26,
              y: -8,
              scale: 0.98,
              filter: 'blur(5px)',
            }}
            animate={{
              opacity: 1,
              x: 0,
              y: 0,
              scale: 1,
              filter: 'blur(0px)',
            }}
            exit={{
              opacity: 0,
              x: 18,
              y: -5,
              scale: 0.985,
              filter: 'blur(4px)',
            }}
            transition={{
              duration: 0.22,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            <header className="notification-header">
              <div className="notification-title">
                <span className="notification-title-icon">
                  <BellRing size={17} />
                </span>

                <div>
                  <strong>Notifications</strong>

                  <span>
                    {unreadCount > 0
                      ? `${unreadCount} unread`
                      : 'You’re all caught up'}
                  </span>
                </div>
              </div>

              <button
                type="button"
                className="notification-close"
                aria-label="Close notifications"
                onClick={onClose}
              >
                <X size={17} />
              </button>
            </header>

            <div className="notification-toolbar">
              <span>Operational inbox</span>

              <button
                type="button"
                onClick={() => void markAllRead()}
                disabled={
                  unreadCount === 0 ||
                  markingAllRead ||
                  updatingIds.length > 0
                }
              >
                <CheckCheck size={14} />
                {markingAllRead
                  ? 'Marking...'
                  : 'Mark all read'}
              </button>
            </div>

            {actionError && (
              <div
                className="notification-action-error"
                role="alert"
              >
                {actionError}
              </div>
            )}

            <div className="notification-list">
              {loading && (
                <div className="dashboard-panel-state">
                  Loading notifications...
                </div>
              )}

              {!loading && error && (
                <div
                  className="dashboard-panel-state"
                  role="alert"
                >
                  {error}
                </div>
              )}

              {!loading &&
                !error &&
                notificationItems.length === 0 && (
                  <div className="dashboard-panel-state">
                    No notifications yet.
                  </div>
                )}

              {!loading &&
                !error &&
                notificationItems.map(
                  (notification, index) => {
                    const Icon = getSeverityIcon(
                      notification.severity,
                    )

                    return (
                      <motion.button
                        key={notification.id}
                        type="button"
                        className={`notification-item notification-${notification.severity} ${
                          notification.read
                            ? 'notification-item-read'
                            : ''
                        }`}
                        disabled={
                          markingAllRead ||
                          updatingIds.includes(
                            notification.id,
                          )
                        }
                        onClick={() => {
                          void openNotification(
                            notification.id,
                          )
                        }}
                        initial={{
                          opacity: 0,
                          x: 12,
                        }}
                        animate={{
                          opacity: 1,
                          x: 0,
                        }}
                        transition={{
                          delay: 0.05 + index * 0.055,
                        }}
                        whileHover={{ x: -2 }}
                        whileTap={{ scale: 0.99 }}
                      >
                        <span className="notification-icon">
                          <Icon size={16} />
                        </span>

                        <span className="notification-copy">
                          <span className="notification-item-heading">
                            <strong>
                              {notification.title}
                            </strong>

                            {!notification.read && (
                              <span className="notification-unread-dot" />
                            )}
                          </span>

                          <span className="notification-message">
                            {notification.message}
                          </span>

                          <span className="notification-meta">
                            <span>
                              {notification.source}
                            </span>

                            <span className="notification-meta-divider" />

                            <span>
                              {notification.time}
                            </span>
                          </span>
                        </span>

                        <ArrowUpRight
                          className="notification-open-icon"
                          size={14}
                        />
                      </motion.button>
                    )
                  },
                )}
            </div>

            <footer className="notification-footer">
              <button
                type="button"
                onClick={openAllAlerts}
              >
                View all alerts
                <ArrowUpRight size={14} />
              </button>
            </footer>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  )
}