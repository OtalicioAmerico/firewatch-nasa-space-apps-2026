import type { CoverageState } from '../types'

/** Static, language-independent helpers. Texts and number/date formatting live in ../i18n. */
export const COVERAGE_TONE: Record<CoverageState, 'green' | 'amber' | 'magenta' | 'neutral'> = {
  CORROBORATED: 'green',
  PARTIAL: 'amber',
  INDETERMINATE: 'magenta',
  NO_COVERAGE_CORROBORATED: 'neutral',
}

/** Adds days to an ISO UTC day (calendar arithmetic in UTC: never shifted by the browser time zone). */
export function addDays(iso: string, n: number): string {
  return new Date(new Date(iso + 'T00:00:00Z').getTime() + n * 86400000).toISOString().slice(0, 10)
}

/** Same month/day if it exists, otherwise the last day of the month. */
export function clampDate(y: number, m: number, d: number): string {
  const last = new Date(Date.UTC(y, m, 0)).getUTCDate()
  return `${y}-${String(m).padStart(2, '0')}-${String(Math.min(d, last)).padStart(2, '0')}`
}
