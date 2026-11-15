/**
 * SIMULATED data generator (Mission 06A mockup). Everything produced here is MOCK data created from a seeded random
 * generator: it does not come from NASA, FIRMS, CMR or from the Mission 05 results, and must never be shown as a
 * scientific result. The arithmetic below only keeps the simulated numbers internally consistent (map = calendar = evidence).
 */
import type {
  CellCategory,
  CellDay,
  ComparisonReason,
  CoverageState,
  DayRecord,
  ModisBlock,
  RefPosition,
  SatelliteDay,
  SatelliteId,
  Scenario,
  SensorDay,
  SensorId,
  DetectionRecord,
} from '../types'
import { gauss, hashString, mulberry32, poisson, rngFor, type Rng } from '../lib/prng'
import { CELLS, CELL_SIZE } from './geometry'

export const YEARS = [2021, 2022, 2023, 2024, 2025]
const N = CELLS.length
const INDEX_BY_IJ = new Map(CELLS.map((c, k) => [`${c.i}_${c.j}`, k]))

// ---- tunables of the simulation (not scientific parameters) -------------------------------------------------------
export const MIN_CORROBORATED_FRACTION_A = 0.5
export const MIN_COMPARABLE_FRACTION = 0.8
const CORROBORATED_AT = 0.95
const YEAR_LEVEL: Record<number, number> = { 2021: 0.85, 2022: 1.05, 2023: 0.8, 2024: 1.45, 2025: 0.95 }

/** Scripted days so that the demo always contains the situations the interface must explain (all MOCK). */
export const SCRIPTED: Record<string, { note: string; override: ScriptedOverride }> = {
  '2021-08-18': { note: 'PEAK_BOTH_COVERED', override: { levelBoost: 1.9 } },
  '2022-09-27': { note: 'N20_INCOMPLETE', override: { n20Incomplete: true, levelBoost: 1.5 } },
  '2023-06-08': { note: 'TERRA_CONFLICT', override: { terraConflict: 38 } },
  '2024-07-19': { note: 'AQUA_PARTIAL', override: { aquaCutLonFrac: 0.38, levelBoost: 1.3 } },
  '2025-08-21': { note: 'MODIS_BOTH_PARTIAL', override: { aquaCutLonFrac: 0.55, terraCutLonFrac: 0.7, levelBoost: 1.2 } },
}

interface ScriptedOverride {
  levelBoost?: number
  n20Incomplete?: boolean
  terraConflict?: number
  aquaCutLonFrac?: number
  terraCutLonFrac?: number
}

interface SatFlags {
  catalogueComplete: boolean
  conflictRecords: number
  cutFrac: number | null // fraction of the longitude range covered, null = full coverage
}

export interface DayInternal {
  date: string
  year: number
  level: number
  terra: Uint16Array
  aqua: Uint16Array
  viirs: Uint16Array
  cov: { terra: Float32Array; aqua: Float32Array; n20: Float32Array }
  flags: { terra: SatFlags; aqua: SatFlags; n20: SatFlags }
  note: string | null
}

// ---- seasonal activity ---------------------------------------------------------------------------------------------
function dayOfYear(date: string): number {
  const d = new Date(date + 'T00:00:00Z')
  return Math.floor((d.getTime() - Date.UTC(d.getUTCFullYear(), 0, 0)) / 86400000)
}

export function weekOfYear(date: string): number {
  return Math.floor((dayOfYear(date) - 1) / 7) + 1
}

function seasonal(doy: number): number {
  const g = (c: number, w: number) => Math.exp(-0.5 * ((doy - c) / w) ** 2)
  return 0.025 + 0.95 * g(255, 38) + 0.35 * g(205, 28) + 0.1 * g(300, 25)
}

