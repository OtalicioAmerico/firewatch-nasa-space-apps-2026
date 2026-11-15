/** Locale-aware formatting through Intl. Dates are scientific UTC days: every formatter pins timeZone to UTC. */
import type { Lang } from './index'

export interface Formatters {
  lang: Lang
  num: (v: number | null, digits?: number) => string
  pct: (v: number | null, digits?: number) => string
  dec: (v: number | null, digits?: number) => string
  date: (iso: string) => string
  dateLong: (iso: string) => string
  monthLong: (m: number) => string
  monthShort: (m: number) => string
  monthYear: (year: number, m: number) => string
  weekdayShort: (index0Monday: number) => string
}

const DASH = '—'
const cache = new Map<Lang, Formatters>()

export function makeFormatters(lang: Lang): Formatters {
  const hit = cache.get(lang)
  if (hit) return hit
  const nf = (d: number) => new Intl.NumberFormat(lang, { minimumFractionDigits: d, maximumFractionDigits: d })
  const pf = (d: number) => new Intl.NumberFormat(lang, { style: 'percent', minimumFractionDigits: d, maximumFractionDigits: d })
  const nfCache = new Map<number, Intl.NumberFormat>()
  const pfCache = new Map<number, Intl.NumberFormat>()
  const getN = (d: number) => nfCache.get(d) ?? (nfCache.set(d, nf(d)), nfCache.get(d)!)
  const getP = (d: number) => pfCache.get(d) ?? (pfCache.set(d, pf(d)), pfCache.get(d)!)
  const utc = (iso: string) => new Date(`${iso}T00:00:00Z`)
  const dayFmt =
    lang === 'pt-BR'
      ? new Intl.DateTimeFormat(lang, { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' })
      : new Intl.DateTimeFormat(lang, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
  const dayOnly =
    lang === 'pt-BR'
      ? new Intl.DateTimeFormat(lang, { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' })
      : new Intl.DateTimeFormat(lang, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
  const monthLong = new Intl.DateTimeFormat(lang, { month: 'long', timeZone: 'UTC' })
  const monthShort = new Intl.DateTimeFormat(lang, { month: 'short', timeZone: 'UTC' })
  const weekday = new Intl.DateTimeFormat(lang, { weekday: 'short', timeZone: 'UTC' })
  const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)
  const f: Formatters = {
    lang,
    num: (v, d = 0) => (v === null ? DASH : getN(d).format(v)),
    dec: (v, d = 1) => (v === null ? DASH : getN(d).format(v)),
    pct: (v, d = 1) => (v === null ? DASH : getP(d).format(v)),
    date: (iso) => dayOnly.format(utc(iso)),
    dateLong: (iso) => dayFmt.format(utc(iso)),
    monthLong: (m) => cap(monthLong.format(new Date(Date.UTC(2024, m - 1, 1)))),
    monthShort: (m) => cap(monthShort.format(new Date(Date.UTC(2024, m - 1, 1))).replace('.', '')),
    monthYear: (y, m) => `${f.monthLong(m)} ${y}`,
    weekdayShort: (i) => cap(weekday.format(new Date(Date.UTC(2024, 0, 1 + i))).replace('.', '')),
  }
  cache.set(lang, f)
  return f
}
