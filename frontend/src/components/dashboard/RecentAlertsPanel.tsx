import {
  ArrowUpRight,
  BellRing,
} from 'lucide-react'
import { motion } from 'motion/react'
import {
  useNavigate,
} from 'react-router-dom'

import type {
  DashboardRecentAlert,
} from '../../types/dashboard'

type RecentAlertsPanelProps = {
  alerts: DashboardRecentAlert[]
  loading?: boolean
}

function formatSeverity(
  severity: string,
): string {
  const normalized =
    severity.trim().toLowerCase()

  return normalized
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    )
}

function getSeverityClass(
  severity: string,
): string {
  const normalized =
    severity.trim().toLowerCase()

  if (
    normalized === 'critical'
    || normalized === 'high'
    || normalized === 'medium'
  ) {
    return normalized
  }

  return 'unknown'
}

function formatRelativeTime(
  createdAt: string,
): string {
  const timestamp =
    new Date(createdAt).getTime()

  if (Number.isNaN(timestamp)) {
    return 'Unknown time'
  }

  const elapsedMilliseconds =
    Date.now() - timestamp

  const elapsedMinutes =
    Math.max(
      0,
      Math.floor(
        elapsedMilliseconds / 60000,
      ),
    )

  if (elapsedMinutes < 1) {
    return 'Just now'
  }

  if (elapsedMinutes < 60) {
    return `${elapsedMinutes} min ago`
  }

  const elapsedHours =
    Math.floor(elapsedMinutes / 60)

  if (elapsedHours < 24) {
    return `${elapsedHours}h ago`
  }

  const elapsedDays =
    Math.floor(elapsedHours / 24)

  return `${elapsedDays}d ago`
}

export function RecentAlertsPanel({
  alerts,
  loading = false,
}: RecentAlertsPanelProps) {
  const navigate = useNavigate()

  return (
    <motion.article
      className="panel compact-panel recent-alerts-panel"
      initial={{
        opacity: 0,
        y: 22,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: 0.46,
      }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            Operational awareness
          </span>

          <h2>Recent alerts</h2>
        </div>

        <BellRing size={20} />
      </div>

      <div className="recent-alert-list">
        {loading && (
          <div className="dashboard-panel-state">
            Loading recent alerts...
          </div>
        )}

        {!loading && alerts.length === 0 && (
          <div className="dashboard-panel-state">
            No open alerts.
          </div>
        )}

        {!loading
          && alerts.map((alert, index) => {
            const severityClass =
              getSeverityClass(
                alert.severity,
              )

            return (
              <motion.div
                key={alert.id}
                className="recent-alert-row"
                initial={{
                  opacity: 0,
                  y: 8,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  delay:
                    0.5 + index * 0.07,
                }}
              >
                <span
                  className={`alert-severity-marker alert-${severityClass}`}
                />

                <div className="alert-content">
                  <div>
                    <strong>
                      {alert.machine_name}
                    </strong>

                    <span
                      className={`alert-severity alert-severity-${severityClass}`}
                    >
                      {formatSeverity(
                        alert.severity,
                      )}
                    </span>
                  </div>

                  <p>
                    {alert.message}
                  </p>

                  <span className="alert-time">
                    {formatRelativeTime(
                      alert.created_at,
                    )}
                  </span>
                </div>

                <button
                  type="button"
                  className="alert-open-button"
                  aria-label={
                    `Open alerts for ${alert.machine_name}`
                  }
                  onClick={() => {
                    navigate('/alerts')
                  }}
                >
                  <ArrowUpRight size={15} />
                </button>
              </motion.div>
            )
          })}
      </div>
    </motion.article>
  )
}