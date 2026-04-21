import { motion } from 'framer-motion'

import { progressRing, useShouldAnimate } from '../../lib/motionPrefs'

type Props = {
  /** 0–100 */
  progress: number
  size?: number
  stroke?: number
  label: string
}

export function ProgressRing({ progress, size = 56, stroke = 4, label }: Props) {
  const shouldAnimate = useShouldAnimate()
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const pct = Math.min(100, Math.max(0, progress))
  const dashOffset = c * (1 - pct / 100)

  return (
    <svg
      width={size}
      height={size}
      role="img"
      aria-label={label}
      className="shrink-0"
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="#ECEAE3"
        strokeWidth={stroke}
      />
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="#009368"
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={c}
        initial={shouldAnimate ? { strokeDashoffset: c } : { strokeDashoffset: dashOffset }}
        animate={{ strokeDashoffset: dashOffset }}
        transition={shouldAnimate ? progressRing : { duration: 0 }}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
    </svg>
  )
}
