// Shared TypeScript types for the CivicBridge frontend.

export type CivicBridgeTrack = 'founder' | 'first1000'

export interface KeyFacts {
  currentStatus: string
  goal: string
  deadline: string
  location: string
  workCompanyFacts: string
  familyDependents: string
}

export type DeptName = 'Sales' | 'Finance' | 'Operations' | 'HR'

export interface SimulationRun {
  run_id: string
  decision: string
  departments: string[]
  status: 'pending' | 'running' | 'complete' | 'error'
  created_at: string
  messages: MessageDict[]
  conflicts: ConflictDict[]
  report: ReportDict | null
}

export interface MessageDict {
  message_id: string
  run_id: string
  round: number
  agent_role: string
  department: string
  content: string
  action_type: string
  timestamp: string
}

export type RiskCategory =
  | 'eligibility'
  | 'evidence'
  | 'timing'
  | 'cost'
  | 'compliance'
  | 'work_authorization'
  | 'healthcare'
  | 'housing'
  | 'banking_credit'
  | 'tax'
  | 'language_access'
  | 'professional_review'

export interface ConflictDict {
  conflict_id: string
  dept_a: string
  dept_b: string
  conflict_type: 'resource' | 'priority' | 'timeline' | 'budget'
  severity: 'low' | 'medium' | 'high'
  description: string
  round_detected: number
  agent_a_message: string
  agent_b_message: string
  /** CivicBridge: coarse risk lane mapped from advisor tension text */
  risk_category?: RiskCategory | string
  risk_summary?: string
}

export interface ReportSourceLink {
  title: string
  url: string
}

export interface ReportDict {
  executive_summary: string
  key_risks: string[]
  recommended_actions: string[]
  confidence_score: number
  known_facts?: string[]
  unknown_facts?: string[]
  must_verify_facts?: string[]
  professional_questions?: string[]
  source_links?: ReportSourceLink[]
  caveat?: string
}

/** Wire event from `/ws/simulation/{run_id}` — may be flat (mock) or nested `data` (NATS). */
export interface SimulationEvent {
  type: 'agent_message' | 'conflict' | 'complete' | 'error'
  run_id: string
  timestamp: string
  data?: MessageDict | ConflictDict | { status: string } | { error: string }
  /** Flat shape from Python mock stream */
  agent?: { name: string; role: string; dept: string }
  message?: string
  sequence?: number
  round?: number
  /** Complete event summary from mock */
  summary?: {
    total_messages?: number
    conflicts_detected?: number
    recommendation?: string
  }
}

export interface CascadeMap {
  decision: string
  primary_impact: Array<{ dept: string; severity: string; reason: string }>
  secondary_impact: Array<{ dept: string; severity: string; via: string; reason: string }>
}
