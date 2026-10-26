'use client'

import { useEffect, useRef, useState } from 'react'

export type DomainFeedKey = 'sales' | 'finance' | 'operations' | 'hr'

const DOMAIN_ADVISOR: Record<DomainFeedKey, string> = {
  sales: 'VP of Sales',
  finance: 'CFO',
  operations: 'Operations Lead',
  hr: 'HR Director',
}

const FAKE_MESSAGES: Record<DomainFeedKey, { agent_role: string; content: string }[]> = {
  sales: [
    {
      agent_role: 'VP of Sales',
      content:
        'A 20% Q4 marketing cut hits pipeline coverage before it hits the P&L. Three deals in late stage depend on the campaigns this budget funds.',
    },
    {
      agent_role: 'VP of Sales',
      content:
        'Win rate is 34% on $4.2M of open pipeline. Cutting demand gen in the quarter we need to close is how coverage falls under 3x.',
    },
  ],
  finance: [
    {
      agent_role: 'CFO',
      content:
        'Runway is the constraint. The marketing line is discretionary spend we can pause without touching headcount or the infra bill.',
    },
    {
      agent_role: 'CFO',
      content:
        'I will take a pipeline-risk note from Sales. I will not approve holding the full Q4 budget when the cost reduction is the decision already made.',
    },
  ],
  operations: [
    {
      agent_role: 'Operations Lead',
      content:
        'If Sales still has to deliver the quarter, implementation capacity does not shrink with the marketing budget. We are already at the service-capacity limit.',
    },
    {
      agent_role: 'Operations Lead',
      content:
        'A cut that slips close dates into next quarter just moves the load. Flag the handoff dates before Finance locks the number.',
    },
  ],
  hr: [
    {
      agent_role: 'HR Director',
      content:
        'Quota pressure plus a public budget cut reads as instability to the AE team. Attrition risk shows up in the roles we cannot backfill this quarter.',
    },
    {
      agent_role: 'HR Director',
      content:
        'Do not pair this cut with a hiring freeze on the same team that has to carry the pipeline. That is the conflict, not the dollar amount.',
    },
  ],
}

function initials(role: string) {
  return role
    .split(/[\s_]/)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function relativeTime(ts: number) {
  const diff = Math.floor((Date.now() - ts) / 1000)
  if (diff < 5) return 'just now'
  if (diff < 60) return `${diff}s ago`
  return `${Math.floor(diff / 60)}m ago`
}

function titleAbbr(title: string) {
  const parts = title.split(/[\s&]+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0]![0] + parts[1]![0]).toUpperCase()
  return title.slice(0, 2).toUpperCase()
}

interface FakeMessage {
  id: string
  agent_role: string
  content: string
  timestamp: number
  round: number
}

interface Props {
  domainKey: DomainFeedKey
  title: string
  color: string
  onClose: () => void
}

export function DeptFeedDrawer({ domainKey, title, color, onClose }: Props) {
  const [messages, setMessages] = useState<FakeMessage[]>([])
  const [isLive, setIsLive] = useState(false)
  const [done, setDone] = useState(false)
  const feedRef = useRef<HTMLDivElement>(null)
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([])
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [, setTick] = useState(0)

  const advisor = DOMAIN_ADVISOR[domainKey]

  // Start streaming fake messages
  useEffect(() => {
    const pool = FAKE_MESSAGES[domainKey] ?? []
    if (pool.length === 0) return

    const start = setTimeout(() => {
      setIsLive(true)
      setMessages([])
      setDone(false)
    }, 0)
    timeoutsRef.current.push(start)

    const delays = [800, 2200, 4100, 6300, 9000, 12500, 16500]
    pool.forEach((msg, i) => {
      const t = setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            id: `${domainKey}-${i}`,
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

    tickRef.current = setInterval(() => setTick((n) => n + 1), 10_000)

    return () => {
      timeoutsRef.current.forEach(clearTimeout)
      timeoutsRef.current = []
      if (tickRef.current) clearInterval(tickRef.current)
    }
  }, [domainKey])

  // Auto-scroll
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [messages.length])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <>
      <div className="fixed inset-0 bg-black/20 backdrop-blur-[1px] z-40" onClick={onClose} />

      <div className="fixed top-0 right-0 h-full w-full max-w-sm bg-white shadow-2xl z-50 flex flex-col">
        <div
          className="flex items-center justify-between px-5 py-4 border-b border-gray-100"
          style={{ borderLeftColor: color, borderLeftWidth: 3 }}
        >
          <div className="flex items-center gap-2.5">
            <span
              className="w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0"
              style={{ backgroundColor: color }}
            >
              {titleAbbr(title)}
            </span>
            <div>
              <p className="text-sm font-bold text-gray-900 leading-tight">{title}</p>
              <p className="text-[10px] text-gray-400 leading-tight">{advisor} · sample rehearsal feed</p>
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

        <div className="px-5 py-2 border-b border-gray-50 bg-gray-50">
          {isLive ? (
            <p className="text-xs text-green-600 font-medium">Live — sample advisor messages for {title}</p>
          ) : done ? (
            <p className="text-xs text-gray-500">
              Sample complete — {messages.length} messages (rehearsal illustration only)
            </p>
          ) : (
            <p className="text-xs text-gray-400 flex items-center gap-1.5">
              <span className="inline-block w-2.5 h-2.5 rounded-full border-2 border-gray-300 border-t-gray-600 animate-spin" />
              Connecting…
            </p>
          )}
        </div>

        <div ref={feedRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3 text-gray-400">
              <span
                className="w-12 h-12 rounded-full flex items-center justify-center text-white text-xs font-bold opacity-30"
                style={{ backgroundColor: color }}
              >
                {titleAbbr(title)}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-500">Waiting for sample messages…</p>
                <p className="text-xs text-gray-400 mt-0.5">Not legal advice — use Rehearse for a full run.</p>
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

        <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
          <span className="text-[10px] text-gray-300">
            {messages.length} message{messages.length !== 1 ? 's' : ''}
          </span>
          <a href="/simulate" className="text-xs text-gray-500 hover:text-gray-800 transition-colors">
            Go to rehearsal →
          </a>
        </div>
      </div>
    </>
  )
}
