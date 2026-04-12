'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { startSimulation, type SimulationEngine } from '@/lib/api'
import { useSimulationStream } from '@/lib/useSimulationStream'
import { ConflictGraph } from '@/components/ConflictGraph'
import { SwarmInteractionGraph } from '@/components/SwarmInteractionGraph'
import Plan from '@/components/ui/agent-plan'
import type { ConflictDict, MessageDict, SimulationEvent } from '@/lib/types'
import { eventsToConflicts, eventsToMessages } from '@/lib/wireSimulationEvents'

const ALL_DEPTS = ['Sales', 'Finance', 'Operations', 'HR'] as const

const DEMO_DECISION =
  'The CFO has decided to cut the Q4 marketing budget by 20%.\nSimulate the organizational cascade over the next 90 days.'

const DEPT_COLOR: Record<string, string> = {
  Sales: '#185FA5',
  Finance: '#854F0B',
  Operations: '#0F6E56',
  HR: '#534AB7',
}

const SEVERITY_BADGE: Record<ConflictDict['severity'], string> = {
  low: 'bg-amber-50 text-amber-700',
  medium: 'bg-orange-50 text-orange-700',
  high: 'bg-red-50 text-red-700',
}

const CONFLICT_TYPE_BADGE: Record<ConflictDict['conflict_type'], string> = {
  resource: 'bg-blue-50 text-blue-700',
  priority: 'bg-purple-50 text-purple-700',
  timeline: 'bg-orange-50 text-orange-700',
  budget: 'bg-red-50 text-red-700',
}

const SEVERITY_EDGE: Record<string, string> = {
  low: '#fbbf24', medium: '#f97316', high: '#ef4444',
}

function relativeTime(ts: string): string {
  const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000)
  if (diff < 5) return 'just now'
  if (diff < 60) return `${diff}s ago`
  return `${Math.floor(diff / 60)}m ago`
}

function initials(role: string): string {
  return role.split(/[\s_]/).map((w) => w[0]).join('').toUpperCase().slice(0, 2)
}

function swarmStats(events: SimulationEvent[]) {
  const agents = new Set<string>()
  const rounds = new Set<number>()
  const interactions = new Set<string>()
  const previousByRound = new Map<number, string>()

  for (const ev of events) {
    if (ev.type !== 'agent_message' || !ev.agent) continue
    const agentName = ev.agent.name || ev.agent.role || 'agent'
    const round = typeof ev.round === 'number' ? ev.round : 1
    agents.add(agentName)
    rounds.add(round)
    const prev = previousByRound.get(round)
    if (prev && prev !== agentName) interactions.add(`${prev}->${agentName}`)
    previousByRound.set(round, agentName)
  }

  return {
    agents: agents.size,
    interactions: interactions.size,
    rounds: rounds.size,
  }
}

function AgentFeedSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex gap-2.5">
          <div className="animate-pulse flex-shrink-0 w-7 h-7 rounded-full bg-gray-200" />
          <div className="flex-1 space-y-1.5 pt-0.5">
            <div className="flex gap-2">
              <div className="animate-pulse h-3.5 w-14 rounded bg-gray-200" />
              <div className="animate-pulse h-3.5 w-20 rounded bg-gray-200" />
            </div>
            <div className="animate-pulse h-3 w-full rounded bg-gray-200" />
            <div className="animate-pulse h-3 w-3/4 rounded bg-gray-200" />
          </div>
        </div>
      ))}
    </div>
  )
}

