import type { DayRecord, MetricId, Scenario, ScaleMax, SensorId } from '../types'
import { dataSource } from '../services'
import type { Formatters } from '../i18n/format'

/** Global maxima of the series (supplied by the data source), so colours are comparable between months and years. */
export function maxes(scenario: Scenario): ScaleMax {
  return dataSource.getScaleMax(scenario)
}

export function valueOf(d: DayRecord, sensor: SensorId, metric: Exclude<MetricId, 'concordance'>): number | null {
  const sd = sensor === 'MODIS' ? d.modis : d.viirs
  if (metric === 'extent') return sd.extent
  if (metric === 'intensity') return sd.intensity
  return sd.detections
}

/** 0..1 level with a square-root stretch for readability (never used as a scientific transformation). */
export function level(v: number | null, max: number): number {
  if (v === null || max <= 0) return 0
  return Math.min(1, Math.sqrt(v / max))
}

export function formatValue(v: number | null, metric: Exclude<MetricId, 'concordance'>, f: Formatters): string {
  if (v === null) return '—'
  if (metric === 'extent') return f.pct(v, 1)
  if (metric === 'intensity') return f.dec(v, 1)
  return f.num(Math.round(v))
}

export const METRICS: MetricId[] = ['extent', 'intensity', 'detections', 'concordance']
