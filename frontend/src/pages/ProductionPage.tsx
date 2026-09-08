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
  getProductionLineOperationalTrends,
  getProductionLineRuns,
  getProductionLines,
} from '../services/production'
import type {
  ProductionLine,
  ProductionLineDowntime,
  ProductionLineOEE,
  ProductionLineOperationalTrends,
  ProductionRun,
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

function formatTrendValue(
  value: number | null,
  type: 'percentage' | 'hours' | 'count',
): string {
  if (value === null) {
    return '—'
  }

  if (type === 'percentage') {
    return formatPercentage(value)
  }

  if (type === 'hours') {
    return formatHours(value)
  }

  return value.toLocaleString()
}

function trendLabel(
  direction:
    | 'improved'
    | 'worsened'
    | 'unchanged'
    | 'not_comparable',
): string {
  switch (direction) {
    case 'improved':
      return 'Improved'
    case 'worsened':
      return 'Worsened'
    case 'unchanged':
      return 'Unchanged'
    case 'not_comparable':
      return 'Not comparable'
  }
}

function trendClassName(
  direction:
    | 'improved'
    | 'worsened'
    | 'unchanged'
    | 'not_comparable',
): string {
  switch (direction) {
    case 'improved':
      return 'production-trend-positive'
    case 'worsened':
      return 'production-trend-negative'
    case 'unchanged':
      return 'production-trend-neutral'
    case 'not_comparable':
      return 'production-trend-neutral'
  }
}

function formatTrendDelta(
  delta: number | null,
  type: 'percentage' | 'hours' | 'count',
): string {
  if (delta === null) {
    return '—'
  }

  const sign = delta > 0 ? '+' : ''

  if (type === 'percentage') {
    return `${sign}${(delta * 100).toFixed(1)} pp`
  }

  if (type === 'hours') {
    return `${sign}${(delta / 3600).toFixed(1)}h`
  }

  return `${sign}${delta.toLocaleString()}`
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
    selectedLineTrends,
    setSelectedLineTrends,
  ] = useState<ProductionLineOperationalTrends | null>(
    null,
  )

  const [
    selectedLineRuns,
    setSelectedLineRuns,
  ] = useState<ProductionRun[] | null>(
    null,
  )

  const [
    loadingRuns,
    setLoadingRuns,
  ] = useState(false)

  const [
    runsError,
    setRunsError,
  ] = useState<string | null>(null)

  const [
    loadingTrends,
    setLoadingTrends,
  ] = useState(false)

  const [
    trendsError,
    setTrendsError,
  ] = useState<string | null>(null)

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

  useEffect(() => {
    if (selectedLineId === null) {
      return
    }

    const lineId = selectedLineId
    let cancelled = false

    async function loadSelectedLineTrends() {
      setLoadingTrends(true)
      setTrendsError(null)
      setSelectedLineTrends(null)

      try {
        const response =
          await getProductionLineOperationalTrends(
            lineId,
          )

        if (!cancelled) {
          setSelectedLineTrends(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        if (
          requestError instanceof ApiError
        ) {
          setTrendsError(
            requestError.message,
          )
        } else {
          setTrendsError(
            'Unable to load operational trends.',
          )
        }

        setSelectedLineTrends(null)
      } finally {
        if (!cancelled) {
          setLoadingTrends(false)
        }
      }
    }

    void loadSelectedLineTrends()

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

    async function loadSelectedLineRuns() {
      setLoadingRuns(true)
      setRunsError(null)
      setSelectedLineRuns(null)

      try {
        const response =
          await getProductionLineRuns(
            lineId,
          )

        if (!cancelled) {
          setSelectedLineRuns(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        if (
          requestError instanceof ApiError
        ) {
          setRunsError(
            requestError.message,
          )
        } else {
          setRunsError(
            'Unable to load production runs.',
          )
        }

        setSelectedLineRuns(null)
      } finally {
        if (!cancelled) {
          setLoadingRuns(false)
        }
      }
    }

    void loadSelectedLineRuns()

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

        {selectedLine && (
          <section className="production-trends">
            <div className="production-section-header">
              <div>
                <span className="panel-eyebrow">
                  Operational intelligence
                </span>

                <h2>
                  Operational trends
                </h2>
              </div>
            </div>

            {loadingTrends && (
              <div className="dashboard-panel-state">
                Loading operational trends...
              </div>
            )}

            {!loadingTrends && trendsError && (
              <div
                className="dashboard-data-error"
                role="alert"
              >
                <RefreshCw size={17} />

                <div>
                  <strong>
                    Operational trends unavailable
                  </strong>

                  <span>
                    {trendsError}
                  </span>
                </div>
              </div>
            )}

            {!loadingTrends
              && !trendsError
              && selectedLineTrends
              && (
                <>
                  <div className="production-trend-periods">
                    <div>
                      <span>
                        Current period
                      </span>

                      <strong>
                        {new Date(
                          selectedLineTrends
                            .current_period
                            .start_at,
                        ).toLocaleDateString()}
                        {' '}
                        –
                        {' '}
                        {new Date(
                          selectedLineTrends
                            .current_period
                            .end_at,
                        ).toLocaleDateString()}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Previous period
                      </span>

                      <strong>
                        {new Date(
                          selectedLineTrends
                            .previous_period
                            .start_at,
                        ).toLocaleDateString()}
                        {' '}
                        –
                        {' '}
                        {new Date(
                          selectedLineTrends
                            .previous_period
                            .end_at,
                        ).toLocaleDateString()}
                      </strong>
                    </div>
                  </div>

                  <div className="production-trend-grid">
                    {[
                      {
                        label: 'OEE',
                        trend:
                          selectedLineTrends
                            .trends.oee,
                        type: 'percentage' as const,
                      },
                      {
                        label: 'Availability',
                        trend:
                          selectedLineTrends
                            .trends.availability,
                        type: 'percentage' as const,
                      },
                      {
                        label: 'Performance',
                        trend:
                          selectedLineTrends
                            .trends.performance,
                        type: 'percentage' as const,
                      },
                      {
                        label: 'Quality',
                        trend:
                          selectedLineTrends
                            .trends.quality,
                        type: 'percentage' as const,
                      },
                      {
                        label: 'Downtime',
                        trend:
                          selectedLineTrends
                            .trends.recorded_downtime,
                        type: 'hours' as const,
                      },
                      {
                        label: 'Failures',
                        trend:
                          selectedLineTrends
                            .trends.total_failure_count,
                        type: 'count' as const,
                      },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="production-trend-card"
                      >
                        <span>
                          {item.label}
                        </span>

                        <strong>
                          {formatTrendValue(
                            item.trend.current_value,
                            item.type,
                          )}
                        </strong>

                        <div
                          className={trendClassName(
                            item.trend.direction,
                          )}
                        >
                          <span>
                            {trendLabel(
                              item.trend.direction,
                            )}
                          </span>

                          <strong>
                            {formatTrendDelta(
                              item.trend.delta,
                              item.type,
                            )}
                          </strong>
                        </div>

                        <small>
                          Previous:{' '}
                          {formatTrendValue(
                            item.trend.previous_value,
                            item.type,
                          )}
                        </small>
                      </div>
                    ))}
                  </div>

                  <div className="production-machine-trends">
                    <div className="production-subsection-header">
                      <h3>
                        Machine reliability trends
                      </h3>
                    </div>

                    {selectedLineTrends.trends
                      .machines.length === 0 ? (
                      <div className="dashboard-panel-state">
                        No machine trend data available.
                      </div>
                    ) : (
                      <div className="production-machine-trend-list">
                        {selectedLineTrends.trends
                          .machines.map((machine) => (
                            <div
                              key={machine.machine_id}
                              className="production-machine-trend-row"
                            >
                              <div className="production-machine-trend-identity">
                                <strong>
                                  {machine.machine_name}
                                </strong>

                                <span>
                                  {machine.machine_code}
                                </span>
                              </div>

                              <div className="production-machine-trend-metrics">
                                <div>
                                  <span>
                                    Downtime
                                  </span>

                                  <strong
                                    className={trendClassName(
                                      machine
                                        .recorded_downtime
                                        .direction,
                                    )}
                                  >
                                    {formatTrendDelta(
                                      machine
                                        .recorded_downtime
                                        .delta,
                                      'hours',
                                    )}
                                  </strong>
                                </div>

                                <div>
                                  <span>
                                    Failures
                                  </span>

                                  <strong
                                    className={trendClassName(
                                      machine
                                        .failure_count
                                        .direction,
                                    )}
                                  >
                                    {formatTrendDelta(
                                      machine
                                        .failure_count
                                        .delta,
                                      'count',
                                    )}
                                  </strong>
                                </div>

                                <div>
                                  <span>
                                    MTTR
                                  </span>

                                  <strong
                                    className={trendClassName(
                                      machine.mttr
                                        .direction,
                                    )}
                                  >
                                    {formatTrendDelta(
                                      machine.mttr.delta,
                                      'hours',
                                    )}
                                  </strong>
                                </div>

                                <div>
                                  <span>
                                    MTBF
                                  </span>

                                  <strong
                                    className={trendClassName(
                                      machine.mtbf
                                        .direction,
                                    )}
                                  >
                                    {formatTrendDelta(
                                      machine.mtbf.delta,
                                      'hours',
                                    )}
                                  </strong>
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </>
              )}
          </section>
        )}

        {selectedLine && (
          <section className="production-runs">
            <div className="production-section-header">
              <div>
                <span className="panel-eyebrow">
                  Production activity
                </span>

                <h2>
                  Production runs
                </h2>
              </div>
            </div>

            {loadingRuns && (
              <div className="dashboard-panel-state">
                Loading production runs...
              </div>
            )}

            {!loadingRuns && runsError && (
              <div
                className="dashboard-data-error"
                role="alert"
              >
                <RefreshCw size={17} />

                <div>
                  <strong>
                    Production runs unavailable
                  </strong>

                  <span>
                    {runsError}
                  </span>
                </div>
              </div>
            )}

            {!loadingRuns
              && !runsError
              && selectedLineRuns
              && selectedLineRuns.length === 0 && (
                <div className="dashboard-panel-state">
                  No production runs recorded for this line.
                </div>
              )}

            {!loadingRuns
              && !runsError
              && selectedLineRuns
              && selectedLineRuns.length > 0 && (
                <div className="production-runs-list">
                  {selectedLineRuns.map((run) => {
                    const durationSeconds =
                      run.ended_at
                        ? (
                            new Date(
                              run.ended_at,
                            ).getTime()
                            - new Date(
                              run.started_at,
                            ).getTime()
                          ) / 1000
                        : null

                    return (
                      <div
                        key={run.id}
                        className="production-run-row"
                      >
                        <div className="production-run-main">
                          <div className="production-run-heading">
                            <strong>
                              Run #{run.id}
                            </strong>

                            <span
                              className={`production-run-status production-run-status-${run.status}`}
                            >
                              {run.status}
                            </span>
                          </div>

                          <span>
                            Started{' '}
                            {new Date(
                              run.started_at,
                            ).toLocaleString()}
                          </span>

                          {run.ended_at && (
                            <span>
                              Ended{' '}
                              {new Date(
                                run.ended_at,
                              ).toLocaleString()}
                            </span>
                          )}
                        </div>

                        <div className="production-run-metrics">
                          <div>
                            <span>
                              Target
                            </span>

                            <strong>
                              {run.target_quantity
                                ?? '—'}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Total
                            </span>

                            <strong>
                              {run.total_quantity}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Good
                            </span>

                            <strong>
                              {run.good_quantity}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Reject
                            </span>

                            <strong>
                              {run.reject_quantity}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Duration
                            </span>

                            <strong>
                              {durationSeconds === null
                                ? 'Running'
                                : formatHours(
                                    durationSeconds,
                                  )}
                            </strong>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
          </section>
        )}
      </section>
    </div>
  )
}