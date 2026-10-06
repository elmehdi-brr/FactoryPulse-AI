import {
  Activity,
  BellRing,
  Cpu,
  MapPin,
  RefreshCw,
  ShieldAlert,
  TriangleAlert,
  CheckCircle2,
  Clock3,
  Wrench,
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
  getMachineMaintenanceEffectiveness,
  getMachineMaintenanceRecords,
  getMachineOperationalIntelligence,
  getMachinePredictions,
  getMachineReliability,
  getMachineSensors,
  getMachineTelemetry,
  getMachines,
} from '../services/machines'
import type {
  Machine,
  MachineMaintenanceEffectiveness,
  MachineMaintenanceRecord,
  MachineOperationalIntelligence,
  MachinePredictions,
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

function formatAnomalyScore(
  score: number | null,
): string {
  if (score === null) {
    return '—'
  }

  return score.toFixed(2)
}

function formatPredictionStatus(
  isAnomaly: boolean,
): string {
  return isAnomaly
    ? 'Anomaly detected'
    : 'Normal prediction'
}

function formatMaintenanceDate(
  value: string | null,
): string {
  if (!value) {
    return 'Not performed'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown'
  }

  return date.toLocaleDateString(
    [],
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    },
  )
}

function formatRate(
  value: number | null,
): string {
  if (value === null) {
    return '—'
  }

  return `${(value * 100).toFixed(1)}%`
}

function formatMaintenanceType(
  type: MachineMaintenanceRecord[
    'maintenance_type'
  ],
): string {
  return type === 'preventive'
    ? 'Preventive'
    : 'Corrective'
}

