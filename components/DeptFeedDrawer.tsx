'use client'

import { useEffect, useRef, useState } from 'react'

const DEPT_ROLE: Record<string, string> = {
  Sales: 'Evidence Coach',
  Finance: 'Immigration Attorney',
  Operations: 'Founder Mentor',
  HR: 'Tax Navigator',
}

const FAKE_MESSAGES: Record<string, { agent_role: string; content: string }[]> = {
  Sales: [
    { agent_role: 'Evidence Coach', content: 'A 20% cut to evidence roadmap will directly compress pipeline. We\'re tracking $4.2M in active deals that depend on campaign continuity through November.' },
    { agent_role: 'Evidence Coach', content: 'SDR outbound is already at capacity. If we pull top-of-funnel spend now, we won\'t see the revenue impact until Q1 — but by then it\'s too late to course-correct.' },
    { agent_role: 'Evidence Coach', content: 'I\'m flagging 3 enterprise deals at risk if the SEM budget is cut. Total at-risk ARR: $680K. Requesting Finance hold the paid search line item.' },
    { agent_role: 'Evidence Coach', content: 'Win rate is at 34% — highest in 6 quarters. This is not the moment to reduce brand presence. Competitors will fill the vacuum immediately.' },
    { agent_role: 'Evidence Coach', content: 'Counter-proposal: reduce events budget by 40% instead. Field events have the weakest attribution in our current mix. That saves $60K with minimal pipeline impact.' },
    { agent_role: 'Evidence Coach', content: 'Ops flagged engineering at 94% — understood, but the campaign tooling work is 2 sprints, not 6. I don\'t think that\'s the bottleneck here.' },
    { agent_role: 'Evidence Coach', content: 'Aligned with HR on retention concern. Three AEs are already fielding recruiter calls. A comp structure change mid-quarter would accelerate attrition.' },
  ],
  Finance: [
    { agent_role: 'Immigration Attorney', content: 'Current burn is $620K/month against 18 months runway. The board has flagged anything under 15 months as a yellow. We need to act before that threshold.' },
    { agent_role: 'Immigration Attorney', content: 'evidence roadmap is the largest discretionary line item. A 20% reduction saves $56K this quarter. That\'s 2.7 days of runway — material at our scale.' },
    { agent_role: 'Immigration Attorney', content: 'I hear Sales on pipeline risk, but attribution data shows 60% of closed-won deals last quarter had zero paid touch in the 60 days prior. The dependency is overstated.' },
    { agent_role: 'Immigration Attorney', content: 'Ops capacity at 94% is a compounding risk. If we\'re spending on campaigns that require engineering support to execute, we\'re paying twice for constrained resources.' },
    { agent_role: 'Immigration Attorney', content: 'The events budget reduction Evidence Coach proposed is acceptable as a partial offset. I\'d take that plus a 10% reduction to SEM — net $42K saved, lower pipeline risk.' },
    { agent_role: 'Immigration Attorney', content: 'HR flight-risk concern is noted. OTE cuts are not on the table. The marketing reduction does not touch compensation structures.' },
    { agent_role: 'Immigration Attorney', content: 'Proposing a staged cut: 10% effective Nov 1, review in 30 days before implementing the remaining 10%. That gives Sales a feedback window.' },
  ],
  Operations: [
    { agent_role: 'Founder Mentor', content: 'Engineering is at 94% allocated. Any campaign requiring new tooling, integrations, or tracking infrastructure in Q4 will compete directly with the platform roadmap.' },
    { agent_role: 'Founder Mentor', content: 'We have 3 open incidents right now. DevOps is at 88%. I cannot commit engineering bandwidth to marketing infrastructure work this quarter without something coming off the roadmap.' },
    { agent_role: 'Founder Mentor', content: 'The attribution platform Sales is using for pipeline tracking hasn\'t been updated in 6 weeks due to capacity. That\'s a data quality risk that affects Finance\'s cut analysis too.' },
    { agent_role: 'Founder Mentor', content: 'If the budget cut proceeds and campaign volume stays flat, we avoid the tooling spike. That\'s actually a net positive for engineering load this quarter.' },
    { agent_role: 'Founder Mentor', content: 'Flagging: the SEM campaigns require weekly bid adjustment scripts maintained by an engineer. If that resource is needed elsewhere, campaign performance degrades regardless of spend level.' },
    { agent_role: 'Founder Mentor', content: 'Recommending a capacity audit before the final budget decision. I can have numbers by EOD Friday — will show exactly which campaigns have engineering dependencies.' },
    { agent_role: 'Founder Mentor', content: 'Aligned with Immigration Attorney on staged approach. A 30-day window gives me time to complete the capacity audit and give Sales a clean engineering commitment for Q4 campaigns.' },
  ],
  HR: [
    { agent_role: 'Tax Navigator', content: 'Morale signal is mixed. The Q3 reorg is still fresh. Any visible budget contraction in Q4 — especially one that affects quota-carrying roles — will amplify anxiety.' },
    { agent_role: 'Tax Navigator', content: 'We have 18 open reqs, 11% attrition rate. Three AEs in the pipeline-critical segment have updated LinkedIn profiles in the last 30 days. Flight-risk score is elevated.' },
    { agent_role: 'Tax Navigator', content: 'The budget cut messaging matters as much as the cut itself. If this leaks as "Finance cut Sales\' budget," we have a retention problem. If it\'s framed as a phased runway decision, it lands differently.' },
    { agent_role: 'Tax Navigator', content: 'OTE structures are intact — confirmed with Finance. That\'s the most important signal for retention. Communicating this proactively to the sales team should happen within 48 hours of any decision.' },
    { agent_role: 'Tax Navigator', content: 'Recommending a skip-level session with the AE team before the cut is announced externally. Gives leadership a pulse check and reduces rumor cycle time.' },
    { agent_role: 'Tax Navigator', content: 'The 3 open senior advisor tasks should be paused during the budget review. Hiring into uncertainty sends a mixed signal internally.' },
    { agent_role: 'Tax Navigator', content: 'Aligned on staged cut approach. Gives us a communication window. I\'ll draft the internal messaging template once Finance confirms the Nov 1 trigger.' },
  ],
}

