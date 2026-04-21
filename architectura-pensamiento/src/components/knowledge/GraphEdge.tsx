import { motion } from 'framer-motion'

import { edgeDraw, useShouldAnimate } from '../../lib/motionPrefs'

type Props = {
  d: string
  id: string
}

/** Arista SVG animada (trazo) — accesible como imagen decorativa de relación */
export function GraphEdge({ d, id }: Props) {
  const shouldAnimate = useShouldAnimate()
  return (
    <motion.path
      id={id}
      d={d}
      fill="none"
      stroke="#143351"
      strokeWidth={2}
      strokeLinecap="round"
      role="img"
      aria-label="Conexión entre conceptos del grafo"
      initial={shouldAnimate ? { pathLength: 0, opacity: 0 } : undefined}
      animate={{ pathLength: 1, opacity: 1 }}
      transition={shouldAnimate ? edgeDraw : { duration: 0 }}
    />
  )
}
