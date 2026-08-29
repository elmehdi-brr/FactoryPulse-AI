import {
  ArrowUpRight,
  BellRing,
} from 'lucide-react'
import { motion } from 'motion/react'

const alerts = [
  {
    severity: 'Critical',
    machine: 'Press M-101',
    message: 'Motor temperature exceeded threshold',
    time: '4 min ago',
  },
  {
    severity: 'High',
    machine: 'Conveyor M-204',
    message: 'Abnormal vibration detected',
    time: '18 min ago',
  },
  {
    severity: 'Medium',
    machine: 'Packager M-312',
    message: 'Cycle time trending above baseline',
    time: '42 min ago',
  },
]

export function RecentAlertsPanel() {
  return (
    <motion.article
      className="panel compact-panel recent-alerts-panel"
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.46 }}
    >
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            Operational awareness
          </span>

          <h2>Recent alerts</h2>
        </div>

        <BellRing size={20} />
      </div>

      <div className="recent-alert-list">
        {alerts.map((alert, index) => (
          <motion.div
            key={`${alert.machine}-${alert.time}`}
            className="recent-alert-row"
            initial={{
              opacity: 0,
              y: 8,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              delay: 0.5 + index * 0.07,
            }}
          >
            <span
              className={`alert-severity-marker alert-${alert.severity.toLowerCase()}`}
            />

            <div className="alert-content">
              <div>
                <strong>{alert.machine}</strong>

                <span
                  className={`alert-severity alert-severity-${alert.severity.toLowerCase()}`}
                >
                  {alert.severity}
                </span>
              </div>

              <p>{alert.message}</p>

              <span className="alert-time">
                {alert.time}
              </span>
            </div>

            <button
              type="button"
              className="alert-open-button"
              aria-label={`Open alert for ${alert.machine}`}
            >
              <ArrowUpRight size={15} />
            </button>
          </motion.div>
        ))}
      </div>
    </motion.article>
  )
}