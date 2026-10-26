'use client'

import { useEffect, useMemo, useRef } from 'react'
import { useTranslations } from 'next-intl'
import * as d3 from 'd3'
import type { SimulationEvent } from '@/lib/types'

const W = 900
const H = 520

/** Exact legacy keys + CivicBridge advisor lane labels; unknown dept uses keyword or hash fallback. */
const DEPT_COLORS: Record<string, string> = {
  Sales: '#185FA5',
  Finance: '#854F0B',
  Operations: '#0F6E56',
  HR: '#534AB7',
  Engineering: '#0ea5e9',
  Marketing: '#db2777',
  'Founder Immigration — Evidence': '#7c3aed',
  'Founder Immigration — Counsel': '#1d4ed8',
  'Tax & payroll posture': '#854F0B',
  'Founder readiness': '#0d9488',
}

function _hashHue(dept: string): string {
  let h = 0
  for (let i = 0; i < dept.length; i += 1) {
    h = (h * 31 + dept.charCodeAt(i)) % 360
  }
  return `hsl(${h}, 55%, 42%)`
}

function fillForDept(dept: string): string {
  if (DEPT_COLORS[dept]) return DEPT_COLORS[dept]
  const lower = dept.toLowerCase()
  if (lower.includes('immigration') || lower.includes('counsel') || lower.includes('attorney'))
    return '#1d4ed8'
  if (lower.includes('evidence') || lower.includes('coach')) return '#7c3aed'
  if (lower.includes('tax') || lower.includes('payroll')) return '#854F0B'
  if (lower.includes('health')) return '#0f766e'
  if (lower.includes('housing') || lower.includes('lease')) return '#c2410c'
  if (lower.includes('bank') || lower.includes('credit')) return '#0369a1'
  if (lower.includes('founder') || lower.includes('mentor')) return '#0d9488'
  if (lower.includes('banking')) return '#0369a1'
  if (lower.includes('local') || lower.includes('systems')) return '#4f46e5'
  return _hashHue(dept)
}

interface SwarmNode extends d3.SimulationNodeDatum {
  id: string
  dept: string
  label: string
  msgs: number
}

interface SwarmLink extends d3.SimulationLinkDatum<SwarmNode> {
  key: string
  weight: number
}

interface Props {
  events: SimulationEvent[]
}

function initials(label: string): string {
  return label
    .split(/[\s_]/)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function stableOffset(seed: string, axis: 'x' | 'y'): number {
  let hash = axis === 'x' ? 17 : 31
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 33 + seed.charCodeAt(i)) % 997
  }
  return (hash / 997 - 0.5) * 120
}

export function SwarmInteractionGraph({ events }: Props) {
  const t = useTranslations('graph')
  const svgRef = useRef<SVGSVGElement>(null)

  const { nodes, links } = useMemo(() => {
    const nodeMap = new Map<string, SwarmNode>()
    const edgeMap = new Map<string, SwarmLink>()
    const prevByRound = new Map<number, string>()

    for (const ev of events) {
      if (ev.type !== 'agent_message' || !ev.agent) continue
      const role = ev.agent.role || ev.agent.name || 'Agent'
      const dept = ev.agent.dept || 'Unknown'
      const round = typeof ev.round === 'number' ? ev.round : 1
      const nodeId = ev.agent.name || role

      const existing = nodeMap.get(nodeId)
      if (existing) {
        existing.msgs += 1
      } else {
        nodeMap.set(nodeId, {
          id: nodeId,
          label: role,
          dept,
          msgs: 1,
          x: W / 2 + stableOffset(nodeId, 'x'),
          y: H / 2 + stableOffset(nodeId, 'y'),
        })
      }

      const prev = prevByRound.get(round)
      if (prev && prev !== nodeId) {
        const key = `${prev}->${nodeId}`
        const ex = edgeMap.get(key)
        if (ex) {
          ex.weight += 1
        } else {
          edgeMap.set(key, {
            key,
            source: prev,
            target: nodeId,
            weight: 1,
          })
        }
      }
      prevByRound.set(round, nodeId)
    }

    return {
      nodes: Array.from(nodeMap.values()),
      links: Array.from(edgeMap.values()),
    }
  }, [events])

  useEffect(() => {
    const svgEl = svgRef.current
    if (!svgEl) return
    const svg = d3.select(svgEl)
    svg.selectAll('*').remove()

    if (nodes.length === 0) return

    const g = svg.append('g')

    g.append('defs')
      .append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 16)
      .attr('refY', 0)
      .attr('markerWidth', 5)
      .attr('markerHeight', 5)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#9ca3af')

    const link = g
      .append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#9ca3af')
      .attr('stroke-opacity', 0.45)
      .attr('stroke-width', (d) => Math.min(7, 1 + d.weight * 0.8))
      .attr('marker-end', 'url(#arrow)')

    const node = g
      .append('g')
      .selectAll<SVGGElement, SwarmNode>('g')
      .data(nodes, (d) => d.id)
      .enter()
      .append('g')

    node
      .append('circle')
      .attr('r', (d) => Math.min(18, 8 + d.msgs * 1.2))
      .attr('fill', (d) => fillForDept(d.dept))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', '#fff')
      .attr('font-size', 10)
      .attr('font-weight', 700)
      .text((d) => initials(d.label))

    node
      .append('title')
      .text((d) => `${d.label} (${d.dept}) · ${d.msgs} messages`)

    const sim = d3
      .forceSimulation<SwarmNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<SwarmNode, SwarmLink>(links)
          .id((d) => d.id)
          .distance(70)
          .strength(0.35),
      )
      .force('charge', d3.forceManyBody().strength(-150))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide<SwarmNode>().radius((d) => Math.min(20, 10 + d.msgs * 1.4)))
      .on('tick', () => {
        link
          .attr('x1', (d) => (d.source as SwarmNode).x ?? 0)
          .attr('y1', (d) => (d.source as SwarmNode).y ?? 0)
          .attr('x2', (d) => (d.target as SwarmNode).x ?? 0)
          .attr('y2', (d) => (d.target as SwarmNode).y ?? 0)
        node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
      })

    const drag = d3
      .drag<SVGGElement, SwarmNode>()
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

    node.call(drag)
    return () => {
      sim.stop()
    }
  }, [nodes, links])

  if (nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-xs text-gray-400">
        {t('swarmEmpty')}
      </div>
    )
  }

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${W} ${H}`}
      className="w-full h-full"
      aria-label={t('swarmAria')}
    />
  )
}
