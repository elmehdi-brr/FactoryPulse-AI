import {
  Activity,
  BellRing,
  Cpu,
  MapPin,
  RefreshCw,
  ShieldAlert,
  TriangleAlert,
} from 'lucide-react'
import {
  motion,
} from 'motion/react'
import {
  useEffect,
  useState,
} from 'react'

import { ApiError } from '../services/api'
import {
  getMachineOperationalIntelligence,
  getMachineReliability,
  getMachineSensors,
  getMachineTelemetry,
  getMachines,
} from '../services/machines'
import type {
  Machine,
  MachineOperationalIntelligence,
  MachineReliability,
  MachineSensor,
  MachineTelemetry,
} from '../types/machine'

type PanelFailure = {
  kind: 'empty' | 'error'
  message: string
}

function formatStatus(
  status: string,
): string {
  const normalized =
    status.trim().toLowerCase()

  if (!normalized) {
    return 'Unknown'
  }

  return normalized
    .charAt(0)
    .toUpperCase()
    + normalized.slice(1)
}

function formatCreatedAt(
  value: string,
): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown'
  }

  return date.toLocaleDateString()
}

function formatHours(
  seconds: number | null,
): string {
  if (seconds === null) {
    return '—'
  }

  return `${(seconds / 3600).toFixed(1)}h`
}

