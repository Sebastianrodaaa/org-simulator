'use client'

import { useEffect, useMemo, useState } from 'react'
import { Link } from '@/i18n/navigation'
import { useTranslations, useMessages } from 'next-intl'
import { Globe } from '@/components/ui/cobe-globe'
import { getHealth } from '@/lib/api'
import { DeptFeedDrawer, type DomainFeedKey } from '@/components/DeptFeedDrawer'

type DomainStatus = 'healthy' | 'warning' | 'critical'

const DOMAIN_LAYOUT: {
  domainKey: DomainFeedKey
  color: string
  bgLight: string
  status: DomainStatus
}[] = [
  { domainKey: 'sales', color: '#185FA5', bgLight: 'bg-blue-50/80 border-blue-200', status: 'warning' },
  { domainKey: 'finance', color: '#854F0B', bgLight: 'bg-amber-50/80 border-amber-200', status: 'critical' },
  { domainKey: 'operations', color: '#0F6E56', bgLight: 'bg-emerald-50/80 border-emerald-200', status: 'healthy' },
  { domainKey: 'hr', color: '#534AB7', bgLight: 'bg-violet-50/80 border-violet-200', status: 'warning' },
]

const STATUS_BADGE: Record<DomainStatus, string> = {
  healthy: 'bg-teal-50 text-teal-900 border border-teal-100',
  warning: 'bg-amber-50 text-amber-900 border border-amber-100',
  critical: 'bg-red-50 text-red-900 border border-red-100',
}

const STATUS_I18N_KEY: Record<DomainStatus, 'onTrack' | 'needsAttention' | 'highTension'> = {
  healthy: 'onTrack',
  warning: 'needsAttention',
  critical: 'highTension',
}

const HUB_LAYOUT: {
  id: string
  location: [number, number]
  label: string
  active: boolean
  color: string
}[] = [
  { id: 'sf', location: [37.7595, -122.4367], label: 'San Francisco', active: true, color: '#0f766e' },
  { id: 'nyc', location: [40.7128, -74.006], label: 'New York', active: true, color: '#185FA5' },
  { id: 'austin', location: [30.2672, -97.7431], label: 'Austin', active: true, color: '#854F0B' },
  { id: 'toronto', location: [43.6532, -79.3832], label: 'Toronto', active: false, color: '#0f766e' },
  { id: 'london', location: [51.5074, -0.1278], label: 'London', active: true, color: '#534AB7' },
  { id: 'berlin', location: [52.52, 13.405], label: 'Berlin', active: false, color: '#185FA5' },
]

type DomainCopy = { title: string; metrics: { label: string; value: string }[] }
type HubCopy = { id: string; city: string; focus: string }

function DomainCardSkeleton() {
  return (
    <div className="rounded-lg border border-gray-200 p-4 space-y-3 bg-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="animate-pulse w-3 h-3 rounded-full bg-gray-200" />
          <div className="animate-pulse h-4 w-16 rounded bg-gray-200" />
        </div>
        <div className="animate-pulse h-4 w-14 rounded-full bg-gray-200" />
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-1">
            <div className="animate-pulse h-3 w-full rounded bg-gray-200" />
            <div className="animate-pulse h-4 w-2/3 rounded bg-gray-200" />
          </div>
        ))}
      </div>
      <div className="animate-pulse h-3 w-16 rounded bg-gray-200" />
    </div>
  )
}