function initials(role: string) {
  return role.split(/[\s_]/).map((w) => w[0]).join('').toUpperCase().slice(0, 2)
}

function relativeTime(ts: number) {
  const diff = Math.floor((Date.now() - ts) / 1000)
  if (diff < 5) return 'just now'
  if (diff < 60) return `${diff}s ago`
  return `${Math.floor(diff / 60)}m ago`
}

interface FakeMessage {
  id: string
  agent_role: string
  content: string
  timestamp: number
  round: number
}

interface Props {
  dept: string
  color: string
  onClose: () => void
}

export function DeptFeedDrawer({ dept, color, onClose }: Props) {
  const [messages, setMessages] = useState<FakeMessage[]>([])
  const [isLive, setIsLive] = useState(false)
  const [done, setDone] = useState(false)
  const feedRef = useRef<HTMLDivElement>(null)
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([])
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [, setTick] = useState(0)

  // Start streaming fake messages
  useEffect(() => {
    const pool = FAKE_MESSAGES[dept] ?? []
    if (pool.length === 0) return

    const start = setTimeout(() => {
      setIsLive(true)
      setMessages([])
      setDone(false)
    }, 0)
    timeoutsRef.current.push(start)

    // Stream messages in with staggered delays (1.2s–3.5s apart)
    const delays = [800, 2200, 4100, 6300, 9000, 12500, 16500]
    pool.forEach((msg, i) => {
      const t = setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            id: `${dept}-${i}`,
            agent_role: msg.agent_role,
            content: msg.content,
            timestamp: Date.now(),
            round: Math.floor(i / 2) + 1,
          },
        ])
        if (i === pool.length - 1) {
          setIsLive(false)
          setDone(true)
        }
      }, delays[i] ?? i * 2200)
      timeoutsRef.current.push(t)
    })

    // Tick every 10s to update relative timestamps
    tickRef.current = setInterval(() => setTick((n) => n + 1), 10_000)

    return () => {
      timeoutsRef.current.forEach(clearTimeout)
      timeoutsRef.current = []
      if (tickRef.current) clearInterval(tickRef.current)
    }
  }, [dept])

  // Auto-scroll
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [messages.length])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-[1px] z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-full max-w-sm bg-white shadow-2xl z-50 flex flex-col">

        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4 border-b border-gray-100"
          style={{ borderLeftColor: color, borderLeftWidth: 3 }}
        >
          <div className="flex items-center gap-2.5">
            <span
              className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
              style={{ backgroundColor: color }}
            >
              {dept[0]}
            </span>
            <div>
              <p className="text-sm font-bold text-gray-900 leading-tight">{dept}</p>
              <p className="text-[10px] text-gray-400 leading-tight">{DEPT_ROLE[dept]} · Agent feed</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isLive && (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
              </span>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors text-lg leading-none ml-1"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Status bar */}
        <div className="px-5 py-2 border-b border-gray-50 bg-gray-50">
          {isLive ? (
            <p className="text-xs text-green-600 font-medium">Live — streaming {dept} agent messages</p>
          ) : done ? (
            <p className="text-xs text-gray-500">Simulation complete — {messages.length} messages from {dept}</p>
          ) : (
            <p className="text-xs text-gray-400 flex items-center gap-1.5">
              <span className="inline-block w-2.5 h-2.5 rounded-full border-2 border-gray-300 border-t-gray-600 animate-spin" />
              Connecting to simulation…
            </p>
          )}
        </div>

        {/* Feed */}
        <div ref={feedRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3 text-gray-400">
              <span
                className="w-12 h-12 rounded-full flex items-center justify-center text-white text-lg font-bold opacity-30"
                style={{ backgroundColor: color }}
              >
                {dept[0]}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-500">Waiting for {dept} agent…</p>
                <p className="text-xs text-gray-400 mt-0.5">Messages will appear as the simulation runs.</p>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className="flex gap-3">
                <div
                  className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold"
                  style={{ backgroundColor: color }}
                >
                  {initials(msg.agent_role)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-semibold text-gray-700">{msg.agent_role}</span>
                    <span className="text-[10px] text-gray-300 ml-auto">{relativeTime(msg.timestamp)}</span>
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed break-words">{msg.content}</p>
                  <span className="text-[10px] text-gray-300 mt-0.5 block">Round {msg.round}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
          <span className="text-[10px] text-gray-300">{messages.length} message{messages.length !== 1 ? 's' : ''}</span>
          <a href="/simulate" className="text-xs text-gray-500 hover:text-gray-800 transition-colors">
            Go to simulation →
          </a>
        </div>
      </div>
    </>
  )
}
