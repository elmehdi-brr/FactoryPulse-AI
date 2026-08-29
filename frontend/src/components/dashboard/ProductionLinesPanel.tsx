import {
  ArrowDownRight,
  ArrowUpRight,
  Factory,
} from 'lucide-react'
import { motion } from 'motion/react'

const productionLines = [
  {
    name: 'Assembly Line A',
    code: 'LINE-A',
    oee: 82.4,
    status: 'Producing',
    trend: 4.2,
  },
  {
    name: 'Packaging Line B',
    code: 'LINE-B',
    oee: 71.2,
    status: 'Attention',
    trend: -2.1,
  },
  {
    name: 'Assembly Line C',
    code: 'LINE-C',
    oee: 89.1,
    status: 'Producing',
    trend: 6.8,
  },
]

export function ProductionLinesPanel() {
  return (
    <motion.article
      className="panel production-lines-panel"
      initial={{ opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.34 }}
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
        {productionLines.map((line, index) => {
          const improving = line.trend >= 0

          return (
            <motion.div
              key={line.code}
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
                delay: 0.4 + index * 0.07,
              }}
              whileHover={{
                x: 3,
              }}
            >
              <div className="line-identity">
                <div
                  className={`line-status-indicator ${
                    line.status === 'Attention'
                      ? 'line-status-attention'
                      : ''
                  }`}
                />

                <div>
                  <strong>{line.name}</strong>
                  <span>{line.code}</span>
                </div>
              </div>

              <div className="line-state">
                <span
                  className={`status-pill ${
                    line.status === 'Attention'
                      ? 'status-pill-warning'
                      : 'status-pill-healthy'
                  }`}
                >
                  {line.status}
                </span>
              </div>

              <div className="line-oee">
                <span>OEE</span>
                <strong>{line.oee}%</strong>
              </div>

              <div
                className={`line-trend ${
                  improving
                    ? 'trend-positive'
                    : 'trend-negative'
                }`}
              >
                {improving ? (
                  <ArrowUpRight size={14} />
                ) : (
                  <ArrowDownRight size={14} />
                )}

                {Math.abs(line.trend)}%
              </div>
            </motion.div>
          )
        })}
      </div>
    </motion.article>
  )
}