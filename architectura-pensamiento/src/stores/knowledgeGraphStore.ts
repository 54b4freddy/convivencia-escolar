import { create } from 'zustand'

import { demoGraph } from '../data/demoGraph'
import { unlockChildren } from '../lib/graph'
import type { KnowledgeGraph } from '../types/knowledge'

type KnowledgeGraphState = {
  graph: KnowledgeGraph
  setGraph: (g: KnowledgeGraph) => void
  /** Marca un nodo como dominado y recalcula desbloqueos (grafo, no barra lineal) */
  markMastered: (nodeId: string) => void
  setNodeInProgress: (nodeId: string) => void
}

export const useKnowledgeGraphStore = create<KnowledgeGraphState>((set, get) => ({
  graph: demoGraph,
  setGraph: (g) => set({ graph: g }),
  markMastered: (nodeId) => {
    const { graph } = get()
    set({ graph: unlockChildren(graph, nodeId) })
  },
  setNodeInProgress: (nodeId) => {
    const { graph } = get()
    const n = graph.nodes[nodeId]
    if (!n || n.state === 'locked') return
    const nodes = { ...graph.nodes, [nodeId]: { ...n, state: 'inprogress' as const } }
    set({ graph: { ...graph, nodes } })
  },
}))