function formatMaintenanceRecordStatus(
  status: MachineMaintenanceRecord[
    'status'
  ],
): string {
  return status
    .replace('_', ' ')
    .replace(
      /^\w/,
      (character) => character.toUpperCase(),
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
    selectedMachineMaintenanceRecords,
    setSelectedMachineMaintenanceRecords,
  ] = useState<MachineMaintenanceRecord[] | null>(
    null,
  )

  const [
    loadingMaintenanceRecords,
    setLoadingMaintenanceRecords,
  ] = useState(false)

  const [
    maintenanceRecordsError,
    setMaintenanceRecordsError,
  ] = useState<string | null>(null)

  const [
    selectedMachineMaintenanceEffectiveness,
    setSelectedMachineMaintenanceEffectiveness,
  ] = useState<MachineMaintenanceEffectiveness | null>(
    null,
  )

  const [
    loadingMaintenanceEffectiveness,
    setLoadingMaintenanceEffectiveness,
  ] = useState(false)

  const [
    maintenanceEffectivenessError,
    setMaintenanceEffectivenessError,
  ] = useState<string | null>(null)

  const [
    telemetryError,
    setTelemetryError,
  ] = useState<string | null>(null)

  const [
    selectedMachinePredictions,
    setSelectedMachinePredictions,
  ] = useState<MachinePredictions | null>(null)

  const [
    loadingPredictions,
    setLoadingPredictions,
  ] = useState(false)

  const [
    predictionError,
    setPredictionError,
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

  useEffect(() => {
    if (selectedMachineId === null) {
      return
    }

    const machineId =
      selectedMachineId

    let cancelled = false

    async function loadMachinePredictions() {
      setLoadingPredictions(true)
      setPredictionError(null)
      setSelectedMachinePredictions(null)

      try {
        const response =
          await getMachinePredictions(
            machineId,
            20,
          )

        if (!cancelled) {
          setSelectedMachinePredictions(
            response,
          )
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setPredictionError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load machine predictions.',
        )

        setSelectedMachinePredictions(null)
      } finally {
        if (!cancelled) {
          setLoadingPredictions(false)
        }
      }
    }

    void loadMachinePredictions()

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

    async function loadMachineMaintenanceRecords() {
      setLoadingMaintenanceRecords(true)
      setMaintenanceRecordsError(null)
      setSelectedMachineMaintenanceRecords(null)

      try {
        const response =
          await getMachineMaintenanceRecords(
            machineId,
          )

        if (!cancelled) {
          setSelectedMachineMaintenanceRecords(
            response,
          )
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setMaintenanceRecordsError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load machine maintenance records.',
        )

        setSelectedMachineMaintenanceRecords(
          null,
        )
      } finally {
        if (!cancelled) {
          setLoadingMaintenanceRecords(
            false,
          )
        }
      }
    }

    void loadMachineMaintenanceRecords()

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

    async function loadMachineMaintenanceEffectiveness() {
      setLoadingMaintenanceEffectiveness(true)
      setMaintenanceEffectivenessError(null)
      setSelectedMachineMaintenanceEffectiveness(
        null,
      )

      try {
        const response =
          await getMachineMaintenanceEffectiveness(
            machineId,
          )

        if (!cancelled) {
          setSelectedMachineMaintenanceEffectiveness(
            response,
          )
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setMaintenanceEffectivenessError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load machine maintenance effectiveness.',
        )

        setSelectedMachineMaintenanceEffectiveness(
          null,
        )
      } finally {
        if (!cancelled) {
          setLoadingMaintenanceEffectiveness(
            false,
          )
        }
      }
    }

    void loadMachineMaintenanceEffectiveness()

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
                  
                  <div className="machine-ai">
                    <div className="machine-ai-header">
                      <div>
                        <span className="panel-eyebrow">
                          AI intelligence
                        </span>

                        <h3>
                          Recent predictions
                        </h3>
                      </div>

                      <span className="machine-ai-count">
                        {selectedMachinePredictions?.predictions.length ?? 0}
                      </span>
                    </div>

                    {loadingPredictions && (
                      <div className="dashboard-panel-state">
                        Loading AI predictions...
                      </div>
                    )}

                    {!loadingPredictions
                      && predictionError && (
                        <div
                          className="dashboard-data-error"
                          role="alert"
                        >
                          <RefreshCw size={16} />

                          <div>
                            <strong>
                              AI predictions unavailable
                            </strong>

                            <span>
                              {predictionError}
                            </span>
                          </div>
                        </div>
                      )}

                    {!loadingPredictions
                      && !predictionError
                      && selectedMachinePredictions
                      && selectedMachinePredictions.predictions.length === 0 && (
                        <div className="machine-ai-empty">
                          <Activity size={18} />

                          <div>
                            <strong>
                              No predictions yet
                            </strong>

                            <span>
                              This machine does not have
                              recent AI predictions.
                            </span>
                          </div>
                        </div>
                      )}

                    {!loadingPredictions
                      && !predictionError
                      && selectedMachinePredictions
                      && selectedMachinePredictions.predictions.length > 0 && (
                        <>
                          <div className="machine-ai-summary">
                            <div className="machine-ai-summary-item">
                              <span>
                                Recent predictions
                              </span>

                              <strong>
                                {
                                  selectedMachinePredictions
                                    .predictions.length
                                }
                              </strong>
                            </div>

                            <div className="machine-ai-summary-item">
                              <span>
                                Anomalies
                              </span>

                              <strong>
                                {
                                  selectedMachinePredictions
                                    .predictions.filter(
                                      (prediction) =>
                                        prediction.is_anomaly,
                                    )
                                    .length
                                }
                              </strong>
                            </div>
                          </div>

                          <div className="machine-prediction-list">
                            {selectedMachinePredictions.predictions
                              .slice(0, 6)
                              .map(
                                (
                                  prediction,
                                  index,
                                ) => (
                                  <motion.article
                                    key={
                                      prediction.prediction_id
                                    }
                                    className={`machine-prediction-item ${
                                      prediction.is_anomaly
                                        ? 'machine-prediction-item-anomaly'
                                        : ''
                                    }`}
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
                                        index * 0.04,
                                    }}
                                  >
                                    <div className="machine-prediction-main">
                                      <div className="machine-prediction-sensor">
                                        <span>
                                          {
                                            prediction.sensor_type
                                          }
                                        </span>

                                        <strong>
                                          {
                                            prediction.sensor_name
                                          }
                                        </strong>
                                      </div>

                                      <span
                                        className={
                                          prediction.is_anomaly
                                            ? 'machine-prediction-status machine-prediction-status-anomaly'
                                            : 'machine-prediction-status'
                                        }
                                      >
                                        {formatPredictionStatus(
                                          prediction.is_anomaly,
                                        )}
                                      </span>
                                    </div>

                                    <div className="machine-prediction-metrics">
                                      <div>
                                        <span>
                                          Predicted
                                        </span>

                                        <strong>
                                          {prediction.predicted_value}{' '}
                                          {
                                            prediction.unit
                                          }
                                        </strong>
                                      </div>

                                      <div>
                                        <span>
                                          Score
                                        </span>

                                        <strong>
                                          {formatAnomalyScore(
                                            prediction.anomaly_score,
                                          )}
                                        </strong>
                                      </div>

                                      <div>
                                        <span>
                                          Model
                                        </span>

                                        <strong>
                                          {
                                            prediction.model_name
                                          }
                                          {prediction.model_version
                                            ? ` v${prediction.model_version}`
                                            : ''}
                                        </strong>
                                      </div>

                                      <div>
                                        <span>
                                          Predicted at
                                        </span>

                                        <strong>
                                          {formatTelemetryTime(
                                            prediction.predicted_at,
                                          )}
                                        </strong>
                                      </div>
                                    </div>
                                  </motion.article>
                                ),
                              )}
                          </div>

                          {selectedMachinePredictions.predictions.length > 6 && (
                            <p className="machine-ai-note">
                              Showing the 6 most recent predictions
                              from the latest{' '}
                              {
                                selectedMachinePredictions
                                  .predictions.length
                              }{' '}
                              returned.
                            </p>
                          )}
                        </>
                      )}
                  </div>
                  <div className="machine-maintenance">
                    <div className="machine-maintenance-header">
                      <div>
                        <span className="panel-eyebrow">
                          Maintenance
                        </span>

                        <h3>
                          Maintenance effectiveness
                        </h3>
                      </div>

                      <Wrench size={18} />
                    </div>

                    {loadingMaintenanceEffectiveness && (
                      <div className="dashboard-panel-state">
                        Loading maintenance analytics...
                      </div>
                    )}

                    {!loadingMaintenanceEffectiveness
                      && maintenanceEffectivenessError && (
                        <div
                          className="dashboard-data-error"
                          role="alert"
                        >
                          <Wrench size={16} />

                          <div>
                            <strong>
                              Maintenance analytics unavailable
                            </strong>

                            <span>
                              {
                                maintenanceEffectivenessError
                              }
                            </span>
                          </div>
                        </div>
                      )}

                    {!loadingMaintenanceEffectiveness
                      && !maintenanceEffectivenessError
                      && selectedMachineMaintenanceEffectiveness
                      && (
                        <div className="machine-maintenance-metrics">
                          <div className="machine-maintenance-metric">
                            <span>
                              Total records
                            </span>

                            <strong>
                              {
                                selectedMachineMaintenanceEffectiveness.total_records
                              }
                            </strong>
                          </div>

                          <div className="machine-maintenance-metric">
                            <span>
                              Preventive share
                            </span>

                            <strong>
                              {formatRate(
                                selectedMachineMaintenanceEffectiveness
                                  .preventive_share,
                              )}
                            </strong>
                          </div>

                          <div className="machine-maintenance-metric">
                            <span>
                              Completion
                            </span>

                            <strong>
                              {formatRate(
                                selectedMachineMaintenanceEffectiveness
                                  .completion_rate,
                              )}
                            </strong>
                          </div>

                          <div className="machine-maintenance-metric">
                            <span>
                              Verification
                            </span>

                            <strong>
                              {formatRate(
                                selectedMachineMaintenanceEffectiveness
                                  .verification_rate,
                              )}
                            </strong>
                          </div>

                          <div className="machine-maintenance-metric">
                            <span>
                              Alert response
                            </span>

                            <strong>
                              {formatRate(
                                selectedMachineMaintenanceEffectiveness
                                  .response_rate,
                              )}
                            </strong>
                          </div>
                        </div>
                      )}

                    <div className="machine-maintenance-history">
                      <div className="machine-maintenance-history-header">
                        <div>
                          <span className="panel-eyebrow">
                            Recent activity
                          </span>

                          <h3>
                            Maintenance history
                          </h3>
                        </div>

                        <span className="machine-maintenance-count">
                          {selectedMachineMaintenanceRecords?.length ?? 0}
                        </span>
                      </div>

                      {loadingMaintenanceRecords && (
                        <div className="dashboard-panel-state">
                          Loading maintenance history...
                        </div>
                      )}

                      {!loadingMaintenanceRecords
                        && maintenanceRecordsError && (
                          <div
                            className="dashboard-data-error"
                            role="alert"
                          >
                            <Wrench size={16} />

                            <div>
                              <strong>
                                Maintenance history unavailable
                              </strong>

                              <span>
                                {
                                  maintenanceRecordsError
                                }
                              </span>
                            </div>
                          </div>
                        )}

                      {!loadingMaintenanceRecords
                        && !maintenanceRecordsError
                        && selectedMachineMaintenanceRecords
                        && selectedMachineMaintenanceRecords.length === 0 && (
                          <div className="machine-maintenance-empty">
                            <Wrench size={18} />

                            <div>
                              <strong>
                                No maintenance records
                              </strong>

                              <span>
                                No maintenance activity has
                                been recorded for this machine.
                              </span>
                            </div>
                          </div>
                        )}

                      {!loadingMaintenanceRecords
                        && !maintenanceRecordsError
                        && selectedMachineMaintenanceRecords
                        && selectedMachineMaintenanceRecords.length > 0 && (
                          <div className="machine-maintenance-list">
                            {selectedMachineMaintenanceRecords
                              .slice(0, 6)
                              .map(
                                (
                                  record,
                                  index,
                                ) => (
                                  <motion.article
                                    key={record.id}
                                    className="machine-maintenance-item"
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
                                        index * 0.04,
                                    }}
                                  >
                                    <div className="machine-maintenance-icon">
                                      {record.status ===
                                        'completed'
                                        || record.status ===
                                          'verified' ? (
                                        <CheckCircle2 size={17} />
                                      ) : (
                                        <Clock3 size={17} />
                                      )}
                                    </div>

                                    <div className="machine-maintenance-main">
                                      <div className="machine-maintenance-title">
                                        <strong>
                                          {
                                            record.description
                                          }
                                        </strong>

                                        <span
                                          className={`machine-maintenance-status machine-maintenance-status-${record.status}`}
                                        >
                                          {formatMaintenanceRecordStatus(
                                            record.status,
                                          )}
                                        </span>
                                      </div>

                                      <div className="machine-maintenance-meta">
                                        <span>
                                          {formatMaintenanceType(
                                            record.maintenance_type,
                                          )}
                                        </span>

                                        <span>
                                          {formatMaintenanceDate(
                                            record.performed_at,
                                          )}
                                        </span>

                                        <span>
                                          {record.alert_id !==
                                          null
                                            ? 'Alert linked'
                                            : 'No alert linked'}
                                        </span>
                                      </div>
                                    </div>
                                  </motion.article>
                                ),
                              )}
                          </div>
                        )}

                      {selectedMachineMaintenanceRecords
                        && selectedMachineMaintenanceRecords.length > 6 && (
                        <p className="machine-maintenance-note">
                          Showing the 6 most recent records.
                        </p>
                      )}
                    </div>
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