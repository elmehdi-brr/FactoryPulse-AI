import {
  BrainCircuit,
  Clock3,
  TriangleAlert,
  Wrench,
} from 'lucide-react'
import { motion } from 'motion/react'

import type {
  DashboardNeedsAttention,
} from '../../types/dashboard'

type NeedsAttentionPanelProps = {
  item: DashboardNeedsAttention | null
  loading?: boolean
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
    return `${Math.round(seconds / 60)} min`
  }

  const hours = seconds / 3600

  if (hours < 24) {
    return `${hours.toFixed(1)}h`
  }

  const days = hours / 24

  return `${days.toFixed(1)}d`
}

function formatReasonPercentage(
  value: number | null,
): string {
  if (value === null) {
    return '—'
  }

  return `${Math.round(value * 100)}%`
}

export function NeedsAttentionPanel({
  item,
  loading = false,
}: NeedsAttentionPanelProps) {
  const reasonPercentage =
    item?.dominant_reason_percentage ?? null

  const reasonWidth =
    reasonPercentage !== null
      ? `${Math.min(
          Math.max(reasonPercentage * 100, 0),
          100,
        )}%`
      : '0%'

  return (
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
            Operational intelligence
          </span>

          <h2>Needs attention</h2>
        </div>

        <BrainCircuit size={20} />
      </div>

      {loading ? (
        <div className="dashboard-panel-state">
          Evaluating factory priority...
        </div>
      ) : item === null ? (
        <div className="dashboard-panel-state">
          No operational concern detected.
        </div>
      ) : (
        <>
          <div className="attention-machine">
            <div className="attention-rank">
              #{item.priority_rank}
            </div>

            <div>
              <strong>
                {item.machine_name}
              </strong>

              <span>
                {item.production_line_name}
                {' · '}
                {item.machine_code}
              </span>
            </div>
          </div>

          <div className="attention-reasons">
            <div>
              <TriangleAlert size={16} />

              <span>
                Recorded downtime{' '}
                <strong>
                  {formatDuration(
                    item.recorded_downtime_seconds,
                  )}
                </strong>
              </span>
            </div>

            <div>
              <Clock3 size={16} />

              <span>
                MTTR{' '}
                <strong>
                  {formatDuration(
                    item.mttr_seconds,
                  )}
                </strong>
              </span>
            </div>

            <div>
              <Wrench size={16} />

              <span>
                Failures{' '}
                <strong>
                  {item.failure_count}
                </strong>
              </span>
            </div>

            <div>
              <BrainCircuit size={16} />

              <span>
                MTBF{' '}
                <strong>
                  {formatDuration(
                    item.mtbf_seconds,
                  )}
                </strong>
              </span>
            </div>
          </div>

          <div className="reason-breakdown">
            <div className="reason-header">
              <span>
                {item.dominant_reason
                  ?? 'No recorded downtime reason'}
              </span>

              <strong>
                {formatReasonPercentage(
                  reasonPercentage,
                )}
              </strong>
            </div>

            <div className="reason-track">
              <motion.div
                className="reason-fill"
                initial={{
                  width: 0,
                }}
                animate={{
                  width: reasonWidth,
                }}
                transition={{
                  duration: 0.9,
                  delay: 0.55,
                }}
              />
            </div>

            <span className="reason-subtitle">
              Dominant recorded downtime reason
            </span>
          </div>
        </>
      )}
    </motion.article>
  )
}