'use client'

import { use, useEffect, useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { getSimulation, type SimulationCreateResponse } from '@/lib/api'
import type { ConflictDict, MessageDict } from '@/lib/types'

const REPORT_PALETTE = ['#185FA5', '#854F0B', '#0F6E56', '#534AB7', '#0369a1', '#7c3aed']

function badgeColor(label: string): string {
  let h = 0
  for (let i = 0; i < label.length; i++) h = (h << 5) - h + label.charCodeAt(i)
  return REPORT_PALETTE[Math.abs(h) % REPORT_PALETTE.length]
}

const SEVERITY_BADGE: Record<string, string> = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-amber-100 text-amber-800',
  high: 'bg-red-100 text-red-800',
}

function Skeleton({ className }: { className: string }) {
  return <div className={`animate-pulse rounded bg-gray-200 ${className}`} />
}

/** Full-page skeleton: shown before the first API response arrives */
function InitialSkeleton() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="h-4 w-1/3" />
      <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-3">
        <Skeleton className="h-5 w-32" />
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-4 w-full" />)}
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-3">
        <Skeleton className="h-5 w-48" />
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-4 w-full" />)}
      </div>
    </div>
  )
}

/** Inline spinner + label: shown when run is fetched but report not yet ready */
function GeneratingBanner() {
  const t = useTranslations('report')
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 flex items-center gap-3">
      <svg
        className="animate-spin h-5 w-5 text-gray-400 flex-shrink-0"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
        />
      </svg>
      <span className="text-sm text-gray-500">{t('generating')}</span>
    </div>
  )
}

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const locale = useLocale()
  const t = useTranslations('report')
  const ts = useTranslations('simulate')
  const [run, setRun] = useState<SimulationCreateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [logOpen, setLogOpen] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function poll() {
      try {
        const data = await getSimulation(id)
        if (cancelled) return
        setRun(data)
        if (data.status !== 'complete' && data.status !== 'failed' && data.status !== 'error') {
          setTimeout(poll, 2000)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('loadError'))
      }
    }
    poll()
    return () => { cancelled = true }
  }, [id, t])

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <div className="rounded-md bg-red-50 border border-red-200 p-4 text-red-700 text-sm break-words">
          {error}
        </div>
      </div>
    )
  }

  // First load — no data yet
  if (!run) return <InitialSkeleton />

  const report = run.report ?? null
  const isGenerating =
    run.status !== 'complete' && run.status !== 'failed' && run.status !== 'error'
  const createdAt = new Date(run.created_at).toLocaleString(locale)

  const transcriptMessages = run.messages ?? []
  const conflicts = (run.conflicts ?? []) as ConflictDict[]

  // Group messages by round
  const byRound = transcriptMessages.reduce<Record<number, MessageDict[]>>((acc, m) => {
    ;(acc[m.round] ??= []).push(m)
    return acc
  }, {})

  const sevLabel = (s: string) =>
    s === 'low' ? ts('sevLow') : s === 'medium' ? ts('sevMedium') : s === 'high' ? ts('sevHigh') : s

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold break-words">{run.decision}</h1>
        <p className="text-sm text-gray-400 mt-1">{t('runMeta', { id: run.run_id, date: createdAt })}</p>
      </div>

      {/* Executive summary */}
      <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-2">
        <h2 className="text-lg font-semibold">{t('executiveSummary')}</h2>
        <p className="text-xs text-gray-500">{t('execDisclaimer')}</p>
        {isGenerating || !report ? (
          <div className="space-y-2">
            {!isGenerating && run.recommendation && !report ? (
              <p className="text-sm text-gray-700 leading-relaxed">{run.recommendation}</p>
            ) : (
              <>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
              </>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-700 leading-relaxed">{report.executive_summary}</p>
        )}
      </section>

      {/* Confidence score */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex-shrink-0">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{t('confidenceScore')}</p>
          {isGenerating || !report ? (
            <Skeleton className="h-10 w-20" />
          ) : (
            <p className="text-4xl font-bold text-gray-900">
              {Math.round(report.confidence_score * 100)}%
            </p>
          )}
        </div>
        <div className="w-full h-2 rounded-full bg-gray-100 overflow-hidden">
          {!isGenerating && report && (
            <div
              className="h-2 rounded-full bg-gray-900 transition-all"
              style={{ width: `${Math.round(report.confidence_score * 100)}%` }}
            />
          )}
        </div>
      </div>

      {/* Generating banner — shown while report isn't ready yet */}
      {isGenerating && <GeneratingBanner />}

      {/* Key Risks */}
      <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
        <h2 className="text-lg font-semibold">{t('keyRisks')}</h2>
        {isGenerating || !report || report.key_risks.length === 0 ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-4 w-full" />)}
          </div>
        ) : (
          <ol className="space-y-2">
            {report.key_risks.map((risk, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="flex-shrink-0 font-semibold text-gray-400">{i + 1}.</span>
                <span className="text-gray-700 break-words">{risk}</span>
              </li>
            ))}
          </ol>
        )}
      </section>

      {/* Recommended Actions */}
      <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
        <h2 className="text-lg font-semibold">{t('recommendedActions')}</h2>
        {isGenerating || !report || report.recommended_actions.length === 0 ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-4 w-full" />)}
          </div>
        ) : (
          <ol className="space-y-2">
            {report.recommended_actions.map((action, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="flex-shrink-0 font-semibold text-gray-400">{i + 1}.</span>
                <span className="text-gray-700 break-words">{action}</span>
              </li>
            ))}
          </ol>
        )}
      </section>

      {!isGenerating && report && report.caveat && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {report.caveat}
        </div>
      )}

      {!isGenerating && report && report.known_facts && report.known_facts.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
          <h2 className="text-lg font-semibold">{t('groundedFacts')}</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-700">
            {report.known_facts.map((f, i) => (
              <li key={i} className="break-words">{f}</li>
            ))}
          </ul>
        </section>
      )}

      {!isGenerating && report && report.unknown_facts && report.unknown_facts.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
          <h2 className="text-lg font-semibold">{t('openUncertainties')}</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-700">
            {report.unknown_facts.map((f, i) => (
              <li key={i} className="break-words">{f}</li>
            ))}
          </ul>
        </section>
      )}

      {!isGenerating && report && report.must_verify_facts && report.must_verify_facts.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
          <h2 className="text-lg font-semibold">{t('mustVerify')}</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-700">
            {report.must_verify_facts.map((f, i) => (
              <li key={i} className="break-words">{f}</li>
            ))}
          </ul>
        </section>
      )}

      {!isGenerating && report && report.professional_questions && report.professional_questions.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
          <h2 className="text-lg font-semibold">{t('questionsPro')}</h2>
          <ol className="list-decimal space-y-2 pl-5 text-sm text-gray-700">
            {report.professional_questions.map((q, i) => (
              <li key={i} className="break-words">{q}</li>
            ))}
          </ol>
        </section>
      )}

      {!isGenerating && report && report.source_links && report.source_links.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
          <h2 className="text-lg font-semibold">{t('sources')}</h2>
          <ul className="space-y-2 text-sm">
            {report.source_links.map((link, i) => (
              <li key={i}>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-700 underline hover:text-blue-900 break-all"
                >
                  {link.title}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Risk timeline */}
      {conflicts.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-4 sm:p-6 space-y-3">
          <h2 className="text-lg font-semibold">{t('riskTimeline')}</h2>
          <p className="text-xs text-gray-500">{t('riskTimelineHint')}</p>
          <div className="space-y-4">
            {conflicts
              .slice()
              .sort((a, b) => a.round_detected - b.round_detected)
              .map((c) => (
                <div key={c.conflict_id} className="flex gap-3 items-start text-sm">
                  <span className="flex-shrink-0 text-xs text-gray-400 w-14 sm:w-16 pt-0.5">
                    {t('round', { n: c.round_detected })}
                  </span>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">
                        {c.dept_a} ↔ {c.dept_b}
                      </span>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${SEVERITY_BADGE[c.severity]}`}
                      >
                        {sevLabel(c.severity)}
                      </span>
                      {c.risk_category && (
                        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-gray-600">
                          {String(c.risk_category).replace(/_/g, ' ')}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 text-xs break-words">{c.description}</p>
                    {c.risk_summary && (
                      <p className="text-[11px] leading-snug text-gray-500 break-words">{c.risk_summary}</p>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </section>
      )}

      {/* Full Agent Log — collapsible */}
      {transcriptMessages.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white overflow-hidden">
          <button
            className="w-full flex items-center justify-between px-4 sm:px-6 py-4 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
            onClick={() => setLogOpen((o) => !o)}
          >
            <span>{t('advisorTranscript', { count: transcriptMessages.length })}</span>
            <span className="ml-2">{logOpen ? '▲' : '▼'}</span>
          </button>
          {logOpen && (
            <div className="border-t border-gray-100 px-4 sm:px-6 py-4 space-y-6 max-h-96 overflow-y-auto">
              {Object.entries(byRound)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([round, msgs]) => (
                  <div key={round}>
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                      {t('roundHeading', { n: Number(round) })}
                    </p>
                    <div className="space-y-2">
                      {msgs.map((m) => (
                        <div key={m.message_id} className="flex gap-2 text-sm min-w-0">
                          <span
                            className="flex-shrink-0 text-xs font-semibold px-1.5 py-0.5 rounded text-white h-fit"
                            style={{ backgroundColor: badgeColor(m.department) }}
                          >
                            {m.department}
                          </span>
                          <span className="text-gray-700 break-words min-w-0">{m.content}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
