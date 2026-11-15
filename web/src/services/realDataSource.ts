/**
 * REAL data source: Mission 05 results (SQLite -> tools/export_web -> static JSON). EXPERIMENTAL / NOT VALIDATED.
 * The front end only presents what the scientific engine produced: no indicator is recomputed here. When a file is missing
 * the promise rejects and the interface shows the unavailability; fixtures are never substituted.
 */
import type {
  Cell,
  CellCategory,
  CellDay,
  ComparisonReason,
  CoverageState,
  DayRecord,
  DetectionRecord,
  ExampleStory,
  MonthSeriesPoint,
  RefBasis,
  RefPosition,
  SatelliteDay,
  SatelliteId,
  ScaleMax,
  Scenario,
  SensorDay,
  SensorId,
  SourceFile,
  WeeklyFacts,
  WeeklyReferencePoint,
  YearSummary,
} from '../types'
import type { FireCalendarDataSource, Need } from './dataSource'
import { REGION, makeCell } from '../geo/region'

// ---- raw schema (tools/export_web/exportar_web.py, schema 1) --------------------------------------------------------
interface RawSat {
  detections: number
  passUtc: string | null
  coverageFraction: number
  coverageState: CoverageState
  catalogueComplete: boolean | null
  conflictRecords: number
  productVersion: string | null
}
interface RawSensor {
  detections: number
  valid: boolean
  activeCells: number | null
  extent: number | null
  extentNumerator: number | null
  extentDenominator: number | null
  intensity: number | null
  coverageFraction: number
  coverageState: CoverageState
  excludedDetections: number
  unknownCells: number
}
interface RawScenario {
  modis: RawSensor
  viirs: RawSensor
  comparison: {
    comparable: boolean
    reason: ComparisonReason | null
    K: number | null
    Knull: number | null
    both: number
    onlyModis: number | null
    onlyViirs: number | null
    union: number
    comparableCells: number
    modisConfirmedShare: number | null
  }
  referenceModis: { position: RefPosition; nReferenceYears: number }
  referenceViirs: { position: RefPosition; nReferenceYears: number | null }
}
interface RawDay {
  date: string
  year: number
  month: number
  weekOfYear: number
  modisBlock: 'A' | 'B'
  modisVersion: string | null
  viirsVersion: string | null
  satellites: Record<SatelliteId, RawSat>
  A: RawScenario
  B: RawScenario
  passOffsetMin: number | null
  sources: number[]
}
interface RawSensorPeriod {
  extent: number | null
  intensity: number | null
  validDays: number
  detections: number
  position: RefPosition
  nReferenceYears: number
  refMin: number | null
  refMax: number | null
  detectionsPosition?: RefPosition
  detectionsRef?: [number, number] | null
}
interface RawPeriod {
  year: number
  semana_do_ano?: number
  mes?: number
  A: { modis: RawSensorPeriod; viirs: RawSensorPeriod }
  B: { modis: RawSensorPeriod; viirs: RawSensorPeriod }
}
interface YearFile {
  schema: number
  year: number
  days: RawDay[]
  weeks: RawPeriod[]
  months: RawPeriod[]
}
interface CellsFile {
  days: Record<string, { a: number[][]; cov: Record<string, [number, number] | { c: string; f: number[] }>; fam: [number | string, number | string] }>
}
interface DetFile {
  days: Record<string, (string | number | null)[][]>
}
interface Meta {
  schema: number
  range: { first: string; last: string; days: number }
  cells: [number, number][]
  counts: { uniqueDetectionsInBbox: number; detectionsTocantins: number; sources: number; activeCellDays: number }
  sources: { sha256: string; file: string; product: string }[]
  summary: Record<string, Record<string, unknown>>
  scale: Record<Scenario, { extent: Record<SensorId, number>; intensity: Record<SensorId, number>; detections: Record<SensorId, number> }>
}

interface SensorAgg {
  medianExtent: number | null
  medianIntensity: number | null
  uncertainDays: number
  excludedDays: number
}

export type JsonLoader = (relativePath: string) => Promise<unknown>

const CLS: CoverageState[] = ['CORROBORATED', 'PARTIAL', 'INDETERMINATE', 'NO_COVERAGE_CORROBORATED']
const CAT: CellCategory[] = ['NONE', 'BOTH', 'MODIS_ONLY', 'VIIRS_ONLY', 'UNCERTAIN']
const SAT_KEY: Record<SatelliteId, string> = { Terra: 'TERRA', Aqua: 'AQUA', 'NOAA-20': 'N20' }
const SAT_BY_INDEX: SatelliteId[] = ['Terra', 'Aqua', 'NOAA-20']