export default function DashboardPage() {
  const t = useTranslations('dashboard')
  const messages = useMessages() as { dashboard?: { domains?: Record<string, DomainCopy>; hubs?: HubCopy[] } }

  const [loading, setLoading] = useState(true)
  const [selectedDomain, setSelectedDomain] = useState<{
    domainKey: DomainFeedKey
    title: string
    color: string
  } | null>(null)

  useEffect(() => {
    getHealth()
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const domainCopy = messages.dashboard?.domains ?? {}
  const hubRows = messages.dashboard?.hubs ?? []

  const hubs = useMemo(() => {
    const byId = new Map(hubRows.map((h) => [h.id, h]))
    return HUB_LAYOUT.map((h) => {
      const row = byId.get(h.id)
      return {
        ...h,
        city: row?.city ?? h.label,
        focus: row?.focus ?? '',
      }
    })
  }, [hubRows])

  const activeHubCount = HUB_LAYOUT.filter((h) => h.active).length

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
        <section>
          <h2 className="text-xl font-semibold text-gray-900">{t('planningTitle')}</h2>
          <p className="text-sm text-gray-500 mt-1 mb-4 max-w-xl">{t('planningIntro')}</p>
          <div className="space-y-4">
            {loading
              ? [1, 2, 3, 4].map((i) => <DomainCardSkeleton key={i} />)
              : DOMAIN_LAYOUT.map((domain) => {
                  const copy = domainCopy[domain.domainKey]
                  if (!copy) return null
                  return (
                    <div key={domain.domainKey} className={`rounded-lg border p-4 ${domain.bgLight}`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span
                            className="inline-block w-3 h-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: domain.color }}
                          />
                          <span className="font-semibold text-gray-900">{copy.title}</span>
                        </div>
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_BADGE[domain.status]}`}
                        >
                          {t(`badge.${STATUS_I18N_KEY[domain.status]}`)}
                        </span>
                      </div>
                      <dl className="grid grid-cols-3 gap-2 text-sm">
                        {copy.metrics.map((m) => (
                          <div key={`${m.label}-${m.value}`}>
                            <dt className="text-gray-500 text-xs leading-tight">{m.label}</dt>
                            <dd className="font-semibold text-gray-900">{m.value}</dd>
                          </div>
                        ))}
                      </dl>
                      <div className="mt-3">
                        <button
                          type="button"
                          className="text-xs text-gray-500 hover:text-gray-800 transition-colors"
                          onClick={() =>
                            setSelectedDomain({
                              domainKey: domain.domainKey,
                              title: copy.title,
                              color: domain.color,
                            })
                          }
                        >
                          {t('sampleFeed')}
                        </button>
                      </div>
                    </div>
                  )
                })}
          </div>
        </section>

        <section>
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{t('hubsTitle')}</h2>
              <p className="text-sm text-gray-500 mt-1 max-w-md">{t('hubsIntro')}</p>
            </div>
            <span className="text-xs text-gray-500 sm:text-right sm:pt-1 whitespace-nowrap">
              {t('hubsCount', { active: activeHubCount, total: hubs.length })}
            </span>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
            <div className="flex flex-col md:flex-row">
              <div className="flex-1 flex items-center justify-center p-4 bg-gray-50 min-h-[280px]">
                {loading ? (
                  <div className="animate-pulse w-48 h-48 rounded-full bg-gray-200" />
                ) : (
                  <Globe
                    markers={hubs.map((h) => ({ id: h.id, location: h.location, label: h.city }))}
                    className="w-48 h-48 sm:w-56 sm:h-56"
                    markerColor={[0.059, 0.463, 0.431]}
                    baseColor={[0.97, 0.97, 0.98]}
                    glowColor={[0.88, 0.94, 0.93]}
                    mapBrightness={8}
                    dark={0}
                    speed={0.004}
                  />
                )}
              </div>

              <div className="md:w-56 border-t md:border-t-0 md:border-l border-gray-100 flex flex-col justify-center divide-y divide-gray-50">
                {hubs.map((hub) => (
                  <div key={hub.id} className="flex items-center gap-3 px-4 py-2.5">
                    <span className="relative flex-shrink-0 flex h-2.5 w-2.5">
                      {hub.active && (
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-60" />
                      )}
                      <span
                        className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
                          hub.active ? 'bg-teal-600' : 'bg-gray-300'
                        }`}
                      />
                    </span>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-medium text-gray-900 truncate">{hub.city}</span>
                        <span
                          className="flex-shrink-0 inline-block w-2 h-2 rounded-full"
                          style={{ backgroundColor: hub.color }}
                        />
                      </div>
                      <p className="text-xs text-gray-400 truncate">{hub.focus}</p>
                    </div>

                    <span
                      className={`flex-shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                        hub.active ? 'bg-teal-50 text-teal-800' : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      {hub.active ? t('highlighted') : t('quiet')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>

      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-1">{t('rehearsalsTitle')}</h2>
        <p className="text-sm text-gray-500 mb-4">{t('rehearsalsHint')}</p>
        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-3">
            <div className="animate-pulse h-4 w-1/2 rounded bg-gray-200" />
            <div className="animate-pulse h-4 w-2/3 rounded bg-gray-200" />
            <div className="animate-pulse h-4 w-1/3 rounded bg-gray-200" />
          </div>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-gray-400 text-sm mb-4">
            {t('noRehearsal')}
          </div>
        )}
        <div className="mt-4">
          <Link
            href="/simulate"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            {t('startRehearsal')}
          </Link>
        </div>
      </section>

      {selectedDomain && (
        <DeptFeedDrawer
          domainKey={selectedDomain.domainKey}
          title={selectedDomain.title}
          color={selectedDomain.color}
          onClose={() => setSelectedDomain(null)}
        />
      )}
    </div>
  )
}
