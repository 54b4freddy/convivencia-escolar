export type NodeState = 'locked' | 'available' | 'inprogress' | 'mastered'

export interface KnowledgeNode {
  id: string
  label: string
  description: string
  state: NodeState
  children: string[]
  parents: string[]
  moduleId: string
  masteredAt?: Date
  /** Cuántas veces fue enlazado con otros grafos */
  connections: number
}

export interface KnowledgeGraph {
  id: string
  subjectId: string
  nodes: Record<string, KnowledgeNode>
  edges: Array<[string, string]>
}

export type UserLevel = 'inicial' | 'explorador' | 'integrador' | 'arquitecto'
