import type { FireCalendarDataSource } from './dataSource'
import { mockDataSource } from './mockDataSource'
import { createRealDataSource, fetchLoader } from './realDataSource'

interface Env {
  VITE_DATA_MODE?: string
  DEV?: boolean
  BASE_URL?: string
}
const env: Env = (import.meta as unknown as { env?: Env }).env ?? {}

/**
 * The ONLY place that chooses the data source. REAL (Mission 05 results) is the default.
 * MOCK (simulated fixtures) only when the build says so (VITE_DATA_MODE=mock) or, in development builds, with ?source=mock.
 * The two are never mixed.
 */
function wantsMock(): boolean {
  if (env.VITE_DATA_MODE === 'mock') return true
  if (env.DEV && typeof location !== 'undefined') return new URLSearchParams(location.search).get('source') === 'mock'
  return false
}

export const dataSource: FireCalendarDataSource = wantsMock() ? mockDataSource : createRealDataSource(fetchLoader(env.BASE_URL ?? '/'))
export type { FireCalendarDataSource }
export type { Need } from './dataSource'
