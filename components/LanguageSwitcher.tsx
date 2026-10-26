'use client'

import { useTransition } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { usePathname, useRouter } from '@/i18n/navigation'
import { routing } from '@/i18n/routing'
import type { AppLocale } from '@/i18n/routing'

export function LanguageSwitcher() {
  const locale = useLocale() as AppLocale
  const router = useRouter()
  const pathname = usePathname()
  const t = useTranslations('languages')
  const tNav = useTranslations('nav')
  const [pending, startTransition] = useTransition()

  return (
    <label className="flex items-center gap-2 text-xs text-gray-500">
      <span className="whitespace-nowrap">{tNav('language')}:</span>
      <select
        aria-label={tNav('language')}
        className="rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-800 disabled:opacity-50"
        value={locale}
        disabled={pending}
        onChange={(e) => {
          const next = e.target.value as AppLocale
          startTransition(() => {
            router.replace(pathname, { locale: next })
          })
        }}
      >
        {routing.locales.map((loc) => (
          <option key={loc} value={loc}>
            {t(loc)}
          </option>
        ))}
      </select>
    </label>
  )
}
