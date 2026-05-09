'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { BriefcaseBusiness, Compass, ShieldCheck } from 'lucide-react'
import { startSimulation, type SimulationEngine } from '@/lib/api'
import { useSimulationStream } from '@/lib/useSimulationStream'
import { ConflictGraph } from '@/components/ConflictGraph'
import { SwarmInteractionGraph } from '@/components/SwarmInteractionGraph'
import Plan from '@/components/ui/agent-plan'
import type {
  CivicBridgeTrack,
  ConflictDict,
  GuidedScenario,
  KeyFacts,
  MessageDict,
  SimulationEvent,
} from '@/lib/types'
import { eventsToConflicts, eventsToMessages } from '@/lib/wireSimulationEvents'

const COMPATIBILITY_DEPTS = ['Sales', 'Finance', 'Operations', 'HR'] as const

const EMPTY_KEY_FACTS: KeyFacts = {
  currentStatus: '',
  goal: '',
  deadline: '',
  location: '',
  workCompanyFacts: '',
  familyDependents: '',
}

const TRACKS: Record<
  CivicBridgeTrack,
  { label: string; subtext: string; accent: string; icon: typeof BriefcaseBusiness }
> = {
  founder: {
    label: 'Founder Immigration',
    subtext: 'Visa, company, work strategy',
    accent: '#0f766e',
    icon: BriefcaseBusiness,
  },
  first1000: {
    label: 'First 1000 Days',
    subtext: 'Banking, health, housing, taxes',
    accent: '#2563eb',
    icon: Compass,
  },
}

const GUIDED_SCENARIOS: GuidedScenario[] = [
  {
    id: 'founder-pathway-rehearsal',
    track: 'founder',
    title: 'Founder pathway rehearsal',
    description: 'Compare O-1, EB-1A, International Entrepreneur Rule, company setup, runway timing, and staying in the US.',
    situation:
      'I am an immigrant founder trying to stay in the US while building a company. I want to compare O-1, EB-1A, and the International Entrepreneur Rule, understand company setup needs, and avoid runway timing surprises.',
    keyFacts: {
      currentStatus: 'In the US on a temporary status',
      goal: 'Keep building the company while preparing a stronger long-term pathway',
      deadline: 'Need a credible plan before the next funding and status milestone',
      location: 'United States',
      workCompanyFacts: 'Early-stage company, US customers, evidence still scattered',
      familyDependents: 'Need to understand dependent impact before acting',
    },
    uncertaintyChips: ['I need professional review', 'Deadline is uncertain', 'I am worried about sharing details'],
  },
  {
    id: 'first-90-days-setup',
    track: 'first1000',
    title: 'First 90 days setup',
    description: 'Sequence SSN/ITIN, bank account, credit, health coverage, housing, taxes, and local rights.',
    situation:
      'I recently arrived and need to sequence the first setup decisions: SSN/ITIN, bank account, credit, health coverage, housing, taxes, and local rights without missing a deadline.',
    keyFacts: {
      currentStatus: 'Recently arrived and still learning local systems',
      goal: 'Build a stable first-90-days setup plan',
      deadline: 'Need the basics in place over the next three months',
      location: 'United States',
      workCompanyFacts: 'Income and paperwork are still changing',
      familyDependents: 'Family needs may affect health coverage and housing choices',
    },
    uncertaintyChips: ['I am not sure about my status', 'Money is tight', 'I do not know which agency applies'],
  },
]

const KEY_FACT_FIELDS: Array<{ key: keyof KeyFacts; label: string; placeholder: string }> = [
  { key: 'currentStatus', label: 'Current status', placeholder: 'Current visa, arrival, or setup status' },
  { key: 'goal', label: 'Goal', placeholder: 'What you are trying to make possible' },
  { key: 'deadline', label: 'Deadline', placeholder: 'Key date or timing pressure' },
  { key: 'location', label: 'Location', placeholder: 'City, state, or country context' },
  { key: 'workCompanyFacts', label: 'Work or company facts', placeholder: 'Employer, company, income, or evidence notes' },
  { key: 'familyDependents', label: 'Family or dependents', placeholder: 'Who else is affected' },
]

