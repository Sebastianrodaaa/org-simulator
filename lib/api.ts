import type {
  SimulationRun,
  SimulationEvent,
  ConflictDict,
  MessageDict,
  ReportDict,
} from './types'

export type { SimulationRun, SimulationEvent, ConflictDict, MessageDict, ReportDict }

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function networkErrorHint(context: string): Error {
  return new Error(
    `${context} — cannot reach API at ${BASE}. ` +
      'Start it from the repo: `cd Backend && uvicorn api.main:app --reload --port 8000`. ' +
      'If the API runs elsewhere, set `NEXT_PUBLIC_API_URL` in Frontend `.env.local` and restart `npm run dev`.'
  )
}

async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch (e) {
    if (e instanceof TypeError && /fetch|Load failed|NetworkError/i.test(e.message)) {
      throw networkErrorHint('Network error')
    }
    throw e
  }
}

/** POST /simulate response (subset of fields used by the UI). */
export interface SimulationCreateResponse {
  run_id: string
  status: 'pending' | 'running' | 'complete' | 'failed' | 'error'
  decision: string
  departments: string[]
  created_at: string
  recommendation?: string | null
  engine?: 'cascade' | 'swarm'
  /** Present when the API returns a full run payload (optional on GET /simulate). */
  messages?: MessageDict[]
  conflicts?: ConflictDict[]
  report?: ReportDict | null
}

/** @deprecated use conflicts — same shape; risks surfaced between advisor lanes */
export type RiskSignalDict = ConflictDict

export type SimulationEngine = 'cascade' | 'swarm'

export interface SimulationStartOptions {
  engine?: SimulationEngine
  rounds?: number
  swarmSize?: number
  maxActivePerRound?: number
  /** CivicBridge track — when set, backend uses advisor personas for that track. */
  track?: 'founder' | 'first1000'
}

export async function startSimulation(
  decision: string,
  departments: string[],
  options?: SimulationStartOptions
): Promise<SimulationCreateResponse> {
  const body: Record<string, unknown> = {
    decision,
    departments,
    engine: options?.engine ?? 'swarm',
    rounds: options?.rounds ?? 4,
  }
  if (options?.track != null) body.track = options.track
  if (options?.swarmSize != null) body.swarm_size = options.swarmSize
  if (options?.maxActivePerRound != null) {
    body.max_active_per_round = options.maxActivePerRound
  } else if ((options?.engine ?? 'swarm') === 'swarm') {
    body.max_active_per_round = 8
  }

  const res = await apiFetch(`${BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<SimulationCreateResponse>
}

export async function getSimulation(runId: string): Promise<SimulationCreateResponse> {
  const res = await apiFetch(`${BASE}/simulate/${runId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<SimulationCreateResponse>
}

export async function getHealth(): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${BASE}/health`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
