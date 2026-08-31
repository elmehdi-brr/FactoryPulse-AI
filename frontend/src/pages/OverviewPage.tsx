import {
  TriangleAlert,
} from 'lucide-react'
import { motion } from 'motion/react'
import {
  useEffect,
  useState,
} from 'react'

import { NeedsAttentionPanel } from '../components/dashboard/NeedsAttentionPanel'
import { MachineHealthPanel } from '../components/dashboard/MachineHealthPanel'
import { ProductionLinesPanel } from '../components/dashboard/ProductionLinesPanel'
import { RecentAlertsPanel } from '../components/dashboard/RecentAlertsPanel'
import { EfficiencyTrendPanel } from '../components/dashboard/EfficiencyTrendPanel'
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
        <EfficiencyTrendPanel
          points={
            overview?.efficiency_trend
            ?? []
          }
          loading={loading}
        />

        <NeedsAttentionPanel
          item={
            overview?.needs_attention
            ?? null
          }
          loading={loading}
        />
      </section>

      <section className="command-center-grid">
        <ProductionLinesPanel
          lines={
            overview?.production_lines ?? []
          }
          loading={loading}
        />

        <div className="command-center-side">
          <MachineHealthPanel
            health={
            overview?.machine_health
            ?? null
            }
            loading={loading}
          />

          <RecentAlertsPanel
            alerts={
              overview?.recent_alerts
              ?? []
            }
            loading={loading}
          />
        </div>
      </section>
    </div>
  )
}