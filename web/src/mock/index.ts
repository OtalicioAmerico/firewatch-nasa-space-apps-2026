/**
 * SIMULATED dataset (MOCK). Assembles the whole 2021-2025 demo calendar for the region from the seeded generator.
 * No NASA / FIRMS / CMR / Mission 05 value is used anywhere in this folder (only the public region geometry is real).
 */
import type {
  CellDay,
  DayRecord,
  Divergence,
  ScaleMax,
  YearSummary,
  ExampleStory,
  MonthSeriesPoint,
  RefPosition,
  ReferenceInfo,
  Scenario,
  SensorId,
  DetectionRecord,
  WeeklyReferencePoint,
} from '../types'
import {
  YEARS,
  buildCellDays,
  buildDayRecord,
  buildDetections,
  generateDay,
  modisBlockOf,
  refPositionOf,
  weekOfYear,
  SCRIPTED,
  type DayInternal,
} from './generator'
import { CELLS } from './geometry'

export { CELLS, REGION } from './geometry'
export { YEARS, SCRIPTED }


function allDates(): string[] {
  const out: string[] = []
  for (let t = Date.UTC(2021, 0, 1); t <= Date.UTC(2025, 11, 31); t += 86400000) out.push(new Date(t).toISOString().slice(0, 10))
  return out
}
export const ALL_DATES = allDates()

const internal = new Map<string, DayInternal>()
export function dayInternal(date: string): DayInternal {
  let d = internal.get(date)
  if (!d) {
    d = generateDay(date)
    internal.set(date, d)
  }
  return d
}

type Base = ReturnType<typeof buildDayRecord>
const recordsBase: Record<Scenario, Base[]> = { A: [], B: [] }
const recordsFull: Record<Scenario, Map<string, DayRecord>> = { A: new Map(), B: new Map() }
let built = false

function noRef(position: RefPosition = 'NO_DATA'): ReferenceInfo {
  return { position, nReferenceYears: 0, basis: 'NONE' }
}

function mean(v: (number | null)[], min = 4): number | null {
  const x = v.filter((n): n is number => n !== null)
  return x.length >= min ? x.reduce((a, b) => a + b, 0) / x.length : null
}

/** weekly[scenario][sensor][year][week] */
const weekly: Record<Scenario, Record<SensorId, Record<number, Record<number, number | null>>>> = {
  A: { MODIS: {}, VIIRS: {} },
  B: { MODIS: {}, VIIRS: {} },
}

