import type { KnowledgeGraph, KnowledgeNode } from '../types/knowledge'

function cloneNode(n: KnowledgeNode): KnowledgeNode {
  return {
    ...n,
    children: [...n.children],
    parents: [...n.parents],
    masteredAt: n.masteredAt ? new Date(n.masteredAt) : undefined,
  }
}

/**
 * Desbloquea hijos cuando un nodo pasa a dominado: un hijo queda `available`
 * solo si **todos** sus padres están en `mastered`.
 */
export function unlockChildren(
  graph: KnowledgeGraph,
  masteredId: string
): KnowledgeGraph {
  const nodes: Record<string, KnowledgeNode> = {}
  for (const id of Object.keys(graph.nodes)) {
    nodes[id] = cloneNode(graph.nodes[id])
  }

  const target = nodes[masteredId]
  if (!target) return graph

  nodes[masteredId] = {
    ...target,
    state: 'mastered',
    masteredAt: target.masteredAt ?? new Date(),
  }

  for (const id of Object.keys(nodes)) {
    const node = nodes[id]
    if (node.state !== 'locked') continue

    const allParentsMastered = node.parents.every((pid) => nodes[pid]?.state === 'mastered')
    if (allParentsMastered) {
      nodes[id] = { ...node, state: 'available' }
    }
  }

  return {
    ...graph,
    nodes,
  }
}
