import type { KnowledgeGraph } from '../types/knowledge'

/** Grafo demo — progreso no lineal: dependencias entre nodos */
export const demoGraph: KnowledgeGraph = {
  id: 'g-demo',
  subjectId: 'complejidad-101',
  nodes: {
    n1: {
      id: 'n1',
      label: 'Patrones',
      description: 'Explora el módulo de patrones recurrentes en sistemas vivos.',
      state: 'mastered',
      children: ['n2', 'n3'],
      parents: [],
      moduleId: 'mod-a',
      masteredAt: new Date(),
      connections: 3,
    },
    n2: {
      id: 'n2',
      label: 'Relaciones',
      description: 'Descubre cómo se enlazan conceptos en tu mapa.',
      state: 'available',
      children: ['n4'],
      parents: ['n1'],
      moduleId: 'mod-a',
      connections: 1,
    },
    n3: {
      id: 'n3',
      label: 'Límites',
      description: '¿Ves el patrón? ¿Qué ocurre cuando el sistema cambia de escala?',
      state: 'inprogress',
      children: ['n4'],
      parents: ['n1'],
      moduleId: 'mod-a',
      connections: 0,
    },
    n4: {
      id: 'n4',
      label: 'Síntesis',
      description: 'Aún no hay conexiones — sé el primero en trazarlas.',
      state: 'locked',
      children: [],
      parents: ['n2', 'n3'],
      moduleId: 'mod-a',
      connections: 0,
    },
  },
  edges: [
    ['n1', 'n2'],
    ['n1', 'n3'],
    ['n2', 'n4'],
    ['n3', 'n4'],
  ],
}
