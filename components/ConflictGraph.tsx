'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { useMessages, useTranslations } from 'next-intl'
import type { ConflictDict, MessageDict } from '@/lib/types'

const W = 400
const H = 460

const COLOR_PALETTE = [
  '#185FA5',
  '#854F0B',
  '#0F6E56',
  '#534AB7',
  '#b45309',
  '#0369a1',
  '#7c3aed',
  '#be185d',
]

function hashStr(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i)
  return Math.abs(h)
}

function colorForLane(id: string): string {
  return COLOR_PALETTE[hashStr(id) % COLOR_PALETTE.length]
}

function collectLaneIds(conflicts: ConflictDict[], streamMessages: MessageDict[]): string[] {
  const s = new Set<string>()
  for (const c of conflicts) {
    if (c.dept_a?.trim()) s.add(c.dept_a.trim())
    if (c.dept_b?.trim()) s.add(c.dept_b.trim())
  }
  for (const m of streamMessages) {
    if (m.department?.trim()) s.add(m.department.trim())
  }
  return Array.from(s).sort((a, b) => a.localeCompare(b))
}

function layoutTargets(ids: string[]): Record<string, { x: number; y: number }> {
  const n = ids.length
  const cx = W / 2
  const cy = H / 2
  const r = Math.min(W, H) * 0.36
  const out: Record<string, { x: number; y: number }> = {}
  if (n === 0) return out
  ids.forEach((id, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2
    out[id] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) }
  })
  return out
}

type GraphMetaKey =
  | 'evidence'
  | 'immigration'
  | 'tax'
  | 'bank'
  | 'health'
  | 'housing'
  | 'workAuth'
  | 'founder'
  | 'default'

function laneMetaKey(id: string): GraphMetaKey {
  const lower = id.toLowerCase()
  if (lower.includes('evidence') || lower.includes('filing')) return 'evidence'
  if (lower.includes('counsel') || lower.includes('immigration') || lower.includes('legal')) return 'immigration'
  if (lower.includes('tax') || lower.includes('payroll')) return 'tax'
  if (lower.includes('bank')) return 'bank'
  if (lower.includes('health')) return 'health'
  if (lower.includes('housing') || lower.includes('lease')) return 'housing'
  if (lower.includes('work authorization') || lower.includes('ead')) return 'workAuth'
  if (lower.includes('founder') || lower.includes('readiness')) return 'founder'
  return 'default'
}

function initialLetter(id: string): string {
  const m = id.match(/[A-Za-z0-9]/)
  return m ? m[0].toUpperCase() : '?'
}

function truncateLabel(id: string, max = 18): string {
  return id.length <= max ? id : `${id.slice(0, max - 1)}…`
}

const SEVERITY_COLOR: Record<string, string> = {
  low: '#fbbf24',
  medium: '#f97316',
  high: '#ef4444',
}
const SEVERITY_WIDTH: Record<string, number> = {
  low: 2,
  medium: 3.5,
  high: 5,
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string
  color: string
  tx: number
  ty: number
}
interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  key: string
  severity: string
  conflict_type: string
}
interface Props {
  conflicts: ConflictDict[]
  streamMessages?: MessageDict[]
}

type IntlGraphMeta = Record<string, { role: string; agent: string; bias: string }>

