/**
 * Map WebSocket payloads from the API (mock + NATS relay) into UI types.
 * The mock stream uses a flat shape; NATS may use a nested `data` object.
 */
import type { ConflictDict, MessageDict, SimulationEvent } from './types'

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null
}

/** Agent object sent by Python mock stream */
interface WireAgent {
  name: string
  role: string
  dept: string
}

export function eventsToMessages(events: SimulationEvent[]): MessageDict[] {
  const out: MessageDict[] = []
  for (const e of events) {
    if (e.type !== 'agent_message') continue
    const raw = e as unknown as Record<string, unknown>

    if (isRecord(raw.data) && typeof raw.data.content === 'string') {
      out.push(raw.data as unknown as MessageDict)
      continue
    }

    const agent = raw.agent as WireAgent | undefined
    const message = raw.message
    if (agent && typeof message === 'string') {
      const seq = typeof raw.sequence === 'number' ? raw.sequence : out.length + 1
      const runId = String(raw.run_id ?? '')
      const rnd = typeof raw.round === 'number' ? raw.round : 1
      out.push({
        message_id: `${runId}-${seq}`,
        run_id: runId,
        round: rnd,
        agent_role: agent.role,
        department: agent.dept,
        content: message,
        action_type: 'speak',
        timestamp: String(raw.timestamp ?? ''),
      })
    }
  }
  return out
}

function inferPeerLane(lower: string, deptA: string): string {
  const rules: { test: (s: string) => boolean; lane: string }[] = [
    { test: (s) => s.includes('sales') || s.includes('pipeline') || s.includes('quota') || s.includes('marketing'), lane: 'Sales' },
    { test: (s) => s.includes('finance') || s.includes('budget') || s.includes('runway') || s.includes('cost'), lane: 'Finance' },
    { test: (s) => s.includes('ops') || s.includes('operations') || s.includes('capacity') || s.includes('engineering'), lane: 'Operations' },
    { test: (s) => s.includes('hr') || s.includes('morale') || s.includes('headcount') || s.includes('attrition'), lane: 'HR' },
  ]
  for (const { test, lane } of rules) {
    if (test(lower) && lane !== deptA) return lane
  }
  return 'Cross-cutting coordination'
}

export function eventsToConflicts(events: SimulationEvent[]): ConflictDict[] {
  const out: ConflictDict[] = []
  let idx = 0
  for (const e of events) {
    if (e.type !== 'conflict') continue
    const raw = e as unknown as Record<string, unknown>

    if (isRecord(raw.data) && typeof raw.data.conflict_id === 'string') {
      out.push(raw.data as unknown as ConflictDict)
      continue
    }

    const agent = raw.agent as WireAgent | undefined
    const text = String(raw.message ?? '')
    idx += 1
    const runId = String(raw.run_id ?? '')
    const lower = text.toLowerCase()

    let conflict_type: ConflictDict['conflict_type'] = 'priority'
    if (lower.includes('budget') || lower.includes('marketing spend') || lower.includes('spend') || lower.includes('cost')) {
      conflict_type = 'budget'
    } else if (lower.includes('capacity') || lower.includes('pipeline') || lower.includes('bandwidth')) {
      conflict_type = 'resource'
    } else if (lower.includes('timeline') || lower.includes('delivery') || lower.includes('deadline')) {
      conflict_type = 'timeline'
    }

    let severity: ConflictDict['severity'] = 'medium'
    if (lower.includes('9/10') || lower.includes('8/10') || lower.includes('strength')) {
      severity = 'high'
    }

    const deptA = (agent?.dept ?? '').trim() || 'Advisor lane'
    const deptB = inferPeerLane(lower, deptA)

    out.push({
      conflict_id: `${runId}-conflict-${idx}`,
      dept_a: deptA,
      dept_b: deptB,
      conflict_type,
      severity,
      description: text.replace(/^conflict:\s*/i, 'Risk signal: '),
      round_detected: 1,
      agent_a_message: text,
      agent_b_message: '',
    })
  }
  return out
}
