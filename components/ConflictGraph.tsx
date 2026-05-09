'use client'

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { ConflictDict, MessageDict } from '@/lib/types'

const W = 400
const H = 460

const DEPT_COLORS: Record<string, string> = {
  Sales: '#185FA5',
  Finance: '#854F0B',
  Operations: '#0F6E56',
  HR: '#534AB7',
}

const DEPT_META: Record<string, { role: string; bias: string; agent: string }> = {
  Sales: {
    role: 'Evidence Coach',
    agent: 'Pipeline guardian',
    bias: 'Defends marketing spend as pipeline fuel. Flags Q4 revenue risk on any budget cut.',
  },
  Finance: {
    role: 'Immigration Attorney',
    agent: 'Cost-control anchor',
    bias: 'Prioritises runway preservation. Approves cuts that reduce burn; resists discretionary spend.',
  },
  Operations: {
    role: 'Founder Mentor',
    agent: 'Capacity watchdog',
    bias: 'Engineering at 94% — any scope creep triggers overcommitment alert.',
  },
  HR: {
    role: 'Tax Navigator',
    agent: 'Retention monitor',
    bias: 'Tracks morale signal. Budget cuts threatening OTE raise flight-risk score.',
  },
}

const DEPARTMENTS = ['Sales', 'Finance', 'Operations', 'HR'] as const

const TARGET: Record<string, { x: number; y: number }> = {
  Sales:      { x: W / 2,      y: 72 },
  Finance:    { x: W - 68,     y: H / 2 },
  Operations: { x: W / 2,      y: H - 72 },
  HR:         { x: 68,         y: H / 2 },
}

const SEVERITY_COLOR: Record<string, string> = {
  low: '#fbbf24', medium: '#f97316', high: '#ef4444',
}
const SEVERITY_WIDTH: Record<string, number> = {
  low: 2, medium: 3.5, high: 5,
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string; color: string; tx: number; ty: number
}
interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  key: string; severity: string; conflict_type: string
}
interface Props {
  conflicts: ConflictDict[]
  messages?: MessageDict[]
}