function formatDuration(
  seconds: number | null,
): string {
  if (seconds === null) {
    return '—'
  }

  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }

  if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)}m`
  }

  return `${(seconds / 3600).toFixed(1)}h`
}

function describeReliabilityFailure(
  requestError: unknown,
): PanelFailure {
  if (requestError instanceof ApiError) {
    return {
      kind:
        requestError.status === 422
          ? 'empty'
          : 'error',
      message:
        requestError.message,
    }
  }

  return {
    kind: 'error',
    message:
      'Unable to load machine reliability.',
  }
}

function describeOperationalIntelligenceFailure(
  requestError: unknown,
): PanelFailure {
  if (requestError instanceof ApiError) {
    return {
      kind:
        requestError.status === 422
          ? 'empty'
          : 'error',
      message:
        requestError.message,
    }
  }

  return {
    kind: 'error',
    message:
      'Unable to load machine operational intelligence.',
  }
}

function formatHealthStatus(
  status: MachineOperationalIntelligence[
    'health_status'
  ],
): string {
  if (status === 'critical') {
    return 'Critical'
  }

  if (status === 'attention') {
    return 'Needs attention'
  }

  return 'Healthy'
}

function formatTelemetryValue(
  value: number,
  unit: string,
): string {
  const formattedValue =
    Number.isInteger(value)
      ? String(value)
      : value.toFixed(1)

  return `${formattedValue} ${unit}`
}

function formatTelemetryTime(
  value: string,
): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown time'
  }

  return date.toLocaleTimeString(
    [],
    {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    },
  )
}

  export function MachinesPage() {
  const [
    machines,
    setMachines,
  ] = useState<Machine[] | null>(null)

  const [
    selectedMachineId,
    setSelectedMachineId,
  ] = useState<number | null>(null)

  const [
    selectedMachineReliability,
    setSelectedMachineReliability,
  ] = useState<MachineReliability | null>(
    null,
  )

  const [
    selectedMachineOperationalIntelligence,
    setSelectedMachineOperationalIntelligence,
  ] = useState<MachineOperationalIntelligence | null>(
    null,
  )

  const [
    loadingOperationalIntelligence,
    setLoadingOperationalIntelligence,
  ] = useState(false)

  const [
    operationalIntelligenceError,
    setOperationalIntelligenceError,
  ] = useState<PanelFailure | null>(null)

  const [
    loadingReliability,
    setLoadingReliability,
  ] = useState(false)

  const [
    reliabilityError,
    setReliabilityError,
  ] = useState<PanelFailure | null>(
    null,
  )

  const [
    selectedMachineSensors,
    setSelectedMachineSensors,
  ] = useState<MachineSensor[] | null>(null)

  const [
    loadingSensors,
    setLoadingSensors,
  ] = useState(false)

  const [
    sensorError,
    setSensorError,
  ] = useState<string | null>(null)

  const [
    error,
    setError,
  ] = useState<string | null>(null)

  const [
    selectedMachineTelemetry,
    setSelectedMachineTelemetry,
  ] = useState<MachineTelemetry | null>(null)

  const [
    loadingTelemetry,
    setLoadingTelemetry,
  ] = useState(false)

  const [
    telemetryError,
    setTelemetryError,
  ] = useState<string | null>(null)

  const loading =
    machines === null
    && error === null

  useEffect(() => {
    let cancelled = false

    async function loadMachines() {
      try {
        const response =
          await getMachines()

        if (!cancelled) {
          setMachines(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        if (
          requestError instanceof ApiError
        ) {
          setError(
            requestError.message,
          )
        } else {
          setError(
            'Unable to load machines.',
          )
        }
      }
    }

    void loadMachines()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (selectedMachineId === null) {
      return
    }

    const machineId =
      selectedMachineId

    let cancelled = false

    async function loadMachineReliability() {
      setLoadingReliability(true)
      setReliabilityError(null)
      setSelectedMachineReliability(
        null,
      )

      try {
        const response =
          await getMachineReliability(
            machineId,
          )

        if (!cancelled) {
          setSelectedMachineReliability(
            response,
          )
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setReliabilityError(
          describeReliabilityFailure(
            requestError,
          ),
        )

        setSelectedMachineReliability(
          null,
        )
      } finally {
        if (!cancelled) {
          setLoadingReliability(false)
        }
      }
    }

    void loadMachineReliability()

    return () => {
      cancelled = true
    }
  }, [selectedMachineId])

  useEffect(() => {
    if (selectedMachineId === null) {
      return
    }

    const machineId =
      selectedMachineId

    let cancelled = false

    async function loadMachineOperationalIntelligence() {
      setLoadingOperationalIntelligence(true)
      setOperationalIntelligenceError(null)
      setSelectedMachineOperationalIntelligence(
        null,
      )

      try {
        const response =
          await getMachineOperationalIntelligence(
            machineId,
          )

        if (!cancelled) {
          setSelectedMachineOperationalIntelligence(
            response,
          )
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setOperationalIntelligenceError(
          describeOperationalIntelligenceFailure(
            requestError,
          ),
        )

        setSelectedMachineOperationalIntelligence(
          null,
        )
      } finally {
        if (!cancelled) {
          setLoadingOperationalIntelligence(false)
        }
      }
    }

    void loadMachineOperationalIntelligence()

    return () => {
      cancelled = true
    }
  }, [selectedMachineId])

  useEffect(() => {
    if (selectedMachineId === null) {
      return
    }

    const machineId =
      selectedMachineId

    let cancelled = false

    async function loadMachineSensors() {
      setLoadingSensors(true)
      setSensorError(null)
      setSelectedMachineSensors(null)

      try {
        const response =
          await getMachineSensors(machineId)

        if (!cancelled) {
          setSelectedMachineSensors(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setSensorError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load machine sensors.',
        )

        setSelectedMachineSensors(null)
      } finally {
        if (!cancelled) {
          setLoadingSensors(false)
        }
      }
    }

    void loadMachineSensors()

    return () => {
      cancelled = true
    }
  }, [selectedMachineId])


  useEffect(() => {
    if (selectedMachineId === null) {
      return
    }

    const machineId =
      selectedMachineId

    let cancelled = false

    async function loadMachineTelemetry() {
      setLoadingTelemetry(true)
      setTelemetryError(null)
      setSelectedMachineTelemetry(null)

      try {
        const response =
          await getMachineTelemetry(
            machineId,
            12,
          )

        if (!cancelled) {
          setSelectedMachineTelemetry(
            response,
          )
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setTelemetryError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load machine telemetry.',
        )

        setSelectedMachineTelemetry(null)
      } finally {
        if (!cancelled) {
          setLoadingTelemetry(false)
        }
      }
    }

    void loadMachineTelemetry()

    return () => {
      cancelled = true
    }
  }, [selectedMachineId])
  const selectedMachine =
    machines?.find(
      (machine) =>
        machine.id === selectedMachineId,
    ) ?? null

  return (
    <div className="machines-page">
      <section className="page-heading">
        <div>
          <p className="page-eyebrow">
            Asset Intelligence
          </p>

          <h1>
            Machines.
          </h1>

          <p>
            Explore industrial assets,
            their factory context, and
            operational status.
          </p>
        </div>

        <div className="live-indicator">
          <span />
          Connected
        </div>
      </section>

      {error && (
        <motion.div
          className="dashboard-data-error"
          role="alert"
          initial={{
            opacity: 0,
            y: -6,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
        >
          <RefreshCw size={17} />

          <div>
            <strong>
              Machine data unavailable
            </strong>

            <span>
              {error}
            </span>
          </div>
        </motion.div>
      )}

      <section className="machines-browser">
        <div className="production-section-header">
          <div>
            <span className="panel-eyebrow">
              Factory assets
            </span>

            <h2>
              Machine inventory
            </h2>
          </div>

          <Cpu size={20} />
        </div>

        {loading && (
          <div className="dashboard-panel-state">
            Loading machines...
          </div>
        )}

        {!loading
          && machines?.length === 0 && (
            <div className="dashboard-panel-state">
              No machines available.
            </div>
        )}

        {!loading
          && machines
          && machines.length > 0 && (
            <div className="machines-layout">
              <div className="machines-list">
                {machines.map(
                  (machine, index) => (
                    <motion.button
                      key={machine.id}
                      type="button"
                      className={
                        selectedMachineId
                          === machine.id
                          ? 'machine-list-item machine-list-item-active'
                          : 'machine-list-item'
                      }
                      onClick={() => {
                        setSelectedMachineId(
                          machine.id,
                        )
                      }}
                      initial={{
                        opacity: 0,
                        y: 10,
                      }}
                      animate={{
                        opacity: 1,
                        y: 0,
                      }}
                      transition={{
                        delay:
                          index * 0.04,
                      }}
                    >
                      <div className="machine-list-item-main">
                        <span className="machine-list-item-code">
                          {machine.code}
                        </span>

                        <strong>
                          {machine.name}
                        </strong>

                        <span className="machine-list-item-context">
                          {machine.production_line_id
                            === null
                            ? 'Standalone asset'
                            : `Production line #${machine.production_line_id}`}
                        </span>
                      </div>

                      <span
                        className={`machine-status machine-status-${machine.status.trim().toLowerCase()}`}
                      >
                        {formatStatus(
                          machine.status,
                        )}
                      </span>
                    </motion.button>
                  ),
                )}
              </div>

              {selectedMachine ? (
                <motion.section
                  className="machine-details"
                  key={selectedMachine.id}
                  initial={{
                    opacity: 0,
                    x: 12,
                  }}
                  animate={{
                    opacity: 1,
                    x: 0,
                  }}
                  transition={{
                    duration: 0.2,
                  }}
                >
                  <div className="machine-details-header">
                    <div>
                      <span className="panel-eyebrow">
                        Selected machine
                      </span>

                      <h2>
                        {selectedMachine.name}
                      </h2>

                      <span className="machine-details-code">
                        {selectedMachine.code}
                      </span>
                    </div>

                    <Activity size={20} />
                  </div>

                  <div className="machine-details-status">
                    <span>
                      Current status
                    </span>

                    <strong
                      className={`machine-status machine-status-${selectedMachine.status.trim().toLowerCase()}`}
                    >
                      {formatStatus(
                        selectedMachine.status,
                      )}
                    </strong>
                  </div>

                  <div className="machine-details-grid">
                    <div>
                      <span>
                        Area
                      </span>

                      <strong>
                        Area #{selectedMachine.area_id}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Production line
                      </span>

                      <strong>
                        {selectedMachine
                          .production_line_id
                          === null
                          ? 'Standalone'
                          : `Line #${selectedMachine.production_line_id}`}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Location
                      </span>

                      <strong>
                        {selectedMachine.location
                          ?? 'Not specified'}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Added
                      </span>

                      <strong>
                        {formatCreatedAt(
                          selectedMachine.created_at,
                        )}
                      </strong>
                    </div>
                  </div>

                  {selectedMachine.location && (
                    <div className="machine-location">
                      <MapPin size={16} />

                      <span>
                        {selectedMachine.location}
                      </span>
                    </div>
                  )}
                  <div className="machine-operational-intelligence">
                    <div className="machine-operational-intelligence-header">
                      <div>
                        <span className="panel-eyebrow">
                          Operational intelligence
                        </span>

                        <h3>
                          Health &amp; operational impact
                        </h3>
                      </div>

                      <ShieldAlert size={18} />
                    </div>

                    {loadingOperationalIntelligence && (
                      <div className="dashboard-panel-state">
                        Loading operational intelligence...
                      </div>
                    )}

                    {!loadingOperationalIntelligence
                      && operationalIntelligenceError
                        ?.kind === 'empty' && (
                        <div className="dashboard-panel-state">
                          {
                            operationalIntelligenceError.message
                          }
                        </div>
                      )}

                    {!loadingOperationalIntelligence
                      && operationalIntelligenceError
                        ?.kind === 'error' && (
                        <div
                          className="dashboard-data-error"
                          role="alert"
                        >
                          <RefreshCw size={16} />

                          <div>
                            <strong>
                              Operational data unavailable
                            </strong>

                            <span>
                              {
                                operationalIntelligenceError.message
                              }
                            </span>
                          </div>
                        </div>
                      )}

                    {!loadingOperationalIntelligence
                      && !operationalIntelligenceError
                      && selectedMachineOperationalIntelligence
                      && (
                        <>
                          <div className="machine-health-summary">
                            <div
                              className={`machine-health-status machine-health-status-${selectedMachineOperationalIntelligence.health_status}`}
                            >
                              {selectedMachineOperationalIntelligence.health_status ===
                                'critical' ? (
                                <ShieldAlert size={20} />
                              ) : selectedMachineOperationalIntelligence.health_status ===
                                'attention' ? (
                                <TriangleAlert size={20} />
                              ) : (
                                <Activity size={20} />
                              )}

                              <div>
                                <span>
                                  Current health
                                </span>

                                <strong>
                                  {formatHealthStatus(
                                    selectedMachineOperationalIntelligence.health_status,
                                  )}
                                </strong>
                              </div>
                            </div>

                            <div className="machine-health-alerts">
                              <div>
                                <BellRing size={16} />

                                <span>
                                  Open alerts
                                </span>

                                <strong>
                                  {
                                    selectedMachineOperationalIntelligence.open_alert_count
                                  }
                                </strong>
                              </div>

                              <div>
                                <ShieldAlert size={16} />

                                <span>
                                  Critical
                                </span>

                                <strong>
                                  {
                                    selectedMachineOperationalIntelligence.critical_alert_count
                                  }
                                </strong>
                              </div>

                              <div>
                                <TriangleAlert size={16} />

                                <span>
                                  Attention
                                </span>

                                <strong>
                                  {
                                    selectedMachineOperationalIntelligence.attention_alert_count
                                  }
                                </strong>
                              </div>
                            </div>
                          </div>

                          <div className="machine-impact-grid">
                            <div className="machine-impact-card">
                              <span>
                                Downtime
                              </span>

                              <strong>
                                {formatHours(
                                  selectedMachineOperationalIntelligence
                                    .operational_impact
                                    ?.recorded_downtime_seconds
                                    ?? 0,
                                )}
                              </strong>

                              <small>
                                Recorded machine downtime
                              </small>
                            </div>

                            <div className="machine-impact-card">
                              <span>
                                Downtime share
                              </span>

                              <strong>
                                {selectedMachineOperationalIntelligence
                                  .operational_impact
                                  ?.recorded_downtime_share ===
                                  null
                                  || selectedMachineOperationalIntelligence
                                      .operational_impact ===
                                    null
                                  || selectedMachineOperationalIntelligence
                                      .operational_impact ===
                                    undefined
                                  ? '—'
                                  : `${(
                                      selectedMachineOperationalIntelligence
                                        .operational_impact
                                        .recorded_downtime_share * 100
                                    ).toFixed(1)}%`}
                              </strong>

                              <small>
                                Share of line downtime
                              </small>
                            </div>

                            <div className="machine-impact-card">
                              <span>
                                Operational priority
                              </span>

                              <strong>
                                {selectedMachineOperationalIntelligence
                                  .operational_priority
                                  ?.priority_rank
                                  ?? '—'}
                              </strong>

                              <small>
                                Position within production line
                              </small>
                            </div>

                            <div className="machine-impact-card">
                              <span>
                                Failure events
                              </span>

                              <strong>
                                {
                                  selectedMachineOperationalIntelligence.failure_count
                                }
                              </strong>

                              <small>
                                Recorded reliability failures
                              </small>
                            </div>
                          </div>
                        </>
                      )}
                  </div>
                  
                  <div className="machine-sensors">
                    <div className="machine-sensors-header">
                      <div>
                        <span className="panel-eyebrow">
                          Telemetry
                        </span>

                        <h3>
                          Connected sensors
                        </h3>
                      </div>

                      <span className="machine-sensor-count">
                        {selectedMachineSensors?.length ?? 0}
                      </span>
                    </div>

                    {loadingSensors && (
                      <div className="dashboard-panel-state">
                        Loading sensors...
                      </div>
                    )}

                    {!loadingSensors && sensorError && (
                      <div
                        className="dashboard-data-error"
                        role="alert"
                      >
                        <RefreshCw size={16} />

                        <div>
                          <strong>
                            Sensor data unavailable
                          </strong>

                          <span>
                            {sensorError}
                          </span>
                        </div>
                      </div>
                    )}

                    {!loadingSensors
                      && !sensorError
                      && selectedMachineSensors
                      && selectedMachineSensors.length === 0 && (
                        <div className="machine-sensors-empty">
                          <Cpu size={18} />

                          <div>
                            <strong>
                              No sensors connected
                            </strong>

                            <span>
                              This machine does not have
                              any telemetry sensors registered.
                            </span>
                          </div>
                        </div>
                      )}

                    {!loadingSensors
                      && !sensorError
                      && selectedMachineSensors
                      && selectedMachineSensors.length > 0 && (
                        <div className="machine-sensor-list">
                          {selectedMachineSensors.map(
                            (sensor, index) => (
                              <motion.div
                                key={sensor.id}
                                className="machine-sensor-item"
                                initial={{
                                  opacity: 0,
                                  y: 8,
                                }}
                                animate={{
                                  opacity: 1,
                                  y: 0,
                                }}
                                transition={{
                                  delay: index * 0.04,
                                }}
                              >
                                <div className="machine-sensor-icon">
                                  <Activity size={17} />
                                </div>

                                <div className="machine-sensor-main">
                                  <strong>
                                    {sensor.name}
                                  </strong>

                                  <span>
                                    {sensor.sensor_type}
                                  </span>
                                </div>

                                <div className="machine-sensor-unit">
                                  <span>
                                    Unit
                                  </span>

                                  <strong>
                                    {sensor.unit}
                                  </strong>
                                </div>

                                <span
                                  className={`machine-sensor-status machine-sensor-status-${sensor.status.trim().toLowerCase()}`}
                                >
                                  {formatStatus(
                                    sensor.status,
                                  )}
                                </span>
                              </motion.div>
                            ),
                          )}
                        </div>
                      )}
                  </div>
                  
                  <div className="machine-telemetry">
                    <div className="machine-telemetry-header">
                      <div>
                        <span className="panel-eyebrow">
                          Live telemetry
                        </span>

                        <h3>
                          Sensor readings
                        </h3>
                      </div>

                      <Activity size={18} />
                    </div>

                    {loadingTelemetry && (
                      <div className="dashboard-panel-state">
                        Loading telemetry...
                      </div>
                    )}

                    {!loadingTelemetry
                      && telemetryError && (
                        <div
                          className="dashboard-data-error"
                          role="alert"
                        >
                          <RefreshCw size={16} />

                          <div>
                            <strong>
                              Telemetry unavailable
                            </strong>

                            <span>
                              {telemetryError}
                            </span>
                          </div>
                        </div>
                      )}

                    {!loadingTelemetry
                      && !telemetryError
                      && selectedMachineTelemetry
                      && selectedMachineTelemetry.sensors.length === 0 && (
                        <div className="machine-telemetry-empty">
                          <Activity size={18} />

                          <div>
                            <strong>
                              No telemetry available
                            </strong>

                            <span>
                              The machine has no registered
                              sensor readings yet.
                            </span>
                          </div>
                        </div>
                      )}

                    {!loadingTelemetry
                      && !telemetryError
                      && selectedMachineTelemetry
                      && selectedMachineTelemetry.sensors.length > 0 && (
                        <div className="machine-telemetry-grid">
                          {selectedMachineTelemetry.sensors.map(
                            (sensor, index) => {
                              const readings = [
                                ...sensor.recent_readings,
                              ].reverse()

                              const values =
                                readings.map(
                                  (reading) =>
                                    reading.value,
                                )

                              const minValue =
                                values.length > 0
                                  ? Math.min(...values)
                                  : 0

                              const maxValue =
                                values.length > 0
                                  ? Math.max(...values)
                                  : 1

                              const range =
                                maxValue - minValue || 1

                              const points =
                                readings.map(
                                  (reading, readingIndex) => {
                                    const x =
                                      readings.length === 1
                                        ? 50
                                        : (
                                            readingIndex
                                            / (
                                                readings.length -
                                                1
                                              )
                                          ) * 100

                                    const y =
                                      88 -
                                      (
                                        (
                                          reading.value -
                                          minValue
                                        ) /
                                        range
                                      ) * 76

                                    return `${x},${y}`
                                  },
                                )

                              const latestReading =
                                sensor.latest_reading

                              return (
                                <motion.article
                                  key={sensor.sensor_id}
                                  className="machine-telemetry-card"
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
                                      index * 0.05,
                                  }}
                                >
                                  <div className="machine-telemetry-card-header">
                                    <div>
                                      <span>
                                        {sensor.sensor_type}
                                      </span>

                                      <strong>
                                        {sensor.name}
                                      </strong>
                                    </div>

                                    <span
                                      className={`machine-sensor-status machine-sensor-status-${sensor.status.trim().toLowerCase()}`}
                                    >
                                      {formatStatus(
                                        sensor.status,
                                      )}
                                    </span>
                                  </div>

                                  <div className="machine-telemetry-reading">
                                    <div>
                                      <span>
                                        Current value
                                      </span>

                                      <strong>
                                        {latestReading
                                          ? formatTelemetryValue(
                                              latestReading.value,
                                              sensor.unit,
                                            )
                                          : '—'}
                                      </strong>
                                    </div>

                                    <span>
                                      {latestReading
                                        ? formatTelemetryTime(
                                            latestReading.recorded_at,
                                          )
                                        : 'No reading yet'}
                                    </span>
                                  </div>

                                  {values.length > 0 && (
                                    <div className="machine-telemetry-chart">
                                      <svg
                                        viewBox="0 0 100 100"
                                        role="img"
                                        aria-label={`${sensor.name} recent telemetry trend`}
                                      >
                                        <polyline
                                          points={points.join(' ')}
                                          fill="none"
                                          stroke="currentColor"
                                          strokeWidth="2.5"
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                        />
                                      </svg>

                                      <div className="machine-telemetry-chart-meta">
                                        <span>
                                          {values.length}{' '}
                                          recent readings
                                        </span>

                                        <span>
                                          {sensor.unit}
                                        </span>
                                      </div>
                                    </div>
                                  )}
                                </motion.article>
                              )
                            },
                          )}
                        </div>
                      )}
                  </div>

                  <div className="machine-reliability">
                    <div className="machine-reliability-header">
                      <div>
                        <span className="panel-eyebrow">
                          Reliability
                        </span>

                        <h3>
                          Machine performance
                        </h3>
                      </div>

                      <Activity size={18} />
                    </div>

                    {loadingReliability && (
                      <div className="dashboard-panel-state">
                        Loading reliability...
                      </div>
                    )}

                    {!loadingReliability
                      && reliabilityError
                        ?.kind === 'empty' && (
                        <div className="dashboard-panel-state">
                          {reliabilityError.message}
                        </div>
                    )}

                    {!loadingReliability
                      && reliabilityError
                        ?.kind === 'error' && (
                        <div
                          className="dashboard-data-error"
                          role="alert"
                        >
                          <RefreshCw size={16} />

                          <div>
                            <strong>
                              Reliability unavailable
                            </strong>

                            <span>
                              {reliabilityError.message}
                            </span>
                          </div>
                        </div>
                    )}

                    {!loadingReliability
                      && !reliabilityError
                      && selectedMachineReliability
                      && (
                        <div className="machine-reliability-grid">
                          <div className="machine-reliability-card">
                            <span>
                              Failures
                            </span>

                            <strong>
                              {selectedMachineReliability
                                .failure_count}
                            </strong>
                          </div>

                          <div className="machine-reliability-card">
                            <span>
                              Failure downtime
                            </span>

                            <strong>
                              {formatHours(
                                selectedMachineReliability
                                  .total_failure_downtime_seconds,
                              )}
                            </strong>
                          </div>

                          <div className="machine-reliability-card">
                            <span>
                              MTTR
                            </span>

                            <strong>
                              {formatDuration(
                                selectedMachineReliability
                                  .mttr_seconds,
                              )}
                            </strong>
                          </div>

                          <div className="machine-reliability-card">
                            <span>
                              MTBF
                            </span>

                            <strong>
                              {formatDuration(
                                selectedMachineReliability
                                  .mtbf_seconds,
                              )}
                            </strong>
                          </div>

                          <div className="machine-reliability-card machine-reliability-card-wide">
                            <span>
                              Operating exposure
                            </span>

                            <strong>
                              {formatHours(
                                selectedMachineReliability
                                  .operating_exposure_seconds,
                              )}
                            </strong>
                          </div>
                        </div>
                    )}
                  </div>
                </motion.section>
              ) : (
                <div className="machine-details machine-details-empty">
                  <Cpu size={22} />

                  <div>
                    <strong>
                      Select a machine
                    </strong>

                    <span>
                      Choose an asset from the
                      inventory to inspect its
                      factory context and
                      reliability.
                    </span>
                  </div>
                </div>
              )}
            </div>
        )}
      </section>
    </div>
  )
}