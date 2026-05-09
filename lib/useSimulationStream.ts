'use client'

import { useState, useEffect, useRef } from 'react'
import type { SimulationEvent } from './types'

type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'complete' | 'error'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const BASE_WS = BASE.replace(/^http/, 'ws')

export function useSimulationStream(runId: string | null) {
  const [events, setEvents] = useState<SimulationEvent[]>([])
  const [status, setStatus] = useState<StreamStatus>('idle')
  // Track status in a ref so the onclose handler reads current value
  const statusRef = useRef<StreamStatus>('idle')

  useEffect(() => {
    if (!runId) return

    let ws: WebSocket | null = null
    const reset = setTimeout(() => {
      setEvents([])
      setStatus('connecting')
      statusRef.current = 'connecting'

      ws = new WebSocket(`${BASE_WS}/ws/simulation/${runId}`)

      ws.onopen = () => {
        setStatus('streaming')
        statusRef.current = 'streaming'
      }

      ws.onmessage = (e: MessageEvent<string>) => {
        try {
          const event = JSON.parse(e.data) as SimulationEvent
          setEvents((prev) => [...prev, event])
          if (event.type === 'complete') {
            setStatus('complete')
            statusRef.current = 'complete'
          }
        } catch {
          // ignore malformed frames
        }
      }

      ws.onerror = () => {
        setStatus('error')
        statusRef.current = 'error'
      }

      ws.onclose = () => {
        if (statusRef.current !== 'complete') {
          setStatus('error')
          statusRef.current = 'error'
        }
      }
    }, 0)

    return () => {
      clearTimeout(reset)
      ws?.close()
    }
  }, [runId])

  return { events, status }
}
