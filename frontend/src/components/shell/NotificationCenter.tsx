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

import type {
  DashboardRecentAlert,
} from '../../types/dashboard'
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
  loading?: boolean
  error?: string | null
}

function toNotificationSeverity(
  severity: string,
): NotificationSeverity {
  const normalized =
    severity.trim().toLowerCase()

  if (normalized === 'critical') {
    return 'critical'
  }

  if (
    normalized === 'high'
    || normalized === 'medium'
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
  loading = false,
  error = null,
}: NotificationCenterProps) {
  const navigate = useNavigate()

  const [readIds, setReadIds] = useState<number[]>(
    [],
  )

  const notifications: NotificationItem[] = useMemo(
    () =>
      alerts.map((alert) => ({
        id: alert.id,
        severity: toNotificationSeverity(
          alert.severity,
        ),
        title: alert.title,
        message: alert.message,
        source: alert.machine_name,
        time: formatRelativeTime(
          alert.created_at,
        ),
        read: readIds.includes(alert.id),
      })),
    [alerts, readIds],
  )

  const unreadCount = notifications.filter(
    (notification) => !notification.read,
  ).length

  useEffect(() => {
    onUnreadCountChange(unreadCount)
  }, [onUnreadCountChange, unreadCount])

  function markAllRead() {
    setReadIds(
      alerts.map((alert) => alert.id),
    )
  }

  function markNotificationRead(
    notificationId: number,
  ) {
    setReadIds((current) =>
      current.includes(notificationId)
        ? current
        : [...current, notificationId],
    )
  }

  function openNotification(
    notificationId: number,
  ) {
    markNotificationRead(notificationId)

    navigate('/alerts')
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
                onClick={markAllRead}
                disabled={unreadCount === 0}
              >
                <CheckCheck size={14} />
                Mark all read
              </button>
            </div>

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

              {!loading
                && !error
                && notifications.length === 0 && (
                  <div className="dashboard-panel-state">
                    No open alerts.
                  </div>
                )}

              {!loading
                && !error
                && notifications.map(
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
                      onClick={() => {
                        openNotification(
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
                        delay:
                          0.05
                          + index * 0.055,
                      }}
                      whileHover={{
                        x: -2,
                      }}
                      whileTap={{
                        scale: 0.99,
                      }}
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