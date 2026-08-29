import {
  Activity,
  CircleAlert,
  CircleCheck,
  TriangleAlert,
} from 'lucide-react'
import { motion } from 'motion/react'

const machineHealth = [
  {
    label: 'Healthy',
    value: 14,
    icon: CircleCheck,
    className: 'health-healthy',
  },
  {
    label: 'Attention',
    value: 3,
    icon: TriangleAlert,
    className: 'health-attention',
  },
  {
    label: 'Critical',
    value: 1,
    icon: CircleAlert,
    className: 'health-critical',
  },
]

export function MachineHealthPanel() {
  const total = machineHealth.reduce(
    (sum, item) => sum + item.value,
    0,
  )

  return (
    <motion.article
      className="panel compact-panel machine-health-panel"
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            Asset condition
          </span>

          <h2>Machine health</h2>
        </div>

        <Activity size={20} />
      </div>

      <div className="machine-health-summary">
        <div className="health-ring">
          <svg viewBox="0 0 120 120">
            <circle
              className="health-ring-track"
              cx="60"
              cy="60"
              r="48"
            />

            <motion.circle
              className="health-ring-value"
              cx="60"
              cy="60"
              r="48"
              initial={{
                pathLength: 0,
              }}
              animate={{
                pathLength: 14 / total,
              }}
              transition={{
                duration: 1,
                delay: 0.45,
              }}
            />
          </svg>

          <div>
            <strong>{total}</strong>
            <span>machines</span>
          </div>
        </div>

        <div className="health-breakdown">
          {machineHealth.map((item) => {
            const Icon = item.icon

            return (
              <div
                key={item.label}
                className="health-item"
              >
                <div
                  className={`health-icon ${item.className}`}
                >
                  <Icon size={15} />
                </div>

                <span>{item.label}</span>

                <strong>{item.value}</strong>
              </div>
            )
          })}
        </div>
      </div>
    </motion.article>
  )
}