import {
  BarChart3,
  Factory,
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
  getProductionLineDowntime,
  getProductionLineOEE,
  getProductionLines,
} from '../services/production'
import type {
  ProductionLine,
  ProductionLineDowntime,
  ProductionLineOEE,
} from '../types/production'

function formatPercentage(
  value: number,
): string {
  return `${(value * 100).toFixed(1)}%`
}

function formatHours(
  seconds: number,
): string {
  return `${(seconds / 3600).toFixed(1)}h`
}

export function ProductionPage() {
  const [
    productionLines,
    setProductionLines,
  ] = useState<ProductionLine[] | null>(
    null,
  )

  const [
    selectedLineId,
    setSelectedLineId,
  ] = useState<number | null>(null)

  const [
    selectedLineOEE,
    setSelectedLineOEE,
  ] = useState<ProductionLineOEE | null>(
    null,
  )

  const [
    selectedLineDowntime,
    setSelectedLineDowntime,
  ] = useState<ProductionLineDowntime | null>(
    null,
  )

  const [
    loadingOEE,
    setLoadingOEE,
  ] = useState(false)

  const [
    loadingDowntime,
    setLoadingDowntime,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(null)

  const [
    oeeError,
    setOEEError,
  ] = useState<string | null>(null)

  const [
    downtimeError,
    setDowntimeError,
  ] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadProductionLines() {
      try {
        const response =
          await getProductionLines()

        if (!cancelled) {
          setProductionLines(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        if (
          requestError instanceof ApiError
        ) {
          setError(requestError.message)
        } else {
          setError(
            'Unable to load production lines.',
          )
        }
      }
    }

    void loadProductionLines()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (selectedLineId === null) {
      return
    }

    const lineId = selectedLineId
    let cancelled = false

    async function loadSelectedLineOEE() {
      setLoadingOEE(true)
      setOEEError(null)
      setSelectedLineOEE(null)

      try {
        const response =
          await getProductionLineOEE(
            lineId,
          )

        if (!cancelled) {
          setSelectedLineOEE(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        if (
          requestError instanceof ApiError
        ) {
          setOEEError(requestError.message)
        } else {
          setOEEError(
            'Unable to load line performance.',
          )
        }

        setSelectedLineOEE(null)
      } finally {
        if (!cancelled) {
          setLoadingOEE(false)
        }
      }
    }

    void loadSelectedLineOEE()

    return () => {
      cancelled = true
    }
  }, [selectedLineId])

  useEffect(() => {
    if (selectedLineId === null) {
      return
    }

    const lineId = selectedLineId
    let cancelled = false

    async function loadSelectedLineDowntime() {
      setLoadingDowntime(true)
      setDowntimeError(null)
      setSelectedLineDowntime(null)

      try {
        const response =
          await getProductionLineDowntime(
            lineId,
          )

        if (!cancelled) {
          setSelectedLineDowntime(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        if (
          requestError instanceof ApiError
        ) {
          setDowntimeError(
            requestError.message,
          )
        } else {
          setDowntimeError(
            'Unable to load downtime analytics.',
          )
        }

        setSelectedLineDowntime(null)
      } finally {
        if (!cancelled) {
          setLoadingDowntime(false)
        }
      }
    }

    void loadSelectedLineDowntime()

    return () => {
      cancelled = true
    }
  }, [selectedLineId])

  const loading =
    productionLines === null
    && error === null

  const selectedLine =
    productionLines?.find(
      (line) =>
        line.id === selectedLineId,
    ) ?? null

  return (
    <div className="production-page">
      <section className="page-heading">
        <div>
          <p className="page-eyebrow">
            Production Intelligence
          </p>

          <h1>Production.</h1>

          <p>
            Monitor production lines,
            performance, downtime, and
            operational efficiency.
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
              Production data unavailable
            </strong>

            <span>{error}</span>
          </div>
        </motion.div>
      )}

      <section className="production-lines-browser">
        <div className="production-section-header">
          <div>
            <span className="panel-eyebrow">
              Factory structure
            </span>

            <h2>
              Production lines
            </h2>
          </div>

          <Factory size={20} />
        </div>

        {loading && (
          <div className="dashboard-panel-state">
            Loading production lines...
          </div>
        )}

        {!loading
          && productionLines?.length === 0 && (
            <div className="dashboard-panel-state">
              No production lines available.
            </div>
          )}

        {!loading
          && productionLines
          && productionLines.length > 0 && (
            <div className="production-line-selector">
              {productionLines.map(
                (line, index) => (
                  <motion.button
                    key={line.id}
                    type="button"
                    className={
                      selectedLineId === line.id
                        ? 'production-line-selector-item production-line-selector-item-active'
                        : 'production-line-selector-item'
                    }
                    onClick={() => {
                      setSelectedLineId(
                        line.id,
                      )
                    }}
                    initial={{
                      opacity: 0,
                      y: 12,
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                    }}
                    transition={{
                      delay:
                        index * 0.06,
                    }}
                  >
                    <span className="production-line-selector-code">
                      {line.code}
                    </span>

                    <strong>
                      {line.name}
                    </strong>

                    <span className="production-line-selector-description">
                      {line.description
                        ?? 'No description available'}
                    </span>
                  </motion.button>
                ),
              )}
            </div>
          )}

        {selectedLine && (
          <motion.section
            className="production-selected-line"
            initial={{
              opacity: 0,
              y: 14,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
          >
            <span className="panel-eyebrow">
              Selected production line
            </span>

            <h2>
              {selectedLine.name}
            </h2>

            <span>
              {selectedLine.code}
            </span>
          </motion.section>
        )}

        {selectedLine && (
          <section className="production-performance">
            <div className="production-section-header">
              <div>
                <span className="panel-eyebrow">
                  Line performance
                </span>

                <h2>
                  OEE overview
                </h2>
              </div>
            </div>

            {loadingOEE && (
              <div className="dashboard-panel-state">
                Loading line performance...
              </div>
            )}

            {!loadingOEE && oeeError && (
              <div
                className="dashboard-data-error"
                role="alert"
              >
                <RefreshCw size={17} />

                <div>
                  <strong>
                    Performance unavailable
                  </strong>

                  <span>
                    {oeeError}
                  </span>
                </div>
              </div>
            )}

            {!loadingOEE
              && !oeeError
              && selectedLineOEE
              && (
                <>
                  <div className="production-oee-grid">
                    <div className="production-oee-card production-oee-primary">
                      <span>
                        OEE
                      </span>

                      <strong>
                        {formatPercentage(
                          selectedLineOEE.oee,
                        )}
                      </strong>
                    </div>

                    <div className="production-oee-card">
                      <span>
                        Availability
                      </span>

                      <strong>
                        {formatPercentage(
                          selectedLineOEE.availability,
                        )}
                      </strong>
                    </div>

                    <div className="production-oee-card">
                      <span>
                        Performance
                      </span>

                      <strong>
                        {formatPercentage(
                          selectedLineOEE.performance,
                        )}
                      </strong>
                    </div>

                    <div className="production-oee-card">
                      <span>
                        Quality
                      </span>

                      <strong>
                        {formatPercentage(
                          selectedLineOEE.quality,
                        )}
                      </strong>
                    </div>
                  </div>

                  <div className="production-volume-grid">
                    <div>
                      <span>
                        Completed runs
                      </span>

                      <strong>
                        {selectedLineOEE.run_count}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Total quantity
                      </span>

                      <strong>
                        {selectedLineOEE.total_quantity}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Good quantity
                      </span>

                      <strong>
                        {selectedLineOEE.good_quantity}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Operating time
                      </span>

                      <strong>
                        {formatHours(
                          selectedLineOEE.operating_time_seconds,
                        )}
                      </strong>
                    </div>
                  </div>
                </>
              )}
          </section>
        )}

        {selectedLine && (
          <section className="production-downtime">
            <div className="production-section-header">
              <div>
                <span className="panel-eyebrow">
                  Downtime analytics
                </span>

                <h2>
                  Downtime overview
                </h2>
              </div>

              <BarChart3 size={20} />
            </div>

            {loadingDowntime && (
              <div className="dashboard-panel-state">
                Loading downtime analytics...
              </div>
            )}

            {!loadingDowntime
              && downtimeError && (
                <div
                  className="dashboard-data-error"
                  role="alert"
                >
                  <RefreshCw size={17} />

                  <div>
                    <strong>
                      Downtime data unavailable
                    </strong>

                    <span>
                      {downtimeError}
                    </span>
                  </div>
                </div>
              )}

            {!loadingDowntime
              && !downtimeError
              && selectedLineDowntime
              && (
                <>
                  <div className="production-downtime-summary">
                    <div className="production-downtime-card">
                      <span>
                        Recorded downtime
                      </span>

                      <strong>
                        {formatHours(
                          selectedLineDowntime.recorded_downtime_seconds,
                        )}
                      </strong>
                    </div>

                    <div className="production-downtime-card">
                      <span>
                        Planned
                      </span>

                      <strong>
                        {formatHours(
                          selectedLineDowntime.planned_downtime_seconds,
                        )}
                      </strong>
                    </div>

                    <div className="production-downtime-card">
                      <span>
                        Unplanned
                      </span>

                      <strong>
                        {formatHours(
                          selectedLineDowntime.unplanned_downtime_seconds,
                        )}
                      </strong>
                    </div>

                    <div className="production-downtime-card">
                      <span>
                        Events
                      </span>

                      <strong>
                        {selectedLineDowntime.event_count}
                      </strong>
                    </div>
                  </div>

                  {selectedLineDowntime.event_count === 0 ? (
                    <div className="dashboard-panel-state">
                      No recorded downtime for this line.
                    </div>
                  ) : (
                    <div className="production-downtime-details">
                      <div>
                        <div className="production-subsection-header">
                          <h3>
                            Top downtime reasons
                          </h3>
                        </div>

                        {selectedLineDowntime.by_reason
                          .length === 0 ? (
                          <div className="dashboard-panel-state">
                            No downtime reasons recorded.
                          </div>
                        ) : (
                          <div className="production-breakdown-list">
                            {selectedLineDowntime.by_reason
                              .slice(0, 5)
                              .map((item) => (
                                <div
                                  key={item.reason}
                                  className="production-breakdown-row"
                                >
                                  <div>
                                    <strong>
                                      {item.reason}
                                    </strong>

                                    <span>
                                      {item.event_count}
                                      {' '}
                                      events ·{' '}
                                      {formatHours(
                                        item.duration_seconds,
                                      )}
                                    </span>
                                  </div>

                                  <strong>
                                    {formatPercentage(
                                      item.percentage,
                                    )}
                                  </strong>
                                </div>
                              ))}
                          </div>
                        )}
                      </div>

                      <div>
                        <div className="production-subsection-header">
                          <h3>
                            Machine impact
                          </h3>
                        </div>

                        {selectedLineDowntime.by_machine
                          .filter(
                            (item) =>
                              item.machine_id !== null,
                          )
                          .length === 0 ? (
                          <div className="dashboard-panel-state">
                            No machine downtime recorded.
                          </div>
                        ) : (
                          <div className="production-breakdown-list">
                            {selectedLineDowntime.by_machine
                              .filter(
                                (item) =>
                                  item.machine_id !== null,
                              )
                              .slice(0, 5)
                              .map((item) => (
                                <div
                                  key={item.machine_id}
                                  className="production-breakdown-row"
                                >
                                  <div>
                                    <strong>
                                      Machine #{item.machine_id}
                                    </strong>

                                    <span>
                                      {item.event_count}
                                      {' '}
                                      events ·{' '}
                                      {formatHours(
                                        item.duration_seconds,
                                      )}
                                    </span>
                                  </div>

                                  <strong>
                                    {formatPercentage(
                                      item.percentage,
                                    )}
                                  </strong>
                                </div>
                              ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
          </section>
        )}
      </section>
    </div>
  )
}