function SimulateInner() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isDemo = searchParams.get('demo') === 'true'

  const [decision, setDecision] = useState(DEMO_DECISION)
  const [selectedDepts, setSelectedDepts] = useState<string[]>([...ALL_DEPTS])
  const [runId, setRunId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [engine, setEngine] = useState<SimulationEngine>('swarm')
  const [swarmSize, setSwarmSize] = useState(48)
  const feedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isDemo) {
      setDecision(DEMO_DECISION)
      setSelectedDepts([...ALL_DEPTS])
    }
  }, [isDemo])

  const { events, status } = useSimulationStream(runId)
  const messages: MessageDict[] = eventsToMessages(events)
  const conflicts: ConflictDict[] = eventsToConflicts(events)
  const swarm = swarmStats(events)

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight
    }
  }, [messages.length])

  function toggleDept(dept: string) {
    if (runId) return
    setSelectedDepts((prev) =>
      prev.includes(dept) ? prev.filter((d) => d !== dept) : [...prev, dept],
    )
  }

  async function handleRun() {
    if (!decision.trim() || selectedDepts.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const run = await startSimulation(decision, selectedDepts, {
        engine,
        rounds: engine === 'swarm' ? 10 : 15,
        swarmSize: engine === 'swarm' ? swarmSize : undefined,
      })
      setRunId(run.run_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start simulation')
    } finally {
      setLoading(false)
    }
  }

  const isLive = !!runId && status !== 'complete' && status !== 'error'

  return (
    // Full-height two-column split
    <div className="flex flex-col lg:flex-row h-[calc(100dvh-45px)] overflow-hidden">

      {/* ── LEFT PANEL ─────────────────────────────────────────────────────── */}
      <div className="lg:w-[580px] flex-shrink-0 flex flex-col overflow-y-auto border-r border-gray-200 bg-white">
        <div className="p-5 space-y-4 flex-1">

          {/* Demo banner */}
          {isDemo && !runId && (
            <div className="rounded-md bg-blue-50 border border-blue-200 px-3 py-2 text-xs text-blue-700 flex items-center gap-2">
              <span className="font-semibold">Demo mode</span>
              <span className="text-blue-400">—</span>
              <span>Pre-filled with CFO budget scenario. Press Run to begin.</span>
            </div>
          )}

          {/* Scenario input */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-gray-900">Scenario</h2>
            <textarea
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-gray-900 min-h-[88px] disabled:bg-gray-50 disabled:text-gray-500"
              rows={4}
              placeholder="Describe the decision to simulate..."
              value={decision}
              onChange={(e) => setDecision(e.target.value)}
              disabled={!!runId}
            />
            <div className="flex flex-wrap gap-1.5">
              {ALL_DEPTS.map((dept) => {
                const active = selectedDepts.includes(dept)
                return (
                  <button
                    key={dept}
                    onClick={() => toggleDept(dept)}
                    disabled={!!runId}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors touch-manipulation ${
                      active
                        ? 'text-white border-transparent'
                        : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
                    } disabled:cursor-not-allowed`}
                    style={active ? { backgroundColor: DEPT_COLOR[dept] } : {}}
                  >
                    {dept}
                  </button>
                )
              })}
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-gray-700">Simulation engine</h3>
              <div className="flex flex-wrap gap-3 text-xs text-gray-600">
                <label className="inline-flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="engine"
                    checked={engine === 'cascade'}
                    onChange={() => setEngine('cascade')}
                    disabled={!!runId}
                    className="accent-gray-900"
                  />
                  Cascade (4 roles / round)
                </label>
                <label className="inline-flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="engine"
                    checked={engine === 'swarm'}
                    onChange={() => setEngine('swarm')}
                    disabled={!!runId}
                    className="accent-gray-900"
                  />
                  Swarm (large pool)
                </label>
              </div>
              {engine === 'swarm' && (
                <label className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="whitespace-nowrap">Pool size</span>
                  <input
                    type="number"
                    min={16}
                    max={256}
                    step={8}
                    value={swarmSize}
                    onChange={(e) => setSwarmSize(Number(e.target.value) || 48)}
                    disabled={!!runId}
                    className="w-20 rounded border border-gray-200 px-2 py-1 text-xs"
                  />
                </label>
              )}

            </div>

            {error && <p className="text-red-500 text-xs break-words">{error}</p>}
            <button
              onClick={handleRun}
              disabled={loading || !!runId || selectedDepts.length === 0}
              className="w-full px-4 py-2 rounded-md bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Starting...' : runId ? 'Simulation running' : 'Run simulation'}
            </button>
          </section>

          {/* Divider */}
          {runId && <div className="border-t border-gray-100" />}

          {/* Agent activity feed — Plan component */}
          {runId && (
            <section className="space-y-2">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold text-gray-900">
                  {status === 'complete' ? 'Activity trace' : status === 'error' ? 'Connection error' : 'Live activity'}
                </h2>
                {isLive && (
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
                  </span>
                )}
              </div>
              <div className="h-64 overflow-y-auto">
                <Plan events={events} status={status} />
              </div>
            </section>
          )}

          {/* Conflicts list — compact */}
          {runId && conflicts.length > 0 && (
            <>
              <div className="border-t border-gray-100" />
              <section className="space-y-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-gray-900">Detected conflicts</h2>
                  <span className="px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px] font-semibold">
                    {conflicts.length}
                  </span>
                </div>
                <div className="space-y-1.5">
                  {conflicts.map((c) => (
                    <div
                      key={c.conflict_id}
                      className="flex items-center gap-2 rounded-md border border-gray-100 bg-gray-50 px-3 py-2"
                    >
                      {/* Severity dot */}
                      <span
                        className="flex-shrink-0 w-2 h-2 rounded-full"
                        style={{ backgroundColor: SEVERITY_EDGE[c.severity] }}
                      />
                      <span className="text-xs font-medium text-gray-900 min-w-0 truncate">
                        {c.dept_a} ↔ {c.dept_b}
                      </span>
                      <div className="ml-auto flex items-center gap-1 flex-shrink-0">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${CONFLICT_TYPE_BADGE[c.conflict_type]}`}>
                          {c.conflict_type}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${SEVERITY_BADGE[c.severity]}`}>
                          {c.severity}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}

          {/* View report */}
          {status === 'complete' && runId && (
            <button
              onClick={() => router.push(`/report/${runId}`)}
              className="w-full px-4 py-2 rounded-md bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 transition-colors"
            >
              View simulation report →
            </button>
          )}
        </div>
      </div>

      {/* ── RIGHT PANEL — interactive network ──────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-50 min-h-[400px] lg:min-h-0">

        {/* Header bar */}
        <div className="flex-shrink-0 px-5 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="font-semibold text-sm text-gray-900">
              {engine === 'swarm' ? 'Swarm Interaction Graph' : 'Org Network'}
            </span>
            {isLive && (
              <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
                </span>
                live
              </span>
            )}
            {status === 'complete' && (
              <span className="text-xs text-gray-400 font-medium">complete</span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            {engine === 'swarm' && runId && (
              <>
                <span>{swarm.agents} agents surfaced</span>
                <span>{swarm.interactions} interactions</span>
              </>
            )}
            {conflicts.length > 0 && (
              <span className="text-red-500 font-medium">{conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''}</span>
            )}
            {!runId && (
              <span className="text-gray-400">Run a scenario to see cascade</span>
            )}
          </div>
        </div>

        {/* Graph */}
        <div className="flex-1 min-h-0 p-2">
          {engine === 'swarm' ? (
            <SwarmInteractionGraph events={events} />
          ) : (
            <ConflictGraph conflicts={conflicts} messages={messages} />
          )}
        </div>

        {/* Legend */}
        <div className="flex-shrink-0 px-5 py-2.5 border-t border-gray-100 bg-white flex items-center gap-4 flex-wrap">
          {engine === 'swarm' ? (
            <>
              <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wide">Swarm legend</span>
              <span className="text-[10px] text-gray-500">Node size = message volume</span>
              <span className="text-[10px] text-gray-500">Arrow = next speaker in same round</span>
            </>
          ) : (
            <>
              <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wide">Severity</span>
              {(['low', 'medium', 'high'] as const).map((s) => (
                <span key={s} className="flex items-center gap-1.5 text-[10px] text-gray-500">
                  <span
                    className="inline-block w-5 h-0.5 rounded-full"
                    style={{ backgroundColor: SEVERITY_EDGE[s] }}
                  />
                  {s}
                </span>
              ))}
            </>
          )}
          <span className="ml-auto text-[10px] text-gray-300">drag to reposition</span>
        </div>
      </div>
    </div>
  )
}

export default function SimulatePage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-full text-gray-400 text-sm">Loading...</div>}>
      <SimulateInner />
    </Suspense>
  )
}
