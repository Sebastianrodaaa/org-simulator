'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/simulate', label: 'Rehearse' },
  { href: '/dashboard', label: 'Overview' },
]

export function Nav() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-gray-200 bg-white px-6 py-3 flex items-center justify-between">
      <Link href="/simulate" className="font-semibold text-gray-900 tracking-tight text-lg">
        CivicBridge
      </Link>
      <div className="flex gap-6">
        {links.map(({ href, label }) => {
          const active = pathname.startsWith(href)
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
              {label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
