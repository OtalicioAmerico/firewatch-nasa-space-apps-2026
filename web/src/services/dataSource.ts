/**
 * Data access layer. Components and pages only talk to this interface.
 * Two implementations exist and are NEVER mixed: `mockDataSource` (simulated fixtures, development and tests only) and
 * `realDataSource` (Mission 05 results exported by tools/export_web). `services/index.ts` is the only place that chooses.
 *
 * Getters are synchronous. Data that is not bundled is fetched on demand: call `ensure()` first (the UI does it through
 * <DataBoundary>); a getter whose data has not been loaded throws instead of inventing a value.
 */
import type {
  Cell,
  CellDay,
  DataMode,
  DayRecord,
  DetectionRecord,
  ExampleStory,
  MonthSeriesPoint,
  Region,
  ScaleMax,
  Scenario,
  SensorId,
  SourceFile,
  WeeklyReferencePoint,
  YearSummary,
} from '../types'

export type Need = { kind: 'year'; year: number } | { kind: 'cells'; date: string } | { kind: 'detections'; date: string }

export interface FireCalendarDataSource {
  readonly mode: DataMode
  /** true only for MOCK data */
  readonly isSimulated: boolean
  /** load the small index (universe, summaries); rejects when the real files are not available */
  init(): Promise<void>
  ensure(need: Need): Promise<void>
  isReady(need: Need): boolean
  getRegion(): Region
  getYears(): number[]
  /** universe of cells of the source (REAL: 433 experimental cells of Mission 05) */
  getCells(): Cell[]
  getDay(date: string, scenario: Scenario): DayRecord
  getMonth(year: number, month: number, scenario: Scenario): DayRecord[]
  getYearSeries(year: number, scenario: Scenario): MonthSeriesPoint[]
  getWeeklyReference(year: number, sensor: SensorId, scenario: Scenario): WeeklyReferencePoint[]
  getCellDays(date: string, scenario: Scenario): CellDay[]
  getDetections(date: string, cellId: string): DetectionRecord[]
  getExamples(): ExampleStory[]
  /** first and last day with data */
  getRange(): { first: string; last: string }
  getScaleMax(scenario: Scenario): ScaleMax
  getYearSummary(year: number, scenario: Scenario): YearSummary
  /** REAL: imported FIRMS response files (verifiable by SHA-256); MOCK: empty */
  getSources(): SourceFile[]
}