function build() {
  if (built) return
  built = true
  for (const sc of ['A', 'B'] as Scenario[]) {
    recordsBase[sc] = ALL_DATES.map((d) => buildDayRecord(dayInternal(d), sc))
    for (const sensor of ['MODIS', 'VIIRS'] as SensorId[]) {
      for (const y of YEARS) {
        weekly[sc][sensor][y] = {}
        const byWeek = new Map<number, (number | null)[]>()
        for (const r of recordsBase[sc]) {
          if (r.year !== y) continue
          const arr = byWeek.get(r.weekOfYear) ?? []
          arr.push(sensor === 'MODIS' ? r.modis.extent : r.viirs.extent)
          byWeek.set(r.weekOfYear, arr)
        }
        for (const [w, arr] of byWeek) weekly[sc][sensor][y][w] = mean(arr)
      }
    }
    const percentile = new Map<string, number>()
    // percentile of raw detections and of extent within the year (for the divergence storytelling)
    const pct = (vals: number[]): ((x: number) => number) => {
      const s = [...vals].sort((a, b) => a - b)
      return (x) => {
        let lo = 0
        let hi = s.length
        while (lo < hi) {
          const m = (lo + hi) >> 1
          if (s[m] < x) lo = m + 1
          else hi = m
        }
        return s.length ? lo / s.length : 0
      }
    }
    for (const y of YEARS) {
      for (const sensor of ['MODIS', 'VIIRS'] as SensorId[]) {
        const rows = recordsBase[sc].filter((r) => r.year === y)
        const det = rows.map((r) => (sensor === 'MODIS' ? r.modis.detections : r.viirs.detections))
        const ext = rows.map((r) => (sensor === 'MODIS' ? r.modis.extent : r.viirs.extent)).filter((v): v is number => v !== null)
        const pd = pct(det)
        const pe = pct(ext)
        for (const r of rows) {
          const e = sensor === 'MODIS' ? r.modis.extent : r.viirs.extent
          const dcount = sensor === 'MODIS' ? r.modis.detections : r.viirs.detections
          if (e === null || dcount < 25) continue
          percentile.set(`${r.date}|${sensor}`, pd(dcount) - pe(e))
        }
      }
    }
    for (const base of recordsBase[sc]) {
      const ref = (sensor: SensorId): ReferenceInfo => {
        const own = weekly[sc][sensor][base.year]?.[base.weekOfYear] ?? null
        if (own === null) return noRef('NO_DATA')
        const years = YEARS.filter((y) => y !== base.year && (sensor === 'VIIRS' || modisBlockOf(`${y}-06-01`) === base.modisBlock))
        const refVals = years.map((y) => weekly[sc][sensor][y]?.[base.weekOfYear]).filter((v): v is number => v !== null && v !== undefined)
        return {
          position: refPositionOf(own, refVals),
          nReferenceYears: refVals.length,
          basis: sensor === 'VIIRS' ? 'OTHER_YEARS' : base.modisBlock === 'A' ? 'BLOCK_A' : 'BLOCK_B',
        }
      }
      const dm = percentile.get(`${base.date}|MODIS`)
      const dv = percentile.get(`${base.date}|VIIRS`)
      let divergence: Divergence | null = null
      const pick = Math.abs(dm ?? 0) >= Math.abs(dv ?? 0) ? ['MODIS', dm] : ['VIIRS', dv]
      const gap = pick[1] as number | undefined
      if (gap !== undefined && Math.abs(gap) >= 0.15) {
        divergence = { sensor: pick[0] as SensorId, kind: gap > 0 ? 'COUNT_HIGHER_THAN_EXTENT' : 'EXTENT_HIGHER_THAN_COUNT' }
      }
      recordsFull[sc].set(base.date, { ...base, referenceModis: ref('MODIS'), referenceViirs: ref('VIIRS'), divergence })
    }
  }
}

export function getDay(date: string, scenario: Scenario): DayRecord {
  build()
  const r = recordsFull[scenario].get(date)
  if (!r) throw new Error(`No simulated record for ${date}`)
  return r
}

export function getMonth(year: number, month: number, scenario: Scenario): DayRecord[] {
  build()
  return ALL_DATES.filter((d) => d.startsWith(`${year}-${String(month).padStart(2, '0')}`)).map((d) => getDay(d, scenario))
}

export function getYearSeries(year: number, scenario: Scenario): MonthSeriesPoint[] {
  build()
  return Array.from({ length: 12 }, (_, i) => {
    const days = getMonth(year, i + 1, scenario)
    const m = days.map((d) => d.modis.extent)
    const v = days.map((d) => d.viirs.extent)
    return {
      month: i + 1,
      modisExtent: mean(m, 1),
      viirsExtent: mean(v, 1),
      modisDetections: days.reduce((a, d) => a + d.modis.detections, 0),
      viirsDetections: days.reduce((a, d) => a + d.viirs.detections, 0),
    }
  })
}

export function getWeeklyReference(year: number, sensor: SensorId, scenario: Scenario): WeeklyReferencePoint[] {
  build()
  const out: WeeklyReferencePoint[] = []
  for (let w = 1; w <= 53; w++) {
    const own = weekly[scenario][sensor][year]?.[w] ?? null
    const years = YEARS.filter((y) => y !== year && (sensor === 'VIIRS' || modisBlockOf(`${y}-06-01`) === modisBlockOf(`${year}-06-01`)))
    const ref = years.map((y) => weekly[scenario][sensor][y]?.[w]).filter((v): v is number => v !== null && v !== undefined)
    out.push({
      week: w,
      modis: sensor === 'MODIS' ? own : null,
      viirs: sensor === 'VIIRS' ? own : null,
      refMin: ref.length >= 2 ? Math.min(...ref) : null,
      refMax: ref.length >= 2 ? Math.max(...ref) : null,
    })
  }
  return out
}

export function getCellDays(date: string, scenario: Scenario): CellDay[] {
  return buildCellDays(dayInternal(date), scenario)
}