const UNCERTAINTY_CHIPS = [
  'I am not sure about my status',
  'Deadline is uncertain',
  'I need professional review',
  'Money is tight',
  'I do not know which agency applies',
  'I am worried about sharing details',
]

const SAFETY_NOTE =
  'CivicBridge is a planning aid, not legal advice. It helps organize risks, questions, and next steps so you can verify details with official sources or a qualified professional. Avoid entering documents or secrets in this demo.'

const ADVISOR_PREVIEW: Record<CivicBridgeTrack, string[]> = {
  founder: ['Immigration Attorney', 'Evidence Coach', 'Founder Mentor', 'Tax/Company Navigator'],
  first1000: ['Banking', 'Healthcare', 'Housing', 'Tax', 'Local Systems'],
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

function SimulateInner() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isDemo = searchParams.get('demo') === 'true'
  const defaultScenario = GUIDED_SCENARIOS.find((scenario) => scenario.track === 'founder')!

  const [track, setTrack] = useState<CivicBridgeTrack>('founder')
  const [decision, setDecision] = useState(defaultScenario.situation)
  const [selectedScenarioId, setSelectedScenarioId] = useState(defaultScenario.id)
  const [keyFacts, setKeyFacts] = useState<KeyFacts>(defaultScenario.keyFacts)
  const [selectedUncertaintyChips, setSelectedUncertaintyChips] = useState<string[]>(defaultScenario.uncertaintyChips)
  const [runId, setRunId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [engine, setEngine] = useState<SimulationEngine>('swarm')
  const [swarmSize, setSwarmSize] = useState(24)
  const [maxActivePerRound, setMaxActivePerRound] = useState(8)
  const feedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isDemo) {
      setDecision(defaultScenario.situation)
      setKeyFacts(defaultScenario.keyFacts)
      setSelectedUncertaintyChips(defaultScenario.uncertaintyChips)
      setSelectedScenarioId(defaultScenario.id)
    }
  }, [defaultScenario.id, defaultScenario.keyFacts, defaultScenario.situation, defaultScenario.uncertaintyChips, isDemo])

  const { events, status } = useSimulationStream(runId)
  const messages: MessageDict[] = eventsToMessages(events)
  const conflicts: ConflictDict[] = eventsToConflicts(events)
  const swarm = swarmStats(events)

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight
    }
  }, [messages.length])

  function selectTrack(nextTrack: CivicBridgeTrack) {
    if (runId) return
    setTrack(nextTrack)
    const scenario = GUIDED_SCENARIOS.find((item) => item.track === nextTrack)
    if (scenario) {
      setDecision(scenario.situation)
      setKeyFacts(scenario.keyFacts)
      setSelectedUncertaintyChips(scenario.uncertaintyChips)
      setSelectedScenarioId(scenario.id)
    } else {
      setKeyFacts(EMPTY_KEY_FACTS)
      setSelectedScenarioId('')
      setSelectedUncertaintyChips([])
    }
  }

  function selectScenario(scenario: GuidedScenario) {
    if (runId) return
    setTrack(scenario.track)
    setDecision(scenario.situation)
    setKeyFacts(scenario.keyFacts)
    setSelectedUncertaintyChips(scenario.uncertaintyChips)
    setSelectedScenarioId(scenario.id)
  }

  function updateKeyFact(key: keyof KeyFacts, value: string) {
    setKeyFacts((current) => ({ ...current, [key]: value }))
  }

  function toggleUncertaintyChip(chip: string) {
    if (runId) return
    setSelectedUncertaintyChips((current) =>
      current.includes(chip) ? current.filter((item) => item !== chip) : [...current, chip],
    )
  }

  function buildScenarioText() {
    const nonEmptyFacts = KEY_FACT_FIELDS
      .map((field) => [field.label, keyFacts[field.key].trim()] as const)
      .filter(([, value]) => value.length > 0)
      .map(([label, value]) => `- ${label}: ${value}`)
      .join('\n')

    const uncertaintyText = selectedUncertaintyChips.length
      ? selectedUncertaintyChips.map((chip) => `- ${chip}`).join('\n')
      : '- None selected'

    return [
      `Track: ${TRACKS[track].label}`,
      '',
      'Situation:',
      decision.trim(),
      '',
      'Key facts:',
      nonEmptyFacts || '- Not provided yet',
      '',
      'Uncertainty and review flags:',
      uncertaintyText,
    ].join('\n')
  }

  async function handleRun() {
    if (!decision.trim()) return
    setLoading(true)
    setError(null)
    try {
      const run = await startSimulation(buildScenarioText(), [...COMPATIBILITY_DEPTS], {
        engine,
        rounds: engine === 'swarm' ? 4 : 15,
        swarmSize: engine === 'swarm' ? swarmSize : undefined,
        maxActivePerRound: engine === 'swarm' ? maxActivePerRound : undefined,
      })
      setRunId(run.run_id)
      localStorage.setItem('civicbridge_last_run_id', run.run_id)
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
              <span className="text-blue-400">-</span>
              <span>Pre-filled with a founder pathway rehearsal. Press Run to begin.</span>
            </div>
          )}

          <section className="space-y-3">
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-gray-900">Choose a track</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {(Object.keys(TRACKS) as CivicBridgeTrack[]).map((trackId) => {
                  const item = TRACKS[trackId]
                  const Icon = item.icon
                  const active = track === trackId
                  return (
                    <button
                      key={trackId}
                      type="button"
                      onClick={() => selectTrack(trackId)}
                      disabled={!!runId}
                      className={`rounded-md border px-3 py-2 text-left transition-colors disabled:cursor-not-allowed ${
                        active ? 'bg-gray-950 text-white border-gray-950' : 'bg-white text-gray-700 border-gray-200 hover:border-gray-400'
                      }`}
                    >
                      <span className="flex items-center gap-2 text-sm font-semibold">
                        <Icon className="h-4 w-4" aria-hidden="true" />
                        {item.label}
                      </span>
                      <span className={`mt-1 block text-xs ${active ? 'text-gray-200' : 'text-gray-500'}`}>{item.subtext}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-gray-900">Start from a demo scenario</h2>
              <div className="space-y-2">
                {GUIDED_SCENARIOS.filter((scenario) => scenario.track === track).map((scenario) => {
                  const active = selectedScenarioId === scenario.id
                  return (
                    <button
                      key={scenario.id}
                      type="button"
                      onClick={() => selectScenario(scenario)}
                      disabled={!!runId}
                      className={`w-full rounded-md border px-3 py-2 text-left transition-colors disabled:cursor-not-allowed ${
                        active ? 'border-gray-900 bg-gray-50' : 'border-gray-200 bg-white hover:border-gray-400'
                      }`}
                    >
                      <span className="block text-sm font-semibold text-gray-900">{scenario.title}</span>
                      <span className="mt-1 block text-xs leading-5 text-gray-500">{scenario.description}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-gray-900">Situation</h2>
              <textarea
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-gray-900 min-h-[108px] disabled:bg-gray-50 disabled:text-gray-500"
                rows={5}
                placeholder="Describe your goal, current status, deadline, location, and what feels uncertain."
                value={decision}
                onChange={(e) => {
                  setDecision(e.target.value)
                  setSelectedScenarioId('')
                }}
                disabled={!!runId}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {KEY_FACT_FIELDS.map((field) => (
                <label key={field.key} className="space-y-1">
                  <span className="text-xs font-semibold text-gray-700">{field.label}</span>
                  <input
                    value={keyFacts[field.key]}
                    onChange={(event) => updateKeyFact(field.key, event.target.value)}
                    disabled={!!runId}
                    placeholder={field.placeholder}
                    className="w-full rounded-md border border-gray-200 px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900 disabled:bg-gray-50 disabled:text-gray-500"
                  />
                </label>
              ))}
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-gray-700">Uncertainty and privacy</h3>
              <div className="flex flex-wrap gap-1.5">
                {UNCERTAINTY_CHIPS.map((chip) => {
                  const active = selectedUncertaintyChips.includes(chip)
                  return (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => toggleUncertaintyChip(chip)}
                      disabled={!!runId}
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed ${
                        active ? 'border-transparent text-white' : 'border-gray-200 bg-white text-gray-600 hover:border-gray-400'
                      }`}
                      style={active ? { backgroundColor: TRACKS[track].accent } : undefined}
                    >
                      {chip}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
              <span className="inline-flex items-center gap-1.5 font-semibold">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                Safety note
              </span>
              <p className="mt-1">{SAFETY_NOTE}</p>
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
                  Cascade
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
                  Swarm
                </label>
              </div>
              {engine === 'swarm' && (
                <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600">
                  <label className="flex items-center gap-2">
                    <span className="whitespace-nowrap">Pool size</span>
                    <input
                      type="number"
                      min={16}
                      max={256}
                      step={8}
                      value={swarmSize}
                      onChange={(e) => setSwarmSize(Number(e.target.value) || 24)}
                      disabled={!!runId}
                      className="w-20 rounded border border-gray-200 px-2 py-1 text-xs"
                    />
                  </label>
                  <label className="flex items-center gap-2">
                    <span className="whitespace-nowrap">Active/round</span>
                    <input
                      type="number"
                      min={4}
                      max={24}
                      step={1}
                      value={maxActivePerRound}
                      onChange={(e) => setMaxActivePerRound(Number(e.target.value) || 8)}
                      disabled={!!runId}
                      className="w-20 rounded border border-gray-200 px-2 py-1 text-xs"
                    />
                  </label>
                </div>
              )}
            </div>

            {error && <p className="text-red-500 text-xs break-words">{error}</p>}
            <button
              onClick={handleRun}
              disabled={loading || !!runId || !decision.trim()}
              className="w-full px-4 py-2 rounded-md bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Starting...' : runId ? 'Rehearsal running' : 'Run rehearsal'}
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

          {/* Risks list */}
          {runId && conflicts.length > 0 && (
            <>
              <div className="border-t border-gray-100" />
              <section className="space-y-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-gray-900">Detected risks</h2>
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
              View action report →
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
              {!runId ? 'Risk Map Preview' : engine === 'swarm' ? 'Advisor Deliberation' : 'Risk Map'}
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
              <span className="text-red-500 font-medium">{conflicts.length} risk{conflicts.length !== 1 ? 's' : ''}</span>
            )}
            {!runId && (
              <span className="text-gray-400">Run a rehearsal to see risks</span>
            )}
          </div>
        </div>

        {/* Graph */}
        <div className="flex-1 min-h-0 p-2">
          {!runId ? (
            <div className="h-full rounded-md border border-gray-200 bg-white p-5 flex flex-col">
              <div>
                <h2 className="text-sm font-semibold text-gray-900">Risk Map Preview</h2>
                <p className="mt-1 text-xs leading-5 text-gray-500">
                  Run a rehearsal to see advisor perspectives, risks, and next steps appear here.
                </p>
              </div>
              <div className="mt-5 grid flex-1 min-h-[240px] grid-cols-2 gap-3 content-center sm:grid-cols-3">
                {ADVISOR_PREVIEW[track].map((advisor, index) => (
                  <div
                    key={advisor}
                    className="min-h-24 rounded-md border border-gray-200 bg-gray-50 px-3 py-3 flex flex-col justify-between"
                  >
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: TRACKS[track].accent, opacity: 0.65 + index * 0.07 }}
                    />
                    <span className="text-xs font-semibold leading-4 text-gray-800">{advisor}</span>
                    <span className="text-[10px] text-gray-400">advisor perspective</span>
                  </div>
                ))}
              </div>
            </div>
          ) : engine === 'swarm' ? (
            <SwarmInteractionGraph events={events} />
          ) : (
            <ConflictGraph conflicts={conflicts} messages={messages} />
          )}
        </div>

        {/* Legend */}
        <div className="flex-shrink-0 px-5 py-2.5 border-t border-gray-100 bg-white flex items-center gap-4 flex-wrap">
          {engine === 'swarm' ? (
            <>
              <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wide">Advisor legend</span>
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
