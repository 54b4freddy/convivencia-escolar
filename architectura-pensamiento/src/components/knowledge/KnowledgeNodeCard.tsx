import { motion } from 'framer-motion'

import { springUnlock, useShouldAnimate } from '../../lib/motionPrefs'
import type { KnowledgeNode } from '../../types/knowledge'

type Props = {
  node: KnowledgeNode
  onActivate: () => void
}

function stateClasses(state: KnowledgeNode['state']): string {
  switch (state) {
    case 'locked':
      return 'border border-gray-300 bg-gray-100 text-gray-400'
    case 'available':
      return 'border-2 border-brand-emerald bg-white text-brand-navy shadow-sm'
    case 'inprogress':
      return 'border-2 border-brand-coral bg-brand-coral text-white'
    case 'mastered':
      return 'border-2 border-brand-navy bg-brand-navy text-white'
    default:
      return ''
  }
}

export function KnowledgeNodeCard({ node, onActivate }: Props) {
  const shouldAnimate = useShouldAnimate()

  return (
    <motion.article
      layout
      role="button"
      tabIndex={0}
      aria-label={`Nodo: ${node.label}, estado: ${node.state}`}
      aria-pressed={node.state === 'inprogress'}
      initial={shouldAnimate ? { scale: 0.85, opacity: 0 } : undefined}
      animate={{ scale: 1, opacity: 1 }}
      transition={shouldAnimate ? springUnlock : { duration: 0 }}
      onClick={onActivate}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onActivate()
        }
      }}
      className={`flex cursor-pointer flex-col gap-1 rounded-xl p-4 text-left font-body outline-none transition hover:brightness-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-emerald ${stateClasses(node.state)}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-heading font-medium leading-snug text-inherit">{node.label}</h3>
        {node.state === 'mastered' ? (
          <span
            className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-brand-sand"
            aria-hidden
          />
        ) : null}
      </div>
      <p className="text-[13px] leading-relaxed text-inherit opacity-95">{node.description}</p>
      <p className="font-mono text-[11px] text-inherit opacity-80">
        enlaces: {node.connections}
      </p>
    </motion.article>
  )
}