export function ConflictGraph({ conflicts, streamMessages = [] }: Props) {
  const t = useTranslations('graph')
  const ts = useTranslations('simulate')
  const intl = useMessages() as {
    graph?: { meta?: IntlGraphMeta }
    simulate?: { conflictTypes?: Record<string, string> }
  }

  const svgRef = useRef<SVGSVGElement>(null)
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null)
  const gRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  const laneIds = useMemo(() => collectLaneIds(conflicts, streamMessages), [conflicts, streamMessages])
  const laneKey = laneIds.join('\0')

  // ── Build / rebuild simulation when advisor lanes change ───────────────────
  useEffect(() => {
    const svgEl = svgRef.current
    if (!svgEl) return

    simRef.current?.stop()

    const svg = d3.select(svgEl)
    svg.selectAll('*').remove()

    const targets = layoutTargets(laneIds)
    const nodes: SimNode[] = laneIds.map((id) => {
      const t = targets[id] ?? { x: W / 2, y: H / 2 }
      return {
        id,
        color: colorForLane(id),
        tx: t.x,
        ty: t.y,
        x: t.x + (Math.random() - 0.5) * 40,
        y: t.y + (Math.random() - 0.5) * 40,
      }
    })

    const g = svg.append('g')
    gRef.current = g
    g.append('g').attr('class', 'links')
    g.append('g').attr('class', 'nodes')

    const sim = d3
      .forceSimulation<SimNode, SimLink>(nodes)
      .force('x', d3.forceX<SimNode>((d) => d.tx).strength(0.5))
      .force('y', d3.forceY<SimNode>((d) => d.ty).strength(0.5))
      .force('charge', d3.forceManyBody<SimNode>().strength(-140))
      .force('link', d3.forceLink<SimNode, SimLink>([]).id((d) => d.id).distance(150))
      .on('tick', () => {
        g.select('g.nodes')
          .selectAll<SVGGElement, SimNode>('g.node')
          .attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
        g.select('g.links')
          .selectAll<SVGLineElement, SimLink>('line')
          .attr('x1', (d) => (d.source as SimNode).x ?? 0)
          .attr('y1', (d) => (d.source as SimNode).y ?? 0)
          .attr('x2', (d) => (d.target as SimNode).x ?? 0)
          .attr('y2', (d) => (d.target as SimNode).y ?? 0)
      })

    simRef.current = sim

    const drag = d3
      .drag<SVGGElement, SimNode>()
      .on('start', (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) sim.alphaTarget(0)
        d.fx = null
        d.fy = null
      })

    const nodeG = g
      .select('g.nodes')
      .selectAll<SVGGElement, SimNode>('g.node')
      .data(nodes, (d) => d.id)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('cursor', 'pointer')
      .attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
      .call(drag)
      .on('click', (_event, d) => {
        svgEl.dispatchEvent(new CustomEvent('node-click', { detail: d.id, bubbles: true }))
      })

    nodeG
      .append('circle')
      .attr('class', 'ring')
      .attr('r', 24)
      .attr('fill', 'none')
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', 2.5)
      .attr('opacity', 0)

    nodeG
      .append('circle')
      .attr('r', 22)
      .attr('fill', (d) => d.color)
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 2.5)

    nodeG
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', '#ffffff')
      .attr('font-size', 13)
      .attr('font-weight', 700)
      .attr('pointer-events', 'none')
      .text((d) => initialLetter(d.id))

    nodeG
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', 36)
      .attr('fill', '#4b5563')
      .attr('font-size', 11)
      .attr('font-weight', 600)
      .attr('pointer-events', 'none')
      .text((d) => truncateLabel(d.id))

    return () => {
      sim.stop()
    }
  }, [laneKey, laneIds])

  // ── Listen for node-click custom events ─────────────────────────────────────
  useEffect(() => {
    const el = svgRef.current
    if (!el) return
    const handler = (e: Event) => {
      const dept = (e as CustomEvent<string>).detail
      setSelected((prev) => (prev === dept ? null : dept))
    }
    el.addEventListener('node-click', handler)
    return () => el.removeEventListener('node-click', handler)
  }, [])

  // ── Dismiss card on outside click ───────────────────────────────────────────
  useEffect(() => {
    if (!selected) return
    const handler = (e: MouseEvent) => {
      const card = document.getElementById('node-info-card')
      if (card && !card.contains(e.target as Node)) setSelected(null)
    }
    window.addEventListener('mousedown', handler)
    return () => window.removeEventListener('mousedown', handler)
  }, [selected])

  // ── Update links ─────────────────────────────────────────────────────────────
  useEffect(() => {
    const sim = simRef.current
    const g = gRef.current
    if (!sim || !g) return
    const known = new Set(laneIds)
    const edgeMap = new Map<string, SimLink>()
    const rank: Record<string, number> = { low: 0, medium: 1, high: 2 }
    for (const c of conflicts) {
      if (!known.has(c.dept_a) || !known.has(c.dept_b) || c.dept_a === c.dept_b) continue
      const key = [c.dept_a, c.dept_b].sort().join('|')
      const ex = edgeMap.get(key)
      if (!ex || rank[c.severity] > rank[ex.severity])
        edgeMap.set(key, {
          key,
          source: c.dept_a,
          target: c.dept_b,
          severity: c.severity,
          conflict_type: c.conflict_type,
        })
    }
    const links = Array.from(edgeMap.values())
    const sel = g.select<SVGGElement>('g.links').selectAll<SVGLineElement, SimLink>('line').data(links, (d) => d.key)
    sel
      .enter()
      .append('line')
      .attr('stroke', (d) => SEVERITY_COLOR[d.severity] ?? '#ef4444')
      .attr('stroke-width', (d) => SEVERITY_WIDTH[d.severity] ?? 3)
      .attr('stroke-linecap', 'round')
      .attr('stroke-opacity', 0)
      .transition()
      .duration(700)
      .attr('stroke-opacity', 0.85)
    sel.exit().remove()
    ;(sim.force('link') as d3.ForceLink<SimNode, SimLink>).links(links)
    sim.alpha(0.3).restart()
  }, [conflicts, laneIds])

  // ── Pulse on new message ─────────────────────────────────────────────────────
  useEffect(() => {
    const g = gRef.current
    if (!g || streamMessages.length === 0) return
    const dept = streamMessages[streamMessages.length - 1]?.department
    if (!dept) return
    g.select('g.nodes')
      .selectAll<SVGGElement, SimNode>('g.node')
      .filter((d) => d.id === dept)
      .select('.ring')
      .attr('r', 22)
      .attr('opacity', 0.75)
      .transition()
      .duration(900)
      .ease(d3.easeCubicOut)
      .attr('r', 42)
      .attr('opacity', 0)
  }, [streamMessages])

  const conflictTypeLabel = (type: string) => intl.simulate?.conflictTypes?.[type] ?? type
  const sevLabel = (s: string) =>
    s === 'low' ? ts('sevLow') : s === 'medium' ? ts('sevMedium') : s === 'high' ? ts('sevHigh') : s

  const metaEntry =
    selected && intl.graph?.meta ? intl.graph.meta[laneMetaKey(selected)] : null
  const meta = metaEntry
    ? { role: metaEntry.role, agent: metaEntry.agent, bias: metaEntry.bias }
    : null
  const deptConflicts = selected
    ? conflicts.filter((c) => c.dept_a === selected || c.dept_b === selected)
    : []
  const recentMsg = selected
    ? [...streamMessages].reverse().find((m) => m.department === selected)
    : null

  if (laneIds.length === 0) {
    return (
      <div className="relative flex h-full w-full items-center justify-center px-6 text-center">
        <p className="max-w-xs text-xs leading-relaxed text-gray-400">{t('empty')}</p>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className="h-full w-full"
        aria-label={t('ariaNetwork')}
      />

      {selected && meta && (
        <div
          id="node-info-card"
          className="absolute bottom-3 left-3 right-3 z-10 space-y-2 rounded-lg border border-gray-200 bg-white p-3 shadow-lg sm:left-auto sm:right-3 sm:w-72"
          style={{ borderLeftColor: colorForLane(selected), borderLeftWidth: 3 }}
        >
          <div className="flex items-center justify-between gap-2">
            <div className="flex min-w-0 items-center gap-2">
              <span
                className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
                style={{ backgroundColor: colorForLane(selected) }}
              >
                {initialLetter(selected)}
              </span>
              <div className="min-w-0">
                <p className="text-xs font-bold leading-tight text-gray-900">{truncateLabel(selected, 28)}</p>
                <p className="text-[10px] leading-tight text-gray-400">
                  {meta.role} · {meta.agent}
                </p>
              </div>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="flex-shrink-0 text-sm leading-none text-gray-300 transition-colors hover:text-gray-500"
              aria-label={t('close')}
            >
              ✕
            </button>
          </div>

          <p className="text-[11px] leading-snug text-gray-600">{meta.bias}</p>

          {deptConflicts.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
                {t('risksHeading', { count: deptConflicts.length })}
              </p>
              {deptConflicts.slice(0, 3).map((c) => (
                <div key={c.conflict_id} className="flex items-center gap-1.5 text-[10px]">
                  <span
                    className="inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full"
                    style={{ backgroundColor: SEVERITY_COLOR[c.severity] }}
                  />
                  <span className="truncate text-gray-600">
                    {t('vs')} {c.dept_a === selected ? c.dept_b : c.dept_a}
                    {' · '}
                    {conflictTypeLabel(c.conflict_type)}
                  </span>
                  <span className="ml-auto flex-shrink-0 font-medium" style={{ color: SEVERITY_COLOR[c.severity] }}>
                    {sevLabel(c.severity)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {recentMsg && (
            <div className="space-y-0.5">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">{t('lastMessage')}</p>
              <p className="line-clamp-3 text-[11px] leading-snug text-gray-600">{recentMsg.content}</p>
            </div>
          )}

          {deptConflicts.length === 0 && !recentMsg && (
            <p className="text-[10px] italic text-gray-400">{t('noActivity')}</p>
          )}
        </div>
      )}
    </div>
  )
}
