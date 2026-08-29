import {
  BrainCircuit,
  Clock3,
  Gauge,
  TriangleAlert,
} from 'lucide-react'
import { motion } from 'motion/react'
import {
  useEffect,
  useState,
} from 'react'

import { MachineHealthPanel } from '../components/dashboard/MachineHealthPanel'
import { ProductionLinesPanel } from '../components/dashboard/ProductionLinesPanel'
import { RecentAlertsPanel } from '../components/dashboard/RecentAlertsPanel'
import { ApiError } from '../services/api'
import {
  getDashboardOverview,
} from '../services/dashboard'
import type {
  DashboardOverviewResponse,
} from '../types/dashboard'

function formatPercentage(
  value: number | null,
): string {
  if (value === null) {
    return '—'
  }

  return `${(value * 100).toFixed(1)}%`
}

function formatHours(
  seconds: number | null,
): string {
  if (seconds === null) {
    return '—'
  }

  return `${(seconds / 3600).toFixed(1)}h`
}

export function OverviewPage() {
  const [
    overview,
    setOverview,
  ] = useState<DashboardOverviewResponse | null>(
    null,
  )

  const [
    error,
    setError,
  ] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadOverview() {
      try {
        const response =
          await getDashboardOverview()

        if (!cancelled) {
          setOverview(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        if (requestError instanceof ApiError) {
          setError(requestError.message)
        } else {
          setError(
            'Unable to load the operational overview.',
          )
        }
      }
    }

    void loadOverview()

    return () => {
      cancelled = true
    }
  }, [])

  const loading =
    overview === null && error === null

  const metrics = [
    {
      label: 'Overall OEE',
      value: loading
        ? '…'
        : formatPercentage(
            overview?.kpis.overall_oee
              ?? null,
          ),
      detail: 'Current operational snapshot',
    },
    {
      label: 'Availability',
      value: loading
        ? '…'
        : formatPercentage(
            overview?.kpis.availability
              ?? null,
          ),
      detail: 'Across completed production runs',
    },
    {
      label: 'Active alerts',
      value: loading
        ? '…'
        : String(
            overview?.kpis
              .active_alert_count
            ?? 0,
          ),
      detail: 'Open alerts requiring attention',
    },
    {
      label: 'Fleet MTBF',
      value: loading
        ? '…'
        : formatHours(
            overview?.kpis
              .fleet_mtbf_seconds
            ?? null,
          ),
      detail: 'Valid machine operating exposure',
    },
  ]

  return (
    <div className="overview-page">
      <section className="page-heading">
        <div>
          <p className="page-eyebrow">
            Operational Command Center
          </p>

          <h1>Factory overview.</h1>

          <p>
            Current production, reliability,
            and operational performance.
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
          <TriangleAlert size={17} />

          <div>
            <strong>
              Operational data unavailable
            </strong>

            <span>
              {error}
            </span>
          </div>
        </motion.div>
      )}

      <section className="metric-grid">
        {metrics.map((metric, index) => (
          <motion.article
            key={metric.label}
            className="metric-card"
            initial={{
              opacity: 0,
              y: 18,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              delay: 0.05 * index,
              duration: 0.4,
            }}
            whileHover={{
              y: -3,
            }}
          >
            <span className="metric-label">
              {metric.label}
            </span>

            <div className="metric-value-row">
              <strong>
                {metric.value}
              </strong>
            </div>

            <span className="metric-detail">
              {metric.detail}
            </span>
          </motion.article>
        ))}
      </section>

      <section className="overview-grid">
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
                Production performance · Preview
              </span>

              <h2>Line efficiency</h2>
            </div>

            <Gauge size={20} />
          </div>

          <div className="chart-placeholder">
            <div className="chart-grid-lines" />

            <svg
              viewBox="0 0 700 220"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <defs>
                <linearGradient
                  id="areaGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor="rgba(53, 208, 127, 0.35)"
                  />

                  <stop
                    offset="100%"
                    stopColor="rgba(53, 208, 127, 0)"
                  />
                </linearGradient>
              </defs>

              <path
                className="chart-area"
                d="M0,170 C70,145 90,160 145,125 C205,87 230,135 285,102 C340,69 375,92 425,73 C480,53 505,87 555,54 C610,23 650,52 700,25 L700,220 L0,220 Z"
              />

              <motion.path
                className="chart-line"
                d="M0,170 C70,145 90,160 145,125 C205,87 230,135 285,102 C340,69 375,92 425,73 C480,53 505,87 555,54 C610,23 650,52 700,25"
                initial={{
                  pathLength: 0,
                  opacity: 0,
                }}
                animate={{
                  pathLength: 1,
                  opacity: 1,
                }}
                transition={{
                  duration: 1.4,
                  delay: 0.4,
                  ease: 'easeOut',
                }}
              />
            </svg>

            <div className="chart-axis">
              <span>06:00</span>
              <span>09:00</span>
              <span>12:00</span>
              <span>15:00</span>
              <span>18:00</span>
              <span>Now</span>
            </div>
          </div>
        </motion.article>

        <motion.article
          className="panel attention-panel"
          initial={{
            opacity: 0,
            y: 22,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            delay: 0.28,
          }}
        >
          <div className="panel-header">
            <div>
              <span className="panel-eyebrow">
                Operational intelligence · Preview
              </span>

              <h2>Needs attention</h2>
            </div>

            <BrainCircuit size={20} />
          </div>

          <div className="attention-machine">
            <div className="attention-rank">
              #1
            </div>

            <div>
              <strong>Press M-101</strong>
              <span>Assembly Line A</span>
            </div>
          </div>

          <div className="attention-reasons">
            <div>
              <TriangleAlert size={16} />

              <span>
                Highest downtime burden
              </span>
            </div>

            <div>
              <Clock3 size={16} />

              <span>
                MTTR 47 minutes
              </span>
            </div>
          </div>

          <div className="reason-breakdown">
            <div className="reason-header">
              <span>
                Motor overheating
              </span>

              <strong>63%</strong>
            </div>

            <div className="reason-track">
              <motion.div
                className="reason-fill"
                initial={{
                  width: 0,
                }}
                animate={{
                  width: '63%',
                }}
                transition={{
                  duration: 0.9,
                  delay: 0.55,
                }}
              />
            </div>

            <span className="reason-subtitle">
              dominant recorded downtime reason
            </span>
          </div>
        </motion.article>
      </section>

      <section className="command-center-grid">
        <ProductionLinesPanel
          lines={
            overview?.production_lines ?? []
          }
          loading={loading}
        />

        <div className="command-center-side">
          <MachineHealthPanel />
          <RecentAlertsPanel />
        </div>
      </section>
    </div>
  )
}