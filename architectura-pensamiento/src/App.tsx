import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import { demoGraph } from './data/demoGraph'
import { AchievementBadge } from './components/ui/AchievementBadge'
import { AlertBanner } from './components/ui/AlertBanner'
import { Button } from './components/ui/Button'
import { EmptyGraphState } from './components/EmptyGraphState'
import { KnowledgeNodeCard } from './components/knowledge/KnowledgeNodeCard'
import { ProgressRing } from './components/knowledge/ProgressRing'
import { AppShell } from './components/layout/AppShell'
import { useKnowledgeGraphStore } from './stores/knowledgeGraphStore'
import type { KnowledgeNode } from './types/knowledge'

function graphProgress(nodes: Record<string, KnowledgeNode>): number {
  const list = Object.values(nodes)
  if (!list.length) return 0
  const mastered = list.filter((n) => n.state === 'mastered').length
  return Math.round((mastered / list.length) * 100)
}

export default function App() {
  /** Datos de servidor (demo): mismo grafo; staleTime infinito para no pisar Zustand */
  useQuery({
    queryKey: ['knowledge-graph', 'demo'],
    queryFn: async () => demoGraph,
    staleTime: Infinity,
  })

  const { graph, markMastered, setNodeInProgress } = useKnowledgeGraphStore()
  const [showError, setShowError] = useState(false)

  const pct = useMemo(() => graphProgress(graph.nodes), [graph.nodes])
  const nodeList = useMemo(
    () => Object.values(graph.nodes).sort((a, b) => a.id.localeCompare(b.id)),
    [graph.nodes]
  )

  const handleNode = (node: KnowledgeNode) => {
    if (node.state === 'locked') {
      setShowError(true)
      return
    }
    setShowError(false)
    if (node.state === 'available') {
      setNodeInProgress(node.id)
      return
    }
    if (node.state === 'inprogress') {
      markMastered(node.id)
    }
  }

  return (
    <AppShell
      title="Estás construyendo tu mapa"
      subtitle="Descubre cómo las ideas se enlazan — el progreso es un grafo, no una lista lineal."
    >
      <div className="mb-8 flex flex-wrap items-center gap-4">
        <ProgressRing
          progress={pct}
          label={`Progreso del grafo: ${pct} por ciento`}
        />
        <div>
          <p className="font-body text-[13px] font-medium text-brand-navy">
            Densidad del mapa
          </p>
          <p className="font-body text-[12px] text-gray-500">
            ¿Ves el patrón? Cada nodo desbloquea rutas nuevas.
          </p>
        </div>
        <AchievementBadge className="ml-auto">
          Nodo dominado. El grafo se expande.
        </AchievementBadge>
      </div>

      {showError ? (
        <div className="mb-6">
          <AlertBanner>
            Algo salió de su órbita. Reintentemos — primero completa los
            prerrequisitos en el grafo.
          </AlertBanner>
        </div>
      ) : null}

      <section className="mb-6 rounded-2xl bg-surface-card p-6 shadow-sm">
        <h2 className="font-display text-[22px] font-bold leading-tight text-brand-navy">
          Tu red de conceptos
        </h2>
        <p className="mt-2 font-body text-[15px] leading-[1.65] text-gray-600">
          Explora el módulo tocando un nodo disponible o en progreso. No hay
          puntos ni tablas globales — solo conexiones.
        </p>
        {nodeList.length === 0 ? (
          <div className="mt-6">
            <EmptyGraphState />
          </div>
        ) : (
          <ul className="mt-6 grid list-none gap-4 p-0 sm:grid-cols-2">
            {nodeList.map((node) => (
              <li key={node.id}>
                <KnowledgeNodeCard node={node} onActivate={() => handleNode(node)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="flex flex-wrap gap-3">
        <Button
          variant="primary"
          onClick={() => setShowError((s) => !s)}
        >
          Probar alerta
        </Button>
        <Button variant="secondary" onClick={() => window.location.reload()}>
          Reiniciar vista
        </Button>
      </div>
    </AppShell>
  )
}
