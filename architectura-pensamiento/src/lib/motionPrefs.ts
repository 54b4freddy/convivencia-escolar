import { useReducedMotion } from 'framer-motion'

/** Respeta `prefers-reduced-motion` para animaciones Framer Motion */
export function useShouldAnimate(): boolean {
  const reduced = useReducedMotion()
  return reduced !== true
}

export const springUnlock = {
  type: 'spring' as const,
  damping: 20,
  stiffness: 280,
}

export const edgeDraw = {
  duration: 0.6,
  ease: 'easeInOut' as const,
  delay: 0.1,
}

export const progressRing = {
  duration: 0.8,
  ease: 'easeOut' as const,
}
