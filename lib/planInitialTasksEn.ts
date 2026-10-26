/** Default English pipeline steps for the rehearsal plan UI (bypass messages if locale has no override). */

export interface PlanSubtask {
  id: string
  title: string
  description: string
  status: string
  priority: string
  tools?: string[]
}

export interface PlanTask {
  id: string
  title: string
  description: string
  status: string
  priority: string
  level: number
  dependencies: string[]
  subtasks: PlanSubtask[]
}

export const planInitialTasksEn: PlanTask[] = [
  {
    id: '1',
    title: 'Load Situation Snapshots',
    description:
      "Read structured notes for each advisor perspective to ground reasoning in the user's real situation.",
    status: 'completed',
    priority: 'high',
    level: 0,
    dependencies: [],
    subtasks: [
      {
        id: '1.1',
        title: 'Sales pipeline snapshot',
        description:
          'Pipeline value $4.2M, 25 open deals, win-rate 34%, Q4 close targets at risk.',
        status: 'completed',
        priority: 'high',
        tools: ['typedb', 'file-system'],
      },
      {
        id: '1.2',
        title: 'Timeline snapshot',
        description: 'evidence roadmap budget $280K, runway 18 months, burn $620K/mo.',
        status: 'completed',
        priority: 'high',
        tools: ['typedb', 'file-system'],
      },
      {
        id: '1.3',
        title: 'Operations snapshot',
        description:
          'Engineering capacity 94%, DevOps 88%, 3 open incidents, infra cost rising.',
        status: 'completed',
        priority: 'medium',
        tools: ['typedb', 'file-system'],
      },
      {
        id: '1.4',
        title: 'HR snapshot',
        description:
          '142 headcount, attrition 11%, 18 open reqs, top-performer flight risk in Sales.',
        status: 'completed',
        priority: 'medium',
        tools: ['typedb', 'file-system'],
      },
    ],
  },
  {
    id: '2',
    title: 'Generate Agent Personas',
    description:
      'Instantiate role-specific stakeholder agents with behavioral biases from YAML templates.',
    status: 'in-progress',
    priority: 'high',
    level: 0,
    dependencies: [],
    subtasks: [
      {
        id: '2.1',
        title: 'CFO — cost-control bias',
        description:
          'Prioritises runway preservation, pushes back on discretionary spend, approves cuts that reduce burn.',
        status: 'completed',
        priority: 'high',
        tools: ['ollama', 'dspy', 'neo4j'],
      },
      {
        id: '2.2',
        title: 'VP Sales — pipeline bias',
        description:
          'Defends marketing budget as pipeline fuel, flags Q4 revenue risk if spend drops.',
        status: 'in-progress',
        priority: 'high',
        tools: ['ollama', 'dspy', 'neo4j'],
      },
      {
        id: '2.3',
        title: 'Operations Lead — capacity bias',
        description:
          'Flags overcommitment risk; engineering already at 94% — any scope creep triggers alert.',
        status: 'pending',
        priority: 'medium',
        tools: ['ollama', 'dspy', 'neo4j'],
      },
      {
        id: '2.4',
        title: 'HR Director — retention bias',
        description:
          'Monitors morale signal; budget cuts that threaten commission plans raise flight-risk score.',
        status: 'pending',
        priority: 'medium',
        tools: ['ollama', 'dspy', 'neo4j'],
      },
    ],
  },
  {
    id: '3',
    title: 'Trace Cascade Impact',
    description: 'Map which advisor perspectives and life systems are downstream of the decision.',
    status: 'pending',
    priority: 'high',
    level: 1,
    dependencies: ['1'],
    subtasks: [
      {
        id: '3.1',
        title: 'Primary impact — Finance → Sales',
        description: '20% marketing cut directly reduces lead generation, compressing evidence timeline.',
        status: 'pending',
        priority: 'high',
        tools: ['typedb', 'cascade-tracer'],
      },
      {
        id: '3.2',
        title: 'Secondary impact — Sales → HR',
        description:
          'Pipeline compression threatens OTE attainment, elevating Sales rep flight risk.',
        status: 'pending',
        priority: 'medium',
        tools: ['typedb', 'cascade-tracer'],
      },
      {
        id: '3.3',
        title: 'Secondary impact — Finance → Ops',
        description:
          'Budget reallocation may trigger infra spend freeze, blocking planned capacity upgrades.',
        status: 'pending',
        priority: 'medium',
        tools: ['typedb', 'cascade-tracer'],
      },
    ],
  },
  {
    id: '4',
    title: 'Run Simulation Rounds',
    description:
      'Execute MiroFish-Offline swarm loop on the decision_cascade platform — agents respond and cross-react.',
    status: 'pending',
    priority: 'high',
    level: 1,
    dependencies: ['2', '3'],
    subtasks: [
      {
        id: '4.1',
        title: 'Rounds 1–5: initial reactions',
        description: 'Each agent posts first-order response to the budget decision on the cascade channel.',
        status: 'pending',
        priority: 'high',
        tools: ['mirofish', 'ollama', 'nats'],
      },
      {
        id: '4.2',
        title: 'Rounds 6–15: cross-agent pressure',
        description:
          "Agents read peers' posts and escalate or moderate positions; emergent risks surface.",
        status: 'pending',
        priority: 'high',
        tools: ['mirofish', 'ollama', 'nats'],
      },
      {
        id: '4.3',
        title: 'Rounds 16–20: stabilisation',
        description:
          'Agents attempt negotiation; unresolved positions are flagged as persistent risks.',
        status: 'pending',
        priority: 'medium',
        tools: ['mirofish', 'ollama', 'nats'],
      },
    ],
  },
  {
    id: '5',
    title: 'Extract Conflicts',
    description:
      'Parse agent message log for opposing positions, resource blocks, and action-scope violations.',
    status: 'pending',
    priority: 'high',
    level: 1,
    dependencies: ['4'],
    subtasks: [
      {
        id: '5.1',
        title: 'Classify risk type',
        description:
          'DSPy signature infers budget / resource / priority / timeline from message pair content.',
        status: 'pending',
        priority: 'high',
        tools: ['dspy', 'ollama'],
      },
      {
        id: '5.2',
        title: 'Score severity',
        description:
          'LLM rates low / medium / high based on downstream impact described in cascade map.',
        status: 'pending',
        priority: 'high',
        tools: ['dspy', 'ollama'],
      },
      {
        id: '5.3',
        title: 'Publish to NATS',
        description: 'Each risk signal is emitted to the live UI relay.',
        status: 'pending',
        priority: 'medium',
        tools: ['nats-jetstream'],
      },
    ],
  },
  {
    id: '6',
    title: 'Generate Executive Report',
    description: 'DSPy pipeline compiles risk map and advisor summaries into a practical action report.',
    status: 'pending',
    priority: 'high',
    level: 1,
    dependencies: ['3', '5'],
    subtasks: [
      {
        id: '6.1',
        title: 'Summarise each risk',
        description:
          'ConflictSummary DSPy signature produces plain-English summary + recommendation per pair.',
        status: 'pending',
        priority: 'high',
        tools: ['dspy', 'ollama'],
      },
      {
        id: '6.2',
        title: 'Draft executive summary',
        description:
          'ExecutiveReport signature synthesises all summaries into a 3-paragraph decision brief.',
        status: 'pending',
        priority: 'high',
        tools: ['dspy', 'ollama'],
      },
      {
        id: '6.3',
        title: 'Score confidence',
        description:
          'LLM emits a 0–1 confidence_score reflecting how deterministic the cascade outcomes are.',
        status: 'pending',
        priority: 'medium',
        tools: ['dspy', 'ollama'],
      },
    ],
  },
]
