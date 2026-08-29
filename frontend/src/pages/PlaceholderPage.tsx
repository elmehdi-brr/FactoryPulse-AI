import { ArrowUpRight } from 'lucide-react'
import { motion } from 'motion/react'

type PlaceholderPageProps = {
  eyebrow: string
  title: string
  description: string
}

export function PlaceholderPage({
  eyebrow,
  title,
  description,
}: PlaceholderPageProps) {
  return (
    <div className="placeholder-page">
      <motion.div
        initial={{
          opacity: 0,
          y: 18,
        }}
        animate={{
          opacity: 1,
          y: 0,
        }}
      >
        <p className="page-eyebrow">{eyebrow}</p>

        <h1>{title}</h1>

        <p>{description}</p>

        <div className="coming-soon">
          <span>Coming in this milestone</span>
          <ArrowUpRight size={16} />
        </div>
      </motion.div>
    </div>
  )
}