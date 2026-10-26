'use client'

import { Link, usePathname } from '@/i18n/navigation'
import { useTranslations } from 'next-intl'

const links = [
  { href: '/simulate', key: 'rehearse' as const },
  { href: '/dashboard', key: 'overview' as const },
]

export function Nav() {
  const pathname = usePathname()
  const t = useTranslations('nav')

  return (
    <nav className="border-b border-gray-200 bg-white px-6 py-3 flex flex-wrap items-center justify-between gap-3">
      <Link href="/simulate" className="font-semibold text-gray-900 tracking-tight text-lg">
        {t('brand')}
      </Link>
      <div className="flex flex-wrap items-center gap-4 sm:gap-6">
        <div className="flex gap-6">
          {links.map(({ href, key }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`)
            return (
              <Link
                key={href}
                href={href}
                className={`text-sm font-medium pb-0.5 transition-colors ${
                  active
                    ? 'text-gray-900 border-b-2 border-gray-900'
                    : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                {t(key)}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