export function getDetections(date: string, cellId: string): DetectionRecord[] {
  const idx = CELLS.findIndex((c) => c.id === cellId)
  if (idx < 0) return []
  return buildDetections(dayInternal(date), idx)
}

// ---- storytelling examples (found in the simulated data itself) ----------------------------------------------------
function findSameCountPair(): { a: string; b: string } | null {
  build()
  const recs = recordsBase.B
  for (const y of YEARS) {
    const rows = recs.filter((r) => r.year === y && r.month >= 6 && r.month <= 10 && r.modis.detections >= 60 && r.modis.extent !== null)
    for (let i = 0; i < rows.length; i++) {
      for (let j = i + 1; j < rows.length; j++) {
        const x = rows[i]
        const z = rows[j]
        const rel = Math.abs(x.modis.detections - z.modis.detections) / Math.max(x.modis.detections, z.modis.detections)
        const re = Math.max(x.modis.extent!, z.modis.extent!) / Math.max(Math.min(x.modis.extent!, z.modis.extent!), 1e-9)
        if (rel <= 0.03 && re >= 1.4) return { a: x.date, b: z.date }
      }
    }
  }
  return null
}

export function getExamples(): ExampleStory[] {
  const pair = findSameCountPair()
  return [
    { id: 'count-vs-extent', date: pair?.a ?? '2021-08-18', relatedDate: pair?.b, metric: 'extent', sensor: 'MODIS', featured: true },
    { id: 'agree', date: '2021-08-18', metric: 'concordance', sensor: 'ALL' },
    { id: 'conflict', date: '2023-06-08', metric: 'detections', sensor: 'MODIS' },
    { id: 'incomplete', date: '2022-09-27', metric: 'concordance', sensor: 'ALL', featured: true },
    { id: 'aqua-partial', date: '2024-07-19', metric: 'extent', sensor: 'MODIS', featured: true },
    { id: 'both-partial', date: '2025-08-21', metric: 'extent', sensor: 'ALL' },
    { id: 'reference', date: '2021-07-14', metric: 'extent', sensor: 'MODIS', featured: true },
  ]
}

function medianOf(v: number[]): number | null {
  if (!v.length) return null
  const s = [...v].sort((a, b) => a - b)
  const m = s.length >> 1
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

/** Global maxima of the simulated series, so colours are comparable between months and years. */
export function getScaleMax(scenario: Scenario): ScaleMax {
  const m: ScaleMax = { extent: { MODIS: 0.001, VIIRS: 0.001 }, intensity: { MODIS: 0.001, VIIRS: 0.001 }, detections: { MODIS: 1, VIIRS: 1 } }
  build()
  for (const d of recordsFull[scenario].values()) {
    for (const s of ['MODIS', 'VIIRS'] as SensorId[]) {
      const sd = s === 'MODIS' ? d.modis : d.viirs
      if (sd.extent !== null) m.extent[s] = Math.max(m.extent[s], sd.extent)
      if (sd.intensity !== null) m.intensity[s] = Math.max(m.intensity[s], sd.intensity)
      m.detections[s] = Math.max(m.detections[s], sd.detections)
    }
  }
  return m
}

export function getYearSummary(year: number, scenario: Scenario): YearSummary {
  const days: DayRecord[] = []
  for (let m = 1; m <= 12; m++) days.push(...getMonth(year, m, scenario))
  const sensor = (s: SensorId) => {
    const sd = days.map((d) => (s === 'MODIS' ? d.modis : d.viirs))
    return {
      detections: sd.reduce((a, x) => a + x.detections, 0),
      medianExtent: medianOf(sd.filter((x) => x.extent !== null).map((x) => x.extent!)),
      medianIntensity: medianOf(sd.filter((x) => x.intensity !== null).map((x) => x.intensity!)),
      uncertainDays: sd.filter((x) => x.coverageState !== 'CORROBORATED').length,
      excludedDays: sd.filter((x) => !x.valid).length,
    }
  }
  const ks = days.map((d) => d.comparison.K).filter((k): k is number => k !== null)
  return { days: days.length, MODIS: sensor('MODIS'), VIIRS: sensor('VIIRS'), comparableDays: days.filter((d) => d.comparison.comparable).length, medianK: medianOf(ks), kDays: ks.length }
}

export { weekOfYear }
