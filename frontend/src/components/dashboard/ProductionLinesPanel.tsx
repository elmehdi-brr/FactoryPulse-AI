import {
  Factory,
} from 'lucide-react'
import { motion } from 'motion/react'

import type {
  DashboardProductionLineSummary,
} from '../../types/dashboard'

type ProductionLinesPanelProps = {
  lines: DashboardProductionLineSummary[]
  loading?: boolean
}

function formatPercentage(
  value: number | null,
): string {
  if (value === null) {
    return '—'
  }

  return `${(value * 100).toFixed(1)}%`
}

export function ProductionLinesPanel({
  lines,
  loading = false,
}: ProductionLinesPanelProps) {
  return (
    <motion.article
      className="panel production-lines-panel"
      initial={{
        opacity: 0,
        y: 22,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: 0.34,
      }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            Production network
          </span>

          <h2>Production lines</h2>
        </div>

        <Factory size={20} />
      </div>

      <div className="production-line-list">
        {loading && (
          <div className="dashboard-panel-state">
            Loading production data...
          </div>
        )}

        {!loading && lines.length === 0 && (
          <div className="dashboard-panel-state">
            No production lines available.
          </div>
        )}

        {!loading
          && lines.map((line, index) => {
            const hasMetrics =
              line.oee !== null
              || line.availability !== null

            return (
              <motion.div
                key={line.id}
                className="production-line-row"
                initial={{
                  opacity: 0,
                  x: -10,
                }}
                animate={{
                  opacity: 1,
                  x: 0,
                }}
                transition={{
                  delay:
                    0.4 + index * 0.07,
                }}
                whileHover={{
                  x: 3,
                }}
              >
                <div className="line-identity">
                  <div
                    className={`line-status-indicator ${
                      hasMetrics
                        ? ''
                        : 'line-status-attention'
                    }`}
                  />

                  <div>
                    <strong>
                      {line.name}
                    </strong>

                    <span>
                      {line.code}
                    </span>
                  </div>
                </div>

                <div className="line-state">
                  <span
                    className={`status-pill ${
                      hasMetrics
                        ? 'status-pill-healthy'
                        : 'status-pill-warning'
                    }`}
                  >
                    {hasMetrics
                      ? 'Measured'
                      : 'No data'}
                  </span>
                </div>

                <div className="line-oee">
                  <span>OEE</span>

                  <strong>
                    {formatPercentage(
                      line.oee,
                    )}
                  </strong>
                </div>

                <div className="line-trend line-availability">
                  <span>
                    Availability
                  </span>

                  <strong>
                    {formatPercentage(
                      line.availability,
                    )}
                  </strong>
                </div>
              </motion.div>
            )
          })}
      </div>
    </motion.article>
  )
}