export function ConflictGraph({ conflicts, messages = [] }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null)
  const gRef   = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  // ── Init once ───────────────────────────────────────────────────────────────
  useEffect(() => {
    const svgEl = svgRef.current
    if (!svgEl) return

    const svg = d3.select(svgEl)
    svg.selectAll('*').remove()

    const nodes: SimNode[] = DEPARTMENTS.map((id) => ({
      id, color: DEPT_COLORS[id],
      tx: TARGET[id].x, ty: TARGET[id].y,
      x: TARGET[id].x + (Math.random() - 0.5) * 40,
      y: TARGET[id].y + (Math.random() - 0.5) * 40,
    }))

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

    const drag = d3.drag<SVGGElement, SimNode>()
      .on('start', (event, d) => { if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
      .on('drag',  (event, d) => { d.fx = event.x; d.fy = event.y })
      .on('end',   (event, d) => { if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null })

    const nodeG = g.select('g.nodes')
      .selectAll<SVGGElement, SimNode>('g.node')
      .data(nodes, (d) => d.id)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('cursor', 'pointer')
      .attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
      .call(drag)
      .on('click', (_event, d) => {
        // Bubble the dept id up to React state via a custom event on the SVG element
        svgEl.dispatchEvent(new CustomEvent('node-click', { detail: d.id, bubbles: true }))
      })

    nodeG.append('circle').attr('class', 'ring').attr('r', 24)
      .attr('fill', 'none').attr('stroke', (d) => d.color)
      .attr('stroke-width', 2.5).attr('opacity', 0)

    nodeG.append('circle').attr('r', 22)
      .attr('fill', (d) => d.color).attr('stroke', '#ffffff').attr('stroke-width', 2.5)

    nodeG.append('text').attr('text-anchor', 'middle').attr('dominant-baseline', 'central')
      .attr('fill', '#ffffff').attr('font-size', 13).attr('font-weight', 700)
      .attr('pointer-events', 'none').text((d) => d.id[0])

    nodeG.append('text').attr('text-anchor', 'middle').attr('y', 36)
      .attr('fill', '#4b5563').attr('font-size', 11).attr('font-weight', 600)
      .attr('pointer-events', 'none').text((d) => d.id)

    return () => { sim.stop() }
  }, [])

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
    const sim = simRef.current; const g = gRef.current
    if (!sim || !g) return
    const known = new Set(DEPARTMENTS as readonly string[])
    const edgeMap = new Map<string, SimLink>()
    const rank: Record<string, number> = { low: 0, medium: 1, high: 2 }
    for (const c of conflicts) {
      if (!known.has(c.dept_a) || !known.has(c.dept_b) || c.dept_a === c.dept_b) continue
      const key = [c.dept_a, c.dept_b].sort().join('|')
      const ex = edgeMap.get(key)
      if (!ex || rank[c.severity] > rank[ex.severity])
        edgeMap.set(key, { key, source: c.dept_a, target: c.dept_b, severity: c.severity, conflict_type: c.conflict_type })
    }
    const links = Array.from(edgeMap.values())
    const sel = g.select<SVGGElement>('g.links').selectAll<SVGLineElement, SimLink>('line').data(links, (d) => d.key)
    sel.enter().append('line')
      .attr('stroke', (d) => SEVERITY_COLOR[d.severity] ?? '#ef4444')
      .attr('stroke-width', (d) => SEVERITY_WIDTH[d.severity] ?? 3)
      .attr('stroke-linecap', 'round').attr('stroke-opacity', 0)
      .transition().duration(700).attr('stroke-opacity', 0.85)
    sel.exit().remove()
    ;(sim.force('link') as d3.ForceLink<SimNode, SimLink>).links(links)
    sim.alpha(0.3).restart()
  }, [conflicts])

  // ── Pulse on new message ─────────────────────────────────────────────────────
  useEffect(() => {
    const g = gRef.current
    if (!g || messages.length === 0) return
    const dept = messages[messages.length - 1]?.department
    if (!dept) return
    g.select('g.nodes').selectAll<SVGGElement, SimNode>('g.node')
      .filter((d) => d.id === dept).select('.ring')
      .attr('r', 22).attr('opacity', 0.75)
      .transition().duration(900).ease(d3.easeCubicOut)
      .attr('r', 42).attr('opacity', 0)
  }, [messages])

  // ── Derive card content ──────────────────────────────────────────────────────
  const meta = selected ? DEPT_META[selected] : null
  const deptConflicts = selected
    ? conflicts.filter((c) => c.dept_a === selected || c.dept_b === selected)
    : []
  const recentMsg = selected
    ? [...messages].reverse().find((m) => m.department === selected)
    : null

  return (
    <div className="relative w-full h-full">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-full"
        aria-label="Org decision cascade network"
      />

      {/* Node info card */}
      {selected && meta && (
        <div
          id="node-info-card"
          className="absolute bottom-3 left-3 right-3 sm:left-auto sm:right-3 sm:w-64 bg-white border border-gray-200 rounded-lg shadow-lg p-3 space-y-2 z-10"
          style={{ borderLeftColor: DEPT_COLORS[selected], borderLeftWidth: 3 }}
        >
          {/* Header */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-bold"
                style={{ backgroundColor: DEPT_COLORS[selected] }}
              >
                {selected[0]}
              </span>
              <div className="min-w-0">
                <p className="text-xs font-bold text-gray-900 leading-tight">{selected}</p>
                <p className="text-[10px] text-gray-400 leading-tight">{meta.role} · {meta.agent}</p>
              </div>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="flex-shrink-0 text-gray-300 hover:text-gray-500 transition-colors text-sm leading-none"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          {/* Behavioral bias */}
          <p className="text-[11px] text-gray-600 leading-snug">{meta.bias}</p>

          {/* Conflicts involving this dept */}
          {deptConflicts.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
                Conflicts ({deptConflicts.length})
              </p>
              {deptConflicts.slice(0, 3).map((c) => (
                <div key={c.conflict_id} className="flex items-center gap-1.5 text-[10px]">
                  <span
                    className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: SEVERITY_COLOR[c.severity] }}
                  />
                  <span className="text-gray-600 truncate">
                    vs {c.dept_a === selected ? c.dept_b : c.dept_a}
                    {' · '}{c.conflict_type}
                  </span>
                  <span className="ml-auto flex-shrink-0 font-medium" style={{ color: SEVERITY_COLOR[c.severity] }}>
                    {c.severity}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Most recent agent message */}
          {recentMsg && (
            <div className="space-y-0.5">
              <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">Last message</p>
              <p className="text-[11px] text-gray-600 leading-snug line-clamp-3">{recentMsg.content}</p>
            </div>
          )}

          {/* Empty state when no simulation has run */}
          {deptConflicts.length === 0 && !recentMsg && (
            <p className="text-[10px] text-gray-400 italic">No simulation data yet — run a scenario to see activity.</p>
          )}
        </div>
      )}
    </div>
  )
}
