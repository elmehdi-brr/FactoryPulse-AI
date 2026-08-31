import {
  Gauge,
} from 'lucide-react'
import {
  motion,
} from 'motion/react'

import type {
  DashboardEfficiencyTrendPoint,
} from '../../types/dashboard'

type EfficiencyTrendPanelProps = {
  points: DashboardEfficiencyTrendPoint[]
  loading?: boolean
}

function formatPercentage(
  value: number,
): string {
  return `${(value * 100).toFixed(1)}%`
}

function formatTime(
  value: string,
): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '—'
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(date)
}

export function EfficiencyTrendPanel({
  points,
  loading = false,
}: EfficiencyTrendPanelProps) {
  return (
    <motion.article
      className="panel production-panel"
      initial={{
        opacity: 0,
        y: 22,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: 0.22,
      }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            Production performance
          </span>

          <h2>Line efficiency</h2>
        </div>

        <Gauge size={20} />
      </div>

      {loading ? (
        <div className="dashboard-panel-state">
          Loading efficiency trend...
        </div>
      ) : points.length === 0 ? (
        <div className="dashboard-panel-state">
          No completed production runs available
          for the efficiency trend.
        </div>
      ) : (
        <div className="efficiency-trend">
          <div className="efficiency-trend-summary">
            <div>
              <span>
                Latest OEE
              </span>

              <strong>
                {formatPercentage(
                  points[points.length - 1].oee,
                )}
              </strong>
            </div>

            <div>
              <span>
                Data points
              </span>

              <strong>
                {points.length}
              </strong>
            </div>
          </div>

          <div
            className="efficiency-chart"
            role="img"
            aria-label="Factory OEE trend across completed production runs"
          >
            <svg
              viewBox="0 0 700 240"
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient
                  id="efficiencyAreaGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor="rgba(53, 208, 127, 0.30)"
                  />

                  <stop
                    offset="100%"
                    stopColor="rgba(53, 208, 127, 0)"
                  />
                </linearGradient>
              </defs>

              {points.length === 1 ? (
                <motion.circle
                  className="efficiency-chart-point"
                  cx="350"
                  cy="100"
                  r="5"
                  initial={{
                    opacity: 0,
                    scale: 0,
                  }}
                  animate={{
                    opacity: 1,
                    scale: 1,
                  }}
                  transition={{
                    duration: 0.5,
                  }}
                />
              ) : (
                (() => {
                  const width = 700
                  const height = 190
                  const topPadding = 15
                  const bottomPadding = 35

                  const minOee = Math.min(
                    ...points.map(
                      (point) => point.oee,
                    ),
                  )

                  const maxOee = Math.max(
                    ...points.map(
                      (point) => point.oee,
                    ),
                  )

                  const range =
                    Math.max(
                      maxOee - minOee,
                      0.08,
                    )

                  const paddedMin =
                    Math.max(
                      0,
                      minOee - range * 0.18,
                    )

                  const paddedMax =
                    Math.min(
                      1,
                      maxOee + range * 0.18,
                    )

                  const valueRange =
                    Math.max(
                      paddedMax - paddedMin,
                      0.05,
                    )

                  const chartPoints =
                    points.map(
                      (point, index) => {
                        const x =
                          (index
                            / (points.length - 1))
                          * width

                        const y =
                          topPadding
                          + (
                            1
                            - (
                              (point.oee
                                - paddedMin)
                              / valueRange
                            )
                          )
                          * (
                            height
                            - topPadding
                            - bottomPadding
                          )

                        return {
                          ...point,
                          x,
                          y,
                        }
                      },
                    )

                  const linePath =
                    chartPoints
                      .map(
                        (point, index) =>
                          `${index === 0 ? 'M' : 'L'}${point.x},${point.y}`,
                      )
                      .join(' ')

                  const areaPath =
                    `${linePath} L${width},${height - bottomPadding} L0,${height - bottomPadding} Z`

                  return (
                    <>
                      <path
                        className="efficiency-chart-area"
                        d={areaPath}
                      />

                      <motion.path
                        className="efficiency-chart-line"
                        d={linePath}
                        fill="none"
                        initial={{
                          pathLength: 0,
                          opacity: 0,
                        }}
                        animate={{
                          pathLength: 1,
                          opacity: 1,
                        }}
                        transition={{
                          duration: 1.15,
                          ease: 'easeOut',
                        }}
                      />

                      {chartPoints.map(
                        (point) => (
                          <motion.circle
                            key={point.end_at}
                            className="efficiency-chart-point"
                            cx={point.x}
                            cy={point.y}
                            r="3.5"
                            initial={{
                              opacity: 0,
                            }}
                            animate={{
                              opacity: 1,
                            }}
                            transition={{
                              duration: 0.3,
                            }}
                          />
                        ),
                      )}
                    </>
                  )
                })()
              )}
            </svg>

            <div className="efficiency-chart-axis">
              {points.map(
                (point) => (
                  <span
                    key={`${point.start_at}-${point.end_at}`}
                  >
                    {formatTime(
                      point.end_at,
                    )}
                  </span>
                ),
              )}
            </div>
          </div>
        </div>
      )}
    </motion.article>
  )
}