const mapSat = (name: SatelliteId, s: RawSat): SatelliteDay => ({
  satellite: name,
  detections: s.detections,
  passUtc: s.passUtc,
  coverageState: s.coverageState,
  coverageFraction: s.coverageFraction,
  catalogueComplete: s.catalogueComplete === true,
  conflictRecords: s.conflictRecords,
  productVersion: s.productVersion,
})

function mapSensor(sensor: SensorId, s: RawSensor, sats: SatelliteDay[], version: string | null): SensorDay {
  return {
    sensor,
    detections: s.detections,
    activeCells: s.activeCells,
    extent: s.extent,
    extentNumerator: s.extentNumerator,
    extentDenominator: s.extentDenominator,
    intensity: s.intensity,
    coverageFraction: s.coverageFraction,
    coverageState: s.coverageState,
    unknownCells: s.unknownCells,
    excludedDetections: s.excludedDetections,
    valid: s.valid,
    satellites: sats,
    productVersion: version,
  }
}

function toDay(r: RawDay, scenario: Scenario): DayRecord {
  const sc = r[scenario]
  const terra = mapSat('Terra', r.satellites.Terra)
  const aqua = mapSat('Aqua', r.satellites.Aqua)
  const n20 = mapSat('NOAA-20', r.satellites['NOAA-20'])
  const flags: string[] = []
  for (const s of [terra, aqua, n20]) {
    const key = SAT_KEY[s.satellite]
    if (s.conflictRecords > 0) flags.push(`${key}_CONFLICT`)
    else if (!s.catalogueComplete) flags.push(`${key}_INCOMPLETE`)
    else if (s.coverageState === 'PARTIAL') flags.push(`${key}_PARTIAL`)
  }
  const basis = (position: RefPosition, b: RefBasis): RefBasis => (position === 'NO_DATA' ? 'NONE' : b)
  const modisBasis: RefBasis = r.modisBlock === 'A' ? 'BLOCK_A' : 'BLOCK_B'
  const c = sc.comparison
  return {
    date: r.date,
    year: r.year,
    month: r.month,
    weekOfYear: r.weekOfYear,
    modisBlock: r.modisBlock,
    modis: mapSensor('MODIS', sc.modis, [terra, aqua], r.modisVersion),
    viirs: mapSensor('VIIRS', sc.viirs, [n20], r.viirsVersion),
    comparison: {
      comparable: c.comparable,
      reason: c.reason,
      K: c.K,
      Knull: c.Knull,
      both: c.both,
      onlyModis: c.onlyModis ?? 0,
      onlyViirs: c.onlyViirs ?? 0,
      union: c.union,
      comparableCells: c.comparableCells,
      modisConfirmedShare: c.modisConfirmedShare,
      passOffsetMin: r.passOffsetMin,
    },
    referenceModis: { position: sc.referenceModis.position, nReferenceYears: sc.referenceModis.nReferenceYears, basis: basis(sc.referenceModis.position, modisBasis) },
    referenceViirs: { position: sc.referenceViirs.position, nReferenceYears: sc.referenceViirs.nReferenceYears ?? 0, basis: basis(sc.referenceViirs.position, 'OTHER_YEARS') },
    flags,
    divergence: null,
  }
}

const iso = (y: number, m: number, d: number) => `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
/** Day of the fixed 7-day block (1..53): the first block day is day-of-year 7*(w-1)+1. `offset` 0..6 selects the day inside the block. */
export function blockDate(year: number, week: number, offset = 3): string {
  const t = Date.UTC(year, 0, 1) + (7 * (week - 1) + offset) * 86400000
  const d = new Date(t)
  return iso(d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate())
}

export function createRealDataSource(load: JsonLoader): FireCalendarDataSource {
  let meta: Meta | null = null
  let cells: Cell[] = []
  const years = new Map<number, YearFile>()
  const dayIndex = new Map<string, RawDay>()
  const cellFiles = new Map<string, CellsFile>()
  const detFiles = new Map<string, DetFile>()
  const pending = new Map<string, Promise<void>>()
  const dayCache = new Map<string, DayRecord>()

  const need = (cond: boolean, what: string) => {
    if (!cond) throw new Error(`REAL data not loaded: ${what}`)
  }
  const once = (key: string, fn: () => Promise<void>) => {
    let p = pending.get(key)
    if (!p) {
      p = fn().catch((e) => {
        pending.delete(key)
        throw e
      })
      pending.set(key, p)
    }
    return p
  }
  const ym = (date: string) => date.slice(0, 7)

  const ensure = (n: Need): Promise<void> => {
    if (n.kind === 'year') {
      return once(`year:${n.year}`, async () => {
        const f = (await load(`year/${n.year}.json`)) as YearFile
        years.set(n.year, f)
        for (const d of f.days) dayIndex.set(d.date, d)
      })
    }
    if (n.kind === 'cells') {
      return once(`cells:${ym(n.date)}`, async () => {
        cellFiles.set(ym(n.date), (await load(`cells/${ym(n.date)}.json`)) as CellsFile)
      })
    }
    return once(`det:${ym(n.date)}`, async () => {
      detFiles.set(ym(n.date), (await load(`det/${ym(n.date)}.json`)) as DetFile)
    })
  }
  const isReady = (n: Need): boolean => (n.kind === 'year' ? years.has(n.year) : n.kind === 'cells' ? cellFiles.has(ym(n.date)) : detFiles.has(ym(n.date)))

  const getDay = (date: string, scenario: Scenario): DayRecord => {
    const key = `${date}|${scenario}`
    const hit = dayCache.get(key)
    if (hit) return hit
    const raw = dayIndex.get(date)
    need(!!raw, `year ${date.slice(0, 4)}`)
    const rec = toDay(raw!, scenario)
    dayCache.set(key, rec)
    return rec
  }

  const yearOf = (y: number) => {
    const f = years.get(y)
    need(!!f, `year ${y}`)
    return f!
  }
  const period = (p: RawPeriod, scenario: Scenario, sensor: SensorId) => p[scenario][sensor === 'MODIS' ? 'modis' : 'viirs']

  function getCellDays(date: string, scenario: Scenario): CellDay[] {
    const cf = cellFiles.get(ym(date))
    need(!!cf, `cells ${ym(date)}`)
    const day = cf!.days[date]
    need(!!day, `cells ${date}`)
    const code = scenario === 'A' ? 4 : 5
    const active = new Map<number, number[]>(day.a.map((r) => [r[0], r]))
    const fam = (v: number | string, k: number): CoverageState => CLS[typeof v === 'number' ? v : Number(v[k])]
    return cells.map((cell, k) => {
      const row = active.get(k)
      const mc = fam(day.fam[0], k)
      const vc = fam(day.fam[1], k)
      const sat: Record<string, { state: CoverageState; fraction: number }> = {}
      for (const [name, v] of Object.entries(day.cov)) {
        sat[name] = Array.isArray(v) ? { state: CLS[v[0]], fraction: v[1] / 100 } : { state: CLS[Number(v.c[k])], fraction: v.f[k] / 100 }
      }
      const terra = row ? row[1] : 0
      const aqua = row ? row[2] : 0
      const n20 = row ? row[3] : 0
      let category: CellCategory = row ? CAT[row[code]] : 'NONE'
      if (!row && (mc === 'INDETERMINATE' || vc === 'INDETERMINATE')) category = 'UNCERTAIN'
      return {
        cell,
        category,
        modisCount: terra + aqua,
        viirsCount: n20,
        terra,
        aqua,
        noaa20: n20,
        modisCoverage: mc,
        viirsCoverage: vc,
        satCoverage: sat as CellDay['satCoverage'],
        excludedInA: row ? row[6] === 1 : false,
      }
    })
  }

  function getDetections(date: string, cellId: string): DetectionRecord[] {
    const df = detFiles.get(ym(date))
    need(!!df, `detections ${ym(date)}`)
    const idx = cells.findIndex((c) => c.id === cellId)
    if (idx < 0) return []
    const day = yearOf(Number(date.slice(0, 4))).days.find((d) => d.date === date)
    return (df!.days[date] ?? [])
      .filter((r) => r[0] === idx)
      .map((r) => {
        const sat = SAT_BY_INDEX[r[1] as number]
        const minute = r[2] as number
        const src = meta!.sources[r[10] as number]
        const sensor: SensorId = sat === 'NOAA-20' ? 'VIIRS' : 'MODIS'
        const scan = r[8] as number | null
        const track = r[9] as number | null
        const dn = r[7] as string | null
        return {
          id: `${src.sha256.slice(0, 8)}:${r[11]}`,
          date,
          cellId,
          sensor,
          satellite: sat,
          timeUtc: `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`,
          lat: r[3] as number,
          lon: r[4] as number,
          frpMw: r[5] as number | null,
          confidence: r[6] as string | null,
          pixelKm: scan !== null && track !== null ? [scan, track] : null,
          dayNight: dn === 'D' || dn === 'N' ? dn : null,
          productVersion: day ? day.satellites[sat].productVersion : null,
          sourceFile: src.file,
          sourceSha256: src.sha256,
          sourceLine: r[11] as number | null,
        }
      })
  }

  function weeklyFacts(year: number, week: number, sensor: SensorId): WeeklyFacts | undefined {
    const f = years.get(year)
    if (!f) return undefined
    const w = f.weeks.find((x) => x.semana_do_ano === week)
    if (!w) return undefined
    const p = period(w, 'B', sensor)
    return {
      year,
      week,
      sensor,
      detections: p.detections,
      detectionsPosition: p.detectionsPosition ?? 'NO_DATA',
      detectionsRef: p.detectionsRef ?? null,
      extent: p.extent,
      extentPosition: p.position,
      extentRef: p.refMin !== null && p.refMax !== null ? [p.refMin, p.refMax] : null,
      nReferenceYears: p.nReferenceYears,
    }
  }

  return {
    mode: 'REAL',
    isSimulated: false,
    async init() {
      if (meta) return
      const m = (await load('meta.json')) as Meta
      if (!m || m.schema !== 1 || !Array.isArray(m.cells)) throw new Error('REAL data: unexpected meta.json')
      meta = m
      cells = m.cells.map(([i, j]) => makeCell(i, j))
    },
    ensure,
    isReady,
    getRegion: () => REGION,
    getYears: () => [2021, 2022, 2023, 2024, 2025],
    getCells: () => cells,
    getDay,
    getMonth(year, month, scenario) {
      return yearOf(year)
        .days.filter((d) => d.month === month)
        .map((d) => getDay(d.date, scenario))
    },
    getYearSeries(year, scenario): MonthSeriesPoint[] {
      return yearOf(year).months.map((m) => ({
        month: m.mes!,
        modisExtent: period(m, scenario, 'MODIS').extent,
        viirsExtent: period(m, scenario, 'VIIRS').extent,
        modisDetections: period(m, scenario, 'MODIS').detections,
        viirsDetections: period(m, scenario, 'VIIRS').detections,
      }))
    },
    getWeeklyReference(year, sensor, scenario): WeeklyReferencePoint[] {
      return yearOf(year).weeks.map((w) => {
        const own = period(w, scenario, sensor)
        return { week: w.semana_do_ano!, modis: period(w, scenario, 'MODIS').extent, viirs: period(w, scenario, 'VIIRS').extent, refMin: own.refMin, refMax: own.refMax }
      })
    },
    getCellDays,
    getDetections,
    getExamples(): ExampleStory[] {
      return [
        { id: 'count-vs-extent', date: blockDate(2023, 47), metric: 'extent', sensor: 'MODIS', featured: true, weekly: weeklyFacts(2023, 47, 'MODIS') },
        { id: 'extent-vs-count', date: blockDate(2021, 31), metric: 'extent', sensor: 'VIIRS', featured: true, weekly: weeklyFacts(2021, 31, 'VIIRS') },
        { id: 'agree', date: '2024-09-10', metric: 'concordance', sensor: 'ALL', featured: true },
        { id: 'conflict', date: '2025-05-14', metric: 'detections', sensor: 'MODIS', featured: true },
        { id: 'aqua-partial', date: '2024-08-31', metric: 'extent', sensor: 'MODIS' },
        { id: 'incomplete', date: '2023-09-30', metric: 'concordance', sensor: 'ALL' },
        { id: 'reference', date: '2021-07-14', metric: 'extent', sensor: 'MODIS' },
      ]
    },
    getRange() {
      need(!!meta, 'meta')
      return { first: meta!.range.first, last: meta!.range.last }
    },
    getScaleMax(scenario): ScaleMax {
      need(!!meta, 'meta')
      return meta!.scale[scenario]
    },
    getYearSummary(year, scenario): YearSummary {
      need(!!meta, 'meta')
      const s = meta!.summary[String(year)] as { detections: Record<SensorId, number> } & Record<string, unknown>
      const sc = s[scenario] as Record<string, SensorAgg> & { days: number; comparableDays: number; medianK: number | null; kDays: number }
      const sensor = (k: SensorId) => ({ detections: s.detections[k], medianExtent: sc[k].medianExtent, medianIntensity: sc[k].medianIntensity, uncertainDays: sc[k].uncertainDays, excludedDays: sc[k].excludedDays })
      return { days: sc.days, MODIS: sensor('MODIS'), VIIRS: sensor('VIIRS'), comparableDays: sc.comparableDays, medianK: sc.medianK, kDays: sc.kDays }
    },
    getSources(): SourceFile[] {
      return meta ? meta.sources : []
    },
  }
}

/** Browser loader: static files served next to the app (public/data/real, produced by tools/export_web). */
export function fetchLoader(base: string): JsonLoader {
  return async (rel) => {
    const res = await fetch(`${base}data/real/${rel}`, { cache: 'force-cache' })
    if (!res.ok) throw new Error(`HTTP ${res.status} ${rel}`)
    return res.json()
  }
}
