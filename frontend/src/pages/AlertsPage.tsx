
import {
  Activity,
  BellRing,
  Clock3,
  Search,
  ShieldAlert,
} from 'lucide-react'
import { motion } from 'motion/react'
import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { ApiError } from '../services/api'
import {
  getAlertSensors,
  getAlerts,
} from '../services/alerts'
import { getMachines } from '../services/machines'
import type {
  Alert,
  AlertSensorContext,
} from '../types/alert'
import type { Machine } from '../types/machine'

function normalizeValue(value: string): string {
  return value.trim().toLowerCase()
}

function formatLabel(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    )
}

function formatAlertDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown time'
  }

  return date.toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function getSeverityClass(severity: string): string {
  const normalized = normalizeValue(severity)
    .replace(/[^a-z0-9-]/g, '-')

  return `alert-severity alert-severity-${normalized}`
}

function getStatusClass(status: string): string {
  const normalized = normalizeValue(status)
    .replace(/[^a-z0-9-]/g, '-')

  return `alert-status alert-status-${normalized}`
}

type LoadState = {
  alerts: Alert[]
  sensors: AlertSensorContext[]
  machines: Machine[]
}

export function AlertsPage() {
  const [data, setData] = useState<LoadState | null>(
    null,
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(
    null,
  )

  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] =
    useState('all')
  const [statusFilter, setStatusFilter] =
    useState('all')
  const [selectedAlertId, setSelectedAlertId] =
    useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadAlertsWorkspace() {
      setLoading(true)
      setError(null)

      try {
        const [alerts, sensors, machines] =
          await Promise.all([
            getAlerts(),
            getAlertSensors(),
            getMachines(),
          ])

        if (!cancelled) {
          setData({
            alerts,
            sensors,
            machines,
          })
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load the alerts workspace.',
        )
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadAlertsWorkspace()

    return () => {
      cancelled = true
    }
  }, [])

  const sensorsById = useMemo(
    () =>
      new Map(
        (data?.sensors ?? []).map((sensor) => [
          sensor.id,
          sensor,
        ]),
      ),
    [data],
  )

  const machinesById = useMemo(
    () =>
      new Map(
        (data?.machines ?? []).map((machine) => [
          machine.id,
          machine,
        ]),
      ),
    [data],
  )

  const alerts = useMemo(
  () => data?.alerts ?? [],
  [data],
)

  const severities = useMemo(
    () =>
      [...new Set(
        alerts.map((alert) => alert.severity),
      )].sort((a, b) => a.localeCompare(b)),
    [alerts],
  )

  const statuses = useMemo(
    () =>
      [...new Set(
        alerts.map((alert) => alert.status),
      )].sort((a, b) => a.localeCompare(b)),
    [alerts],
  )

  const filteredAlerts = useMemo(() => {
    const query = normalizeValue(search)

    return [...alerts]
      .filter((alert) => {
        const sensor = sensorsById.get(
          alert.sensor_id,
        )
        const machine = sensor
          ? machinesById.get(sensor.machine_id)
          : undefined

        const matchesSearch =
          !query ||
          [
            alert.title,
            alert.message,
            alert.severity,
            alert.status,
            sensor?.name ?? '',
            sensor?.sensor_type ?? '',
            machine?.name ?? '',
            machine?.code ?? '',
          ].some((value) =>
            normalizeValue(value).includes(query),
          )

        const matchesSeverity =
          severityFilter === 'all' ||
          normalizeValue(alert.severity) ===
            normalizeValue(severityFilter)

        const matchesStatus =
          statusFilter === 'all' ||
          normalizeValue(alert.status) ===
            normalizeValue(statusFilter)

        return (
          matchesSearch &&
          matchesSeverity &&
          matchesStatus
        )
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime(),
      )
  }, [
    alerts,
    machinesById,
    search,
    sensorsById,
    severityFilter,
    statusFilter,
  ])

  const selectedAlert =
    filteredAlerts.find(
      (alert) => alert.id === selectedAlertId,
    ) ?? filteredAlerts[0] ?? null

  const selectedSensor = selectedAlert
    ? sensorsById.get(selectedAlert.sensor_id)
    : undefined

  const selectedMachine = selectedSensor
    ? machinesById.get(selectedSensor.machine_id)
    : undefined

  const openCount = alerts.filter(
    (alert) =>
      normalizeValue(alert.status) === 'open',
  ).length

  const criticalCount = alerts.filter(
    (alert) =>
      normalizeValue(alert.severity) === 'critical' &&
      normalizeValue(alert.status) === 'open',
  ).length

  const anomalyCount = alerts.filter(
    (alert) =>
      alert.prediction_id !== null &&
      normalizeValue(alert.status) === 'open',
  ).length

  return (
    <div className="alerts-page">
      <section className="page-heading">
        <div>
          <p className="page-eyebrow">
            Operational Awareness
          </p>

          <h1>Alerts.</h1>

          <p>
            Investigate active alerts, identify affected
            machines, and trace their sensor context.
          </p>
        </div>

        <div className="live-indicator">
          <span />
          Live data
        </div>
      </section>

      {error && (
        <div
          className="dashboard-data-error"
          role="alert"
        >
          <BellRing size={17} />

          <div>
            <strong>Alerts unavailable</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      <section className="alerts-summary-grid">
        <motion.article
          className="alerts-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="alerts-summary-icon">
            <BellRing size={19} />
          </div>

          <span>Open alerts</span>

          <strong>
            {loading ? '—' : openCount}
          </strong>

          <small>Alerts awaiting resolution</small>
        </motion.article>

        <motion.article
          className="alerts-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <div className="alerts-summary-icon">
            <ShieldAlert size={19} />
          </div>

          <span>Critical and open</span>

          <strong>
            {loading ? '—' : criticalCount}
          </strong>

          <small>Highest-severity active alerts</small>
        </motion.article>

        <motion.article
          className="alerts-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="alerts-summary-icon">
            <Activity size={19} />
          </div>

          <span>Prediction-linked and open</span>

          <strong>
            {loading ? '—' : anomalyCount}
          </strong>

          <small>Open alerts linked to predictions</small>
        </motion.article>
      </section>

      <section className="alerts-workspace">
        <div className="alerts-feed-panel">
          <div className="alerts-panel-header">
            <div>
              <span className="panel-eyebrow">
                Alert management
              </span>

              <h2>Alert stream</h2>
            </div>

            <span className="alerts-result-count">
              {filteredAlerts.length}
            </span>
          </div>

          <div className="alerts-toolbar">
            <label className="alerts-search">
              <Search size={17} />

              <input
                type="search"
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search alerts or machines..."
                aria-label="Search alerts or machines"
              />
            </label>

            <div className="alerts-filter-row">
              <label>
                <span>Severity</span>

                <select
                  value={severityFilter}
                  onChange={(event) =>
                    setSeverityFilter(event.target.value)
                  }
                >
                  <option value="all">
                    All severities
                  </option>

                  {severities.map((severity) => (
                    <option
                      key={severity}
                      value={severity}
                    >
                      {formatLabel(severity)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>Status</span>

                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(event.target.value)
                  }
                >
                  <option value="all">
                    All statuses
                  </option>

                  {statuses.map((status) => (
                    <option
                      key={status}
                      value={status}
                    >
                      {formatLabel(status)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {loading && (
            <div className="dashboard-panel-state">
              Loading alerts and asset context...
            </div>
          )}

          {!loading && !error && filteredAlerts.length === 0 && (
            <div className="alerts-empty">
              <BellRing size={23} />

              <strong>No matching alerts</strong>

              <span>
                Try changing the search or filters.
              </span>
            </div>
          )}

          {!loading && !error && filteredAlerts.length > 0 && (
            <div className="alerts-list">
              {filteredAlerts.map((alert, index) => {
                const sensor = sensorsById.get(
                  alert.sensor_id,
                )
                const machine = sensor
                  ? machinesById.get(sensor.machine_id)
                  : undefined

                const isSelected =
                  selectedAlert?.id === alert.id

                return (
                  <motion.button
                    key={alert.id}
                    type="button"
                    className={
                      isSelected
                        ? 'alert-list-item alert-list-item-selected'
                        : 'alert-list-item'
                    }
                    onClick={() =>
                      setSelectedAlertId(alert.id)
                    }
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      delay: Math.min(index * 0.025, 0.2),
                    }}
                  >
                    <div className="alert-list-item-top">
                      <span className={getSeverityClass(alert.severity)}>
                        {formatLabel(alert.severity)}
                      </span>

                      <span className={getStatusClass(alert.status)}>
                        {formatLabel(alert.status)}
                      </span>
                    </div>

                    <strong className="alert-list-title">
                      {alert.title}
                    </strong>

                    <span className="alert-list-message">
                      {alert.message}
                    </span>

                    <div className="alert-list-context">
                      <span>
                        {machine?.name ??
                          `Machine context unavailable`}
                      </span>

                      <span>
                        {sensor?.name ??
                          `Sensor #${alert.sensor_id}`}
                      </span>
                    </div>

                    <span className="alert-list-time">
                      <Clock3 size={13} />

                      {formatAlertDate(alert.created_at)}
                    </span>
                  </motion.button>
                )
              })}
            </div>
          )}
        </div>

        <aside className="alerts-detail-panel">
          {!selectedAlert ? (
            <div className="alerts-empty alerts-detail-empty">
              <BellRing size={23} />

              <strong>Select an alert</strong>

              <span>
                Choose an item from the alert stream to
                inspect its details.
              </span>
            </div>
          ) : (
            <motion.div
              key={selectedAlert.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="alerts-panel-header">
                <div>
                  <span className="panel-eyebrow">
                    Alert details
                  </span>

                  <h2>#{selectedAlert.id}</h2>
                </div>

                <BellRing size={20} />
              </div>

              <div className="alert-detail-badges">
                <span
                  className={getSeverityClass(
                    selectedAlert.severity,
                  )}
                >
                  {formatLabel(selectedAlert.severity)}
                </span>

                <span
                  className={getStatusClass(
                    selectedAlert.status,
                  )}
                >
                  {formatLabel(selectedAlert.status)}
                </span>
              </div>

              <h3 className="alert-detail-title">
                {selectedAlert.title}
              </h3>

              <p className="alert-detail-message">
                {selectedAlert.message}
              </p>

              <div className="alert-detail-section">
                <span className="panel-eyebrow">
                  Asset context
                </span>

                <div className="alert-detail-row">
                  <span>Machine</span>

                  <strong>
                    {selectedMachine?.name ??
                      'Unavailable'}
                  </strong>
                </div>

                <div className="alert-detail-row">
                  <span>Machine code</span>

                  <strong>
                    {selectedMachine?.code ?? '—'}
                  </strong>
                </div>

                <div className="alert-detail-row">
                  <span>Sensor</span>

                  <strong>
                    {selectedSensor?.name ??
                      `Sensor #${selectedAlert.sensor_id}`}
                  </strong>
                </div>

                <div className="alert-detail-row">
                  <span>Sensor type</span>

                  <strong>
                    {selectedSensor?.sensor_type ?? '—'}
                  </strong>
                </div>

                <div className="alert-detail-row">
                  <span>Sensor unit</span>

                  <strong>
                    {selectedSensor?.unit ?? '—'}
                  </strong>
                </div>
              </div>

              <div className="alert-detail-section">
                <span className="panel-eyebrow">
                  Traceability
                </span>

                <div className="alert-detail-row">
                  <span>Alert ID</span>
                  <strong>#{selectedAlert.id}</strong>
                </div>

                <div className="alert-detail-row">
                  <span>Prediction</span>

                  <strong>
                    {selectedAlert.prediction_id !== null
                      ? `#${selectedAlert.prediction_id}`
                      : 'Not linked'}
                  </strong>
                </div>

                <div className="alert-detail-row">
                  <span>Created</span>

                  <strong>
                    {formatAlertDate(
                      selectedAlert.created_at,
                    )}
                  </strong>
                </div>
              </div>
            </motion.div>
          )}
        </aside>
      </section>
    </div>
  )
}