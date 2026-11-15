/**
 * Domain types of the NASA Fire Calendar front end.
 * Two implementations of `FireCalendarDataSource` (../services/dataSource.ts) fill these types: the SIMULATED fixtures (../mock,
 * development and tests only) and the REAL Mission 05 results exported by tools/export_web (../services/realDataSource.ts).
 * Texts are never stored here: codes only; the interface translates them (../i18n).
 */

export type DataMode = 'MOCK' | 'REAL'

export type SensorId = 'MODIS' | 'VIIRS'
export type SatelliteId = 'Terra' | 'Aqua' | 'NOAA-20'
/** A = conservative (only corroborated coverage), B = exploratory (all observations, uncertainty flagged). */
export type Scenario = 'A' | 'B'
/** 'ALL' = compare both sensors side by side. */
export type SensorFilter = 'ALL' | SensorId

/** Coverage dimension. Independent from the detection dimension (a cell can have detections and partial coverage). */
export type CoverageState =
  | 'CORROBORATED' // geometric coverage >= 95 % of the cell, catalogue complete, no conflict
  | 'PARTIAL' // 0 < coverage < 95 %
  | 'INDETERMINATE' // catalogue incomplete or FIRMS x CMR conflict: coverage cannot be asserted
  | 'NO_COVERAGE_CORROBORATED' // catalogue complete and no granule covers the cell (this is NOT "no fire")

export type CellCategory = 'BOTH' | 'MODIS_ONLY' | 'VIIRS_ONLY' | 'UNCERTAIN' | 'NONE'
export type RefPosition = 'ABOVE' | 'WITHIN' | 'BELOW' | 'INSUFFICIENT' | 'NO_DATA'
export type ModisBlock = 'A' | 'B'
export type MetricId = 'extent' | 'intensity' | 'detections' | 'concordance'

export interface Region {
  id: string
  name: string
  country: string
  /** west, south, east, north */
  bbox: [number, number, number, number]
  cellSizeDeg: number
}

export interface Cell {
  id: string
  i: number
  j: number
  lat0: number
  lon0: number
  lat1: number
  lon1: number
  /** the centre of the cell lies outside the state outline: part of the cell is outside the territory */
  boundary?: boolean
}

export interface SatelliteDay {
  satellite: SatelliteId
  detections: number
  passUtc: string | null // median UTC time of the detections of the satellite-day, "HH:MM"; null when there are none
  coverageState: CoverageState
  coverageFraction: number // mean geometric coverage over the region, 0..1
  catalogueComplete: boolean
  conflictRecords: number // FIRMS records without a matching granule
  productVersion: string | null // observed product version; null when the satellite had no detection that day
}

export interface SensorDay {
  sensor: SensorId
  detections: number // raw detections of the sensor (never summed with the other sensor)
  activeCells: number | null
  /** active cells / coverage denominator; null when the day is excluded in scenario A */
  extent: number | null
  /** numerator and denominator of the extent, both exposed */
  extentNumerator: number | null
  extentDenominator: number | null
  intensity: number | null // detections per active cell
  coverageFraction: number
  coverageState: CoverageState
  unknownCells: number // cells with indeterminate coverage and no detection
  excludedDetections: number // detections left out by scenario A
  valid: boolean
  satellites: SatelliteDay[]
  productVersion: string | null
}

export type ComparisonReason = 'INSUFFICIENT_COVERAGE' | 'NO_ACTIVE_CELLS'

export interface Comparison {
  comparable: boolean
  reason: ComparisonReason | null
  K: number | null // spatial agreement (Jaccard) over comparable cells; null = not applicable
  Knull: number | null
  both: number
  onlyModis: number
  onlyViirs: number
  union: number
  comparableCells: number
  modisConfirmedShare: number | null
  passOffsetMin: number | null // Aqua minus NOAA-20 median detection time offset, minutes
}

export type RefBasis = 'BLOCK_A' | 'BLOCK_B' | 'OTHER_YEARS' | 'NONE'

export interface ReferenceInfo {
  position: RefPosition
  nReferenceYears: number
  basis: RefBasis
}

/** Reading of a raw count versus the extent (mock storytelling only; the real source does not derive daily divergences). */
export interface Divergence {
  sensor: SensorId
  kind: 'COUNT_HIGHER_THAN_EXTENT' | 'EXTENT_HIGHER_THAN_COUNT'
}

export interface DayRecord {
  date: string // YYYY-MM-DD (UTC day)
  year: number
  month: number
  weekOfYear: number
  modisBlock: ModisBlock
  modis: SensorDay
  viirs: SensorDay
  comparison: Comparison
  referenceModis: ReferenceInfo
  referenceViirs: ReferenceInfo
  /** day-level notes as codes (AQUA_PARTIAL, TERRA_CONFLICT, ...); translated by the interface */
  flags: string[]
  divergence: Divergence | null
}

export interface CellDay {
  cell: Cell
  category: CellCategory
  modisCount: number
  viirsCount: number
  terra: number
  aqua: number
  noaa20: number
  modisCoverage: CoverageState
  viirsCoverage: CoverageState
  /** coverage of the cell by satellite (REAL source); the mock falls back to the day-level state */
  satCoverage?: Partial<Record<SatelliteId, { state: CoverageState; fraction: number }>>
  /** excluded from the indicators in scenario A */
  excludedInA: boolean
}

export interface DetectionRecord {
  id: string
  date: string
  cellId: string
  sensor: SensorId
  satellite: SatelliteId
  timeUtc: string
  lat: number
  lon: number
  frpMw: number | null
  confidence: string | null
  pixelKm: [number, number] | null
  dayNight: 'D' | 'N' | null
  productVersion: string | null
  sourceFile: string
  /** REAL source only: SHA-256 of the imported FIRMS response file and the line of the record in it */
  sourceSha256?: string
  sourceLine?: number | null
}

/** Weekly facts of a documented example (REAL source): 7-day blocks of the processing, NOT ISO weeks. */
export interface WeeklyFacts {
  year: number
  week: number
  sensor: SensorId
  detections: number
  detectionsPosition: RefPosition
  detectionsRef: [number, number] | null
  extent: number | null
  extentPosition: RefPosition
  extentRef: [number, number] | null
  nReferenceYears: number
}

/** Texts live in the dictionaries under `examples.<id>.*`; the story carries only ids, dates and facts. */
export interface ExampleStory {
  id: string
  date: string
  /** second day of a pair (mock "same count" example) */
  relatedDate?: string
  metric: MetricId
  sensor: SensorFilter
  /** shown as a card on the Overview */
  featured?: boolean
  weekly?: WeeklyFacts
}

export interface ScaleMax {
  extent: Record<SensorId, number>
  intensity: Record<SensorId, number>
  detections: Record<SensorId, number>
}

export interface SensorYearSummary {
  detections: number
  medianExtent: number | null
  medianIntensity: number | null
  uncertainDays: number
  excludedDays: number
}

export interface YearSummary {
  days: number
  MODIS: SensorYearSummary
  VIIRS: SensorYearSummary
  comparableDays: number
  medianK: number | null
  kDays: number
}

export interface SourceFile {
  sha256: string
  file: string
  product: string
}

export interface MonthSeriesPoint {
  month: number
  modisExtent: number | null
  viirsExtent: number | null
  modisDetections: number
  viirsDetections: number
}

export interface WeeklyReferencePoint {
  week: number
  modis: number | null
  viirs: number | null
  refMin: number | null
  refMax: number | null
}
