import type { MetricId, Scenario, SensorFilter } from '../types'
import { DEFAULT_LANG, parseLang, type Lang } from '../i18n'

/** Both data sources cover exactly this range of scientific UTC days (checked by the tests). */
export const DATA_RANGE = { first: '2021-01-01', last: '2025-12-31' }

export type PageId = 'overview' | 'calendar' | 'spatial' | 'methodology'
export type Theme = 'ikarus-light' | 'ikarus-dark' // attribute values of the vendored design tokens (internal names)

export interface AppState {
  page: PageId
  date: string
  sensor: SensorFilter
  metric: MetricId
  scenario: Scenario
  theme: Theme
  selectedCellId: string | null
  showCells: boolean
  showPoints: boolean
  showMunicipalities: boolean
  navOpen: boolean
  lang: Lang
}

export const DEFAULT_DATE = '2024-07-19'


const PAGES: PageId[] = ['overview', 'calendar', 'spatial', 'methodology']
const SENSORS: SensorFilter[] = ['ALL', 'MODIS', 'VIIRS']
const METRICS: MetricId[] = ['extent', 'intensity', 'detections', 'concordance']

export function parseHash(hash: string, base: AppState): AppState {
  const raw = hash.replace(/^#\/?/, '')
  const [path, query = ''] = raw.split('?')
  const page = (PAGES as string[]).includes(path) ? (path as PageId) : base.page
  const q = new URLSearchParams(query)
  const range = DATA_RANGE
  const date = q.get('date')
  const sensor = q.get('sensor')
  const metric = q.get('metric')
  const scenario = q.get('scenario')
  return {
    ...base,
    page,
    date: date && /^\d{4}-\d{2}-\d{2}$/.test(date) && date >= range.first && date <= range.last ? date : base.date,
    sensor: sensor && (SENSORS as string[]).includes(sensor) ? (sensor as SensorFilter) : base.sensor,
    metric: metric && (METRICS as string[]).includes(metric) ? (metric as MetricId) : base.metric,
    scenario: scenario === 'A' || scenario === 'B' ? scenario : base.scenario,
    selectedCellId: q.get('cell') ?? (page === base.page ? base.selectedCellId : null),
    lang: parseLang(q.get('lang')) ?? base.lang,
  }
}

export function toHash(s: AppState): string {
  const q = new URLSearchParams({ date: s.date, sensor: s.sensor, metric: s.metric, scenario: s.scenario })
  if (s.selectedCellId) q.set('cell', s.selectedCellId)
  q.set('lang', s.lang)
  return `#/${s.page}?${q.toString()}`
}


export const BASE: AppState = {
  page: 'overview',
  date: DEFAULT_DATE,
  sensor: 'ALL',
  metric: 'extent',
  scenario: 'B',
  theme: 'ikarus-light',
  selectedCellId: null,
  showCells: true,
  showPoints: false,
  showMunicipalities: true,
  navOpen: false,
  lang: DEFAULT_LANG,
}

/** True when a key event should close an open overlay (Escape, not already handled by another control). */
export function isCloseKey(e: { key: string; defaultPrevented?: boolean; isComposing?: boolean }): boolean {
  return e.key === 'Escape' && !e.defaultPrevented && !e.isComposing
}