// ---- spatial weights (smooth fake field; three seasonal phases) ----------------------------------------------------
const BLOBS: [number, number, number, number][] = [
  [-48.0, -11.6, 0.9, 1.0],
  [-47.2, -9.4, 0.8, 0.9],
  [-49.6, -7.6, 0.7, 0.8],
  [-46.9, -6.6, 0.6, 0.7],
  [-48.6, -10.2, 0.5, 0.9],
  [-47.6, -12.6, 0.6, 0.6],
]
function buildWeights(phase: number): Float64Array {
  const w = new Float64Array(N)
  const rng = mulberry32(7000 + phase)
  for (let k = 0; k < N; k++) {
    const cx = (CELLS[k].lon0 + CELLS[k].lon1) / 2
    const cy = (CELLS[k].lat0 + CELLS[k].lat1) / 2
    let s = 0.04
    BLOBS.forEach(([bx, by, sg, a], b) => {
      const shift = (phase - 1) * 0.35 * (b % 2 ? 1 : -1)
      s += a * Math.exp(-(((cx - bx - shift) / sg) ** 2 + ((cy - by + shift * 0.4) / sg) ** 2) / 2)
    })
    w[k] = s * (0.6 + 0.8 * rng())
  }
  return w
}
const WEIGHTS = [buildWeights(0), buildWeights(1), buildWeights(2)]
const LON_MIN = Math.min(...CELLS.map((c) => c.lon0))
const LON_MAX = Math.max(...CELLS.map((c) => c.lon1))

function pickCells(rng: Rng, w: Float64Array, n: number): number[] {
  const keys: [number, number][] = Array.from({ length: N }, () => [0, 0])
  for (let k = 0; k < N; k++) keys[k] = [Math.pow(rng(), 1 / Math.max(w[k], 1e-6)), k]
  keys.sort((a, b) => b[0] - a[0])
  return keys.slice(0, Math.min(n, N)).map((x) => x[1])
}

function coverageArray(cutFrac: number | null): Float32Array {
  const f = new Float32Array(N).fill(1)
  if (cutFrac === null) return f
  const cut = LON_MIN + cutFrac * (LON_MAX - LON_MIN)
  for (let k = 0; k < N; k++) {
    const c = CELLS[k]
    if (c.lon1 <= cut) f[k] = 1
    else if (c.lon0 >= cut) f[k] = 0
    else f[k] = (cut - c.lon0) / CELL_SIZE
  }
  return f
}

// ---- one simulated day ---------------------------------------------------------------------------------------------
export function generateDay(date: string): DayInternal {
  const rng = rngFor('mock-day:' + date)
  const year = Number(date.slice(0, 4))
  const doy = dayOfYear(date)
  const script = SCRIPTED[date]?.override ?? {}
  const level = Math.max(0, seasonal(doy) * (YEAR_LEVEL[year] ?? 1) * Math.exp(0.45 * gauss(rng)) * (script.levelBoost ?? 1))
  const phase = doy < 190 ? 0 : doy < 270 ? 1 : 2
  const nLatent = Math.min(Math.round(0.5 * N), Math.round(3 + 92 * Math.pow(level, 1.05)))
  const latent = pickCells(rng, WEIGHTS[phase], nLatent)
  const terra = new Uint16Array(N)
  const aqua = new Uint16Array(N)
  const viirs = new Uint16Array(N)
  for (const k of latent) {
    const lam = 0.6 + -Math.log(Math.max(rng(), 1e-9)) * 1.1 * Math.sqrt(0.6 + level)
    if (rng() < 0.9) viirs[k] = 1 + poisson(rng, lam * 2.3)
    if (rng() < 0.3) terra[k] = 1 + poisson(rng, lam * 0.45)
    if (rng() < 0.34) aqua[k] = 1 + poisson(rng, lam * 0.5)
  }
  const extraV = 0.003 + 0.02 * Math.min(level, 1.5)
  const extraM = 0.0008 + 0.003 * Math.min(level, 1.5)
  for (let k = 0; k < N; k++) {
    if (viirs[k] === 0 && rng() < extraV) viirs[k] = 1 + poisson(rng, 0.5)
    if (terra[k] === 0 && rng() < extraM) terra[k] = 1
    if (aqua[k] === 0 && rng() < extraM) aqua[k] = 1
  }
  // coverage / catalogue situations
  const r1 = rng()
  const r2 = rng()
  const r3 = rng()
  const r4 = rng()
  const aquaCut = script.aquaCutLonFrac ?? (r1 < 0.26 ? 0.25 + 0.6 * r2 : null)
  const terraCut = script.terraCutLonFrac ?? (r3 < 0.035 ? 0.3 + 0.5 * r4 : null)
  const terraIncomplete = r3 > 0.965
  const n20Incomplete = script.n20Incomplete ?? r4 > 0.985
  const terraConflict = script.terraConflict ?? 0
  const cov = { terra: coverageArray(terraCut), aqua: coverageArray(aquaCut), n20: coverageArray(null) }
  // a satellite cannot record detections where the (simulated) swath does not reach
  for (let k = 0; k < N; k++) {
    if (cov.terra[k] === 0) terra[k] = 0
    if (cov.aqua[k] === 0) aqua[k] = 0
  }
  return {
    date,
    year,
    level,
    terra,
    aqua,
    viirs,
    cov,
    flags: {
      terra: { catalogueComplete: !terraIncomplete && terraConflict === 0, conflictRecords: terraConflict, cutFrac: terraCut },
      aqua: { catalogueComplete: true, conflictRecords: 0, cutFrac: aquaCut },
      n20: { catalogueComplete: !n20Incomplete, conflictRecords: 0, cutFrac: null },
    },
    note: SCRIPTED[date]?.note ?? null,
  }
}

// ---- derived quantities ----------------------------------------------------------------------------------------------
function stateOf(f: number, flags: SatFlags): CoverageState {
  if (flags.conflictRecords > 0 || !flags.catalogueComplete) return 'INDETERMINATE'
  if (f >= CORROBORATED_AT) return 'CORROBORATED'
  if (f > 0) return 'PARTIAL'
  return 'NO_COVERAGE_CORROBORATED'
}
const ORDER: CoverageState[] = ['CORROBORATED', 'PARTIAL', 'INDETERMINATE', 'NO_COVERAGE_CORROBORATED']
function best(states: CoverageState[]): CoverageState {
  for (const s of ORDER) if (states.includes(s)) return s
  return 'NO_COVERAGE_CORROBORATED'
}

export function modisBlockOf(date: string): ModisBlock {
  return date < '2023-01-01' ? 'A' : 'B'
}
export function modisVersionOf(date: string): string {
  return modisBlockOf(date) === 'A' ? '6.03' : '61.03'
}

/** Typical pass time (hours UTC) per satellite and year; simulated drift of Aqua (later) and Terra (earlier). */
export function passHour(sat: SatelliteId, year: number): number {
  if (sat === 'Aqua') return 16.9 + 0.3 * (year - 2021)
  if (sat === 'Terra') return 13.65 - 0.33 * (year - 2021)
  return 16.8
}
function hhmm(h: number): string {
  const m = Math.round(h * 60)
  return `${String(Math.floor(m / 60) % 24).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
}

interface Computed {
  famCov: { MODIS: Float32Array; VIIRS: Float32Array }
  famState: { MODIS: CoverageState[]; VIIRS: CoverageState[] }
  modisCount: Uint16Array
  satStates: { terra: CoverageState[]; aqua: CoverageState[]; n20: CoverageState[] }
}
const cache = new Map<string, Computed>()
function compute(d: DayInternal): Computed {
  const hit = cache.get(d.date)
  if (hit) return hit
  const satStates = {
    terra: Array.from(d.cov.terra, (f) => stateOf(f, d.flags.terra)),
    aqua: Array.from(d.cov.aqua, (f) => stateOf(f, d.flags.aqua)),
    n20: Array.from(d.cov.n20, (f) => stateOf(f, d.flags.n20)),
  }
  const mFcov = new Float32Array(N)
  const mState: CoverageState[] = Array.from({ length: N }, () => 'CORROBORATED' as CoverageState)
  const vState: CoverageState[] = Array.from({ length: N }, () => 'CORROBORATED' as CoverageState)
  const modisCount = new Uint16Array(N)
  for (let k = 0; k < N; k++) {
    mFcov[k] = Math.max(d.cov.terra[k], d.cov.aqua[k])
    mState[k] = best([satStates.terra[k], satStates.aqua[k]])
    vState[k] = satStates.n20[k]
    modisCount[k] = d.terra[k] + d.aqua[k]
  }
  const out: Computed = { famCov: { MODIS: mFcov, VIIRS: d.cov.n20 }, famState: { MODIS: mState, VIIRS: vState }, modisCount, satStates }
  if (cache.size > 400) cache.clear()
  cache.set(d.date, out)
  return out
}

function sum(a: Uint16Array): number {
  let s = 0
  for (let k = 0; k < a.length; k++) s += a[k]
  return s
}

function indicators(count: Uint16Array, fcov: Float32Array, states: CoverageState[], scenario: Scenario) {
  let active = 0
  let det = 0
  let denB = 0
  let unknown = 0
  let corr = 0
  let activeCorr = 0
  let detCorr = 0
  for (let k = 0; k < N; k++) {
    const a = count[k] > 0
    if (a) {
      active++
      det += count[k]
    }
    denB += Math.max(fcov[k], a ? 1 : 0)
    if (states[k] === 'INDETERMINATE' && !a) unknown++
    if (states[k] === 'CORROBORATED') {
      corr++
      if (a) {
        activeCorr++
        detCorr += count[k]
      }
    }
  }
  if (scenario === 'A') {
    const valid = corr >= MIN_CORROBORATED_FRACTION_A * N
    return {
      valid,
      active: valid ? activeCorr : null,
      den: corr,
      extent: valid ? activeCorr / corr : null,
      num: valid ? activeCorr : null,
      intensity: valid && activeCorr > 0 ? detCorr / activeCorr : null,
      excluded: det - detCorr,
      unknown,
    }
  }
  return {
    valid: true,
    active,
    den: Math.round(denB * 10) / 10,
    extent: denB > 0 ? active / denB : null,
    num: active,
    intensity: active > 0 ? det / active : null,
    excluded: 0,
    unknown,
  }
}

function sensorDay(d: DayInternal, sensor: SensorId, scenario: Scenario): SensorDay {
  const c = compute(d)
  const isM = sensor === 'MODIS'
  const count = isM ? c.modisCount : d.viirs
  const ind = indicators(count, c.famCov[sensor], c.famState[sensor], scenario)
  const sats: SatelliteDay[] = []
  const mk = (satellite: SatelliteId, arr: Uint16Array, key: 'terra' | 'aqua' | 'n20', version: string): SatelliteDay => {
    const f = d.cov[key]
    let m = 0
    for (let k = 0; k < N; k++) m += f[k]
    return {
      satellite,
      detections: sum(arr),
      passUtc: hhmm(passHour(satellite, d.year)),
      coverageState: d.flags[key].conflictRecords > 0 || !d.flags[key].catalogueComplete ? 'INDETERMINATE' : m / N >= CORROBORATED_AT ? 'CORROBORATED' : m > 0 ? 'PARTIAL' : 'NO_COVERAGE_CORROBORATED',
      coverageFraction: m / N,
      catalogueComplete: d.flags[key].catalogueComplete,
      conflictRecords: d.flags[key].conflictRecords,
      productVersion: version,
    }
  }
  if (isM) {
    sats.push(mk('Terra', d.terra, 'terra', modisVersionOf(d.date)), mk('Aqua', d.aqua, 'aqua', modisVersionOf(d.date)))
  } else {
    sats.push(mk('NOAA-20', d.viirs, 'n20', '2'))
  }
  const fam = dominant(c.famState[sensor])
  let fmean = 0
  for (let k = 0; k < N; k++) fmean += c.famCov[sensor][k]
  return {
    sensor,
    detections: sum(count),
    activeCells: ind.active,
    extent: ind.extent,
    extentNumerator: ind.num,
    extentDenominator: ind.den,
    intensity: ind.intensity,
    coverageFraction: fmean / N,
    coverageState: fam,
    unknownCells: ind.unknown,
    excludedDetections: ind.excluded,
    valid: ind.valid,
    satellites: sats,
    productVersion: isM ? modisVersionOf(d.date) : '2',
  }
}

function dominant(states: CoverageState[]): CoverageState {
  const cnt: Record<string, number> = {}
  for (const s of states) cnt[s] = (cnt[s] ?? 0) + 1
  let bestS: CoverageState = 'CORROBORATED'
  let bestN = -1
  for (const s of ORDER) {
    if ((cnt[s] ?? 0) > bestN) {
      bestN = cnt[s] ?? 0
      bestS = s
    }
  }
  return bestS
}

function shiftedK(m: Set<number>, v: Set<number>, comp: Uint8Array): number | null {
  const shifts: [number, number][] = [[1, 0], [-1, 0], [0, 1], [0, -1]]
  const vals: number[] = []
  for (const [di, dj] of shifts) {
    const vs = new Set<number>()
    for (const k of v) {
      const idx = INDEX_BY_IJ.get(`${CELLS[k].i + di}_${CELLS[k].j + dj}`)
      if (idx !== undefined && comp[idx]) vs.add(idx)
    }
    let inter = 0
    for (const k of m) if (vs.has(k)) inter++
    const uni = m.size + vs.size - inter
    if (uni > 0) vals.push(inter / uni)
  }
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
}

function comparison(d: DayInternal, scenario: Scenario): DayRecord['comparison'] {
  const c = compute(d)
  const comp = new Uint8Array(N)
  let nComp = 0
  for (let k = 0; k < N; k++) {
    const mAct = c.modisCount[k] > 0
    const vAct = d.viirs[k] > 0
    const ok =
      scenario === 'A'
        ? c.famState.MODIS[k] === 'CORROBORATED' && c.famState.VIIRS[k] === 'CORROBORATED'
        : (c.famCov.MODIS[k] >= CORROBORATED_AT || mAct) && (c.famCov.VIIRS[k] >= CORROBORATED_AT || vAct)
    if (ok) {
      comp[k] = 1
      nComp++
    }
  }
  const M = new Set<number>()
  const V = new Set<number>()
  for (let k = 0; k < N; k++) {
    if (!comp[k]) continue
    if (c.modisCount[k] > 0) M.add(k)
    if (d.viirs[k] > 0) V.add(k)
  }
  let inter = 0
  for (const k of M) if (V.has(k)) inter++
  const union = M.size + V.size - inter
  const frac = nComp / N
  const ok = frac >= MIN_COMPARABLE_FRACTION
  let reason: ComparisonReason | null = null
  if (!ok) reason = 'INSUFFICIENT_COVERAGE'
  else if (union === 0) reason = 'NO_ACTIVE_CELLS'
  const K = ok && union > 0 ? inter / union : null
  const off = (passHour('Aqua', d.year) - passHour('NOAA-20', d.year)) * 60 + 6 * Math.sin(hashString(d.date) % 97)
  return {
    comparable: ok,
    reason,
    K,
    Knull: K !== null ? shiftedK(M, V, comp) : null,
    both: inter,
    onlyModis: M.size - inter,
    onlyViirs: V.size - inter,
    union,
    comparableCells: nComp,
    modisConfirmedShare: ok && M.size > 0 ? inter / M.size : null,
    passOffsetMin: Math.round(off),
  }
}

export function buildDayRecord(d: DayInternal, scenario: Scenario): Omit<DayRecord, 'referenceModis' | 'referenceViirs' | 'divergence'> {
  const modis = sensorDay(d, 'MODIS', scenario)
  const viirs = sensorDay(d, 'VIIRS', scenario)
  const flags: string[] = []
  if (d.note) flags.push(d.note)
  if (d.flags.aqua.cutFrac !== null && !d.note) flags.push('AQUA_PARTIAL')
  if (d.flags.terra.cutFrac !== null && !d.note) flags.push('TERRA_PARTIAL')
  if (!d.flags.n20.catalogueComplete && !d.note) flags.push('N20_INCOMPLETE')
  if (!d.flags.terra.catalogueComplete && d.flags.terra.conflictRecords === 0) flags.push('TERRA_INCOMPLETE')
  return {
    date: d.date,
    year: d.year,
    month: Number(d.date.slice(5, 7)),
    weekOfYear: weekOfYear(d.date),
    modisBlock: modisBlockOf(d.date),
    modis,
    viirs,
    comparison: comparison(d, scenario),
    flags,
  }
}

// ---- cell level view for one day -----------------------------------------------------------------------------------
export function buildCellDays(d: DayInternal, scenario: Scenario): CellDay[] {
  const c = compute(d)
  const out: CellDay[] = []
  for (let k = 0; k < N; k++) {
    const m = c.modisCount[k]
    const v = d.viirs[k]
    const mc = c.famState.MODIS[k]
    const vc = c.famState.VIIRS[k]
    let category: CellCategory = 'NONE'
    if (m > 0 && v > 0) category = 'BOTH'
    else if (m > 0) category = vc === 'CORROBORATED' ? 'MODIS_ONLY' : 'UNCERTAIN'
    else if (v > 0) category = mc === 'CORROBORATED' ? 'VIIRS_ONLY' : 'UNCERTAIN'
    else if (mc === 'INDETERMINATE' || vc === 'INDETERMINATE') category = 'UNCERTAIN'
    const excluded = scenario === 'A' && (mc !== 'CORROBORATED' || vc !== 'CORROBORATED') && category !== 'NONE'
    out.push({
      cell: CELLS[k],
      category,
      modisCount: m,
      viirsCount: v,
      terra: d.terra[k],
      aqua: d.aqua[k],
      noaa20: v,
      modisCoverage: mc,
      viirsCoverage: vc,
      excludedInA: excluded,
    })
  }
  return out
}

// ---- individual simulated detections for one cell-day --------------------------------------------------------------
export function buildDetections(d: DayInternal, cellIdx: number): DetectionRecord[] {
  const cell = CELLS[cellIdx]
  const rng = rngFor(`mock-det:${d.date}:${cell.id}`)
  const out: DetectionRecord[] = []
  const emit = (sat: SatelliteId, sensor: SensorId, n: number, version: string, key: string) => {
    for (let q = 0; q < n; q++) {
      const night = rng() < 0.14
      const base = passHour(sat, d.year) + (night ? -12 : 0)
      const h = (base + 0.12 * gauss(rng) + 24) % 24
      const lat = cell.lat0 + 0.02 + rng() * (CELL_SIZE - 0.04)
      const lon = cell.lon0 + 0.02 + rng() * (CELL_SIZE - 0.04)
      const confidence = sensor === 'MODIS' ? String(Math.round(35 + 65 * rng())) : rng() < 0.07 ? 'h' : rng() < 0.2 ? 'l' : 'n'
      const hh = String(Math.floor(h)).padStart(2, '0')
      const mm = String(Math.floor((h % 1) * 60)).padStart(2, '0')
      out.push({
        id: `MOCK-${d.date}-${key}-${cell.i}_${cell.j}-${q + 1}`,
        date: d.date,
        cellId: cell.id,
        sensor,
        satellite: sat,
        timeUtc: `${hh}:${mm}`,
        lat: Math.round(lat * 10000) / 10000,
        lon: Math.round(lon * 10000) / 10000,
        frpMw: Math.round(Math.exp(1.2 + 1.0 * gauss(rng)) * 10) / 10,
        confidence,
        pixelKm: sensor === 'MODIS' ? [Math.round((1 + 0.9 * rng()) * 100) / 100, Math.round((1 + 0.5 * rng()) * 100) / 100] : [Math.round((0.375 + 0.15 * rng()) * 1000) / 1000, Math.round((0.375 + 0.1 * rng()) * 1000) / 1000],
        dayNight: night ? 'N' : 'D',
        productVersion: version,
        sourceFile: `MOCK_${key.toUpperCase()}_${d.date.replaceAll('-', '')}_SIMULATED.csv`,
      })
    }
  }
  emit('Terra', 'MODIS', d.terra[cellIdx], modisVersionOf(d.date), 'terra')
  emit('Aqua', 'MODIS', d.aqua[cellIdx], modisVersionOf(d.date), 'aqua')
  emit('NOAA-20', 'VIIRS', d.viirs[cellIdx], '2', 'n20')
  out.sort((a, b) => a.timeUtc.localeCompare(b.timeUtc))
  return out
}

export function refPositionOf(x: number | null, ref: number[], minRef = 2): RefPosition {
  if (x === null) return 'NO_DATA'
  if (ref.length < minRef) return 'INSUFFICIENT'
  if (x > Math.max(...ref)) return 'ABOVE'
  if (x < Math.min(...ref)) return 'BELOW'
  return 'WITHIN'
}

export { N as CELL_COUNT, INDEX_BY_IJ }
export type { Rng }
