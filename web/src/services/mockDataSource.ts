import type { FireCalendarDataSource } from './dataSource'
import {
  ALL_DATES,
  CELLS,
  REGION,
  YEARS,
  getCellDays,
  getDay,
  getDetections,
  getExamples,
  getMonth,
  getScaleMax,
  getWeeklyReference,
  getYearSeries,
  getYearSummary,
} from '../mock'

/** SIMULATED fixtures. Development and tests only: the interface labels this mode as simulated data. */
export const mockDataSource: FireCalendarDataSource = {
  mode: 'MOCK',
  isSimulated: true,
  init: () => Promise.resolve(),
  ensure: () => Promise.resolve(),
  isReady: () => true,
  getRegion: () => REGION,
  getYears: () => YEARS,
  getCells: () => CELLS,
  getDay,
  getMonth,
  getYearSeries,
  getWeeklyReference,
  getCellDays,
  getDetections,
  getExamples,
  getRange: () => ({ first: ALL_DATES[0], last: ALL_DATES[ALL_DATES.length - 1] }),
  getScaleMax,
  getYearSummary,
  getSources: () => [],
}
