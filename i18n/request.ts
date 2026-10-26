import { getRequestConfig } from 'next-intl/server'
import { hasLocale } from 'next-intl'
import { routing } from './routing'
import enUi from '../messages/en.json'
import { planInitialTasksEn } from '../lib/planInitialTasksEn'
import type { AbstractIntlMessages } from 'next-intl'

function mergeMessages(
  base: AbstractIntlMessages,
  override: AbstractIntlMessages,
): AbstractIntlMessages {
  const out: AbstractIntlMessages = { ...base }
  for (const k of Object.keys(override)) {
    const key = k as keyof AbstractIntlMessages
    const bv = base[key]
    const ov = override[key]
    if (ov === undefined) continue
    if (Array.isArray(ov)) {
      out[key] = ov
    } else if (
      ov !== null &&
      typeof ov === 'object' &&
      typeof bv === 'object' &&
      bv !== null &&
      !Array.isArray(bv)
    ) {
      out[key] = mergeMessages(bv as AbstractIntlMessages, ov as AbstractIntlMessages) as never
    } else {
      out[key] = ov as never
    }
  }
  return out
}

const enMessages = {
  ...enUi,
  planInitialTasks: planInitialTasksEn,
} as unknown as AbstractIntlMessages

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale
  const locale = hasLocale(routing.locales, requested) ? requested : routing.defaultLocale

  let messages: AbstractIntlMessages = enMessages
  if (locale !== 'en') {
    try {
      const loc = (await import(`../messages/${locale}.json`)).default as AbstractIntlMessages
      messages = mergeMessages(enMessages, loc)
    } catch {
      messages = enMessages
    }
  }

  return { locale, messages }
})
