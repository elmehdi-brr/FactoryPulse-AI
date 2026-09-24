import {
  Activity,
  Cpu,
  MapPin,
  RefreshCw,
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
  getMachineReliability,
  getMachines,
} from '../services/machines'
import type {
  Machine,
  MachineReliability,
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
    error,
    setError,
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