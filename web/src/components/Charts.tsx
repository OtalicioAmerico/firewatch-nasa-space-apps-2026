import { useMemo } from 'react'
import type { MonthSeriesPoint, Scenario, SensorId, WeeklyReferencePoint } from '../types'
import { dataSource } from '../services'
import { useI18n } from '../i18n/useI18n'

/** Monthly mean extent of each sensor for one year. Click a month to open it in the calendar. */
export function YearStrip({ series, selectedMonth, onSelect }: { series: MonthSeriesPoint[]; selectedMonth: number; onSelect: (m: number) => void }) {
  const { t, f } = useI18n()
  const maxM = Math.max(0.0001, ...series.map((s) => s.modisExtent ?? 0))
  const maxV = Math.max(0.0001, ...series.map((s) => s.viirsExtent ?? 0))
  return (
    <figure className="chart" style={{ margin: 0 }}>
      <svg viewBox="0 0 360 120" role="img" aria-label={t('charts.yearStrip.aria')} className="yearstrip">
        {series.map((s, i) => {
          const x = i * 30
          const hm = ((s.modisExtent ?? 0) / maxM) * 70
          const hv = ((s.viirsExtent ?? 0) / maxV) * 70
          const sel = s.month === selectedMonth
          return (
            <g
              key={s.month}
              tabIndex={0}
              role="button"
              aria-label={t('charts.yearStrip.open', { month: f.monthLong(s.month) })}
              onClick={() => onSelect(s.month)}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelect(s.month)}
              style={{ cursor: 'pointer' }}
            >
              <rect x={x + 1} y={4} width={28} height={104} rx={6} className={sel ? 'ys-sel' : 'ys-bg'} />
              <rect x={x + 5} y={96 - hm} width={9} height={Math.max(hm, 1)} rx={2} fill="var(--cat-modis)" />
              <rect x={x + 16} y={96 - hv} width={9} height={Math.max(hv, 1)} rx={2} fill="var(--cat-viirs)" />
              <text x={x + 15} y={116} textAnchor="middle" className="ys-t">
                {f.monthShort(s.month)}
              </text>
            </g>
          )
        })}
      </svg>
      <figcaption className="legend" style={{ marginTop: 6 }}>
        <span><i className="dot modis" /> {t('charts.yearStrip.modis')}</span>
        <span><i className="dot viirs" /> {t('charts.yearStrip.viirs')}</span>
        <span className="muted">{t('charts.yearStrip.note')}</span>
      </figcaption>
    </figure>
  )
}

/** Weekly extent of one sensor against the range of the available reference years. Weeks are fixed 7-day blocks, not ISO weeks. */
export function WeeklyReferenceChart({ year, sensor, scenario, highlightWeek }: { year: number; sensor: SensorId; scenario: Scenario; highlightWeek: number }) {
  const { t } = useI18n()
  const pts: WeeklyReferencePoint[] = useMemo(() => dataSource.getWeeklyReference(year, sensor, scenario), [year, sensor, scenario])
  const vals = pts.map((p) => (sensor === 'MODIS' ? p.modis : p.viirs))
  const hi = Math.max(0.0001, ...vals.map((v) => v ?? 0), ...pts.map((p) => p.refMax ?? 0))
  const X = (w: number) => 8 + ((w - 1) / 52) * 344
  const Y = (v: number) => 104 - (v / hi) * 92
  const band = pts.filter((p) => p.refMin !== null && p.refMax !== null)
  const color = sensor === 'MODIS' ? 'var(--cat-modis)' : 'var(--cat-viirs)'
  const path = vals
    .map((v, i) => (v === null ? null : `${i === 0 || vals[i - 1] === null ? 'M' : 'L'}${X(i + 1).toFixed(1)},${Y(v).toFixed(1)}`))
    .filter(Boolean)
    .join(' ')
  const bandPath =
    band.length > 1
      ? `M${band.map((p) => `${X(p.week).toFixed(1)},${Y(p.refMax!).toFixed(1)}`).join(' L')} L${[...band].reverse().map((p) => `${X(p.week).toFixed(1)},${Y(p.refMin!).toFixed(1)}`).join(' L')} Z`
      : ''
  const hv = vals[highlightWeek - 1]
  return (
    <figure className="chart" style={{ margin: 0 }}>
      <svg viewBox="0 0 360 124" role="img" aria-label={t('charts.weekly.aria', { sensor, year })} className="weekly">
        <line x1="8" y1="104" x2="352" y2="104" className="ax" />
        {bandPath ? <path d={bandPath} className="refband" /> : <text x="180" y="60" textAnchor="middle" className="ys-t">{t('charts.weekly.noBand')}</text>}
        <path d={path} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {hv !== null && hv !== undefined && <circle cx={X(highlightWeek)} cy={Y(hv)} r="4.5" fill={color} stroke="var(--color-surface)" strokeWidth="2" />}
        {[1, 14, 27, 40, 53].map((w) => (
          <text key={w} x={X(w)} y="119" textAnchor={w === 1 ? 'start' : w === 53 ? 'end' : 'middle'} className="ys-t">
            {t('charts.weekly.weekShort', { w })}
          </text>
        ))}
      </svg>
      <figcaption className="legend" style={{ marginTop: 4 }}>
        <span><i className="sw" style={{ background: color }} /> {t('charts.weekly.legendSeries', { sensor, year })}</span>
        <span><i className="sw" style={{ background: 'color-mix(in srgb, var(--color-muted) 35%, transparent)' }} /> {t('charts.weekly.legendBand')}</span>
      </figcaption>
    </figure>
  )
}

/** Two horizontal bars: raw count vs extent, each scaled to its own maximum, for the explanation panels. */
export function CountVsExtent({ items }: { items: { label: string; count: number; extent: number; maxCount: number; maxExtent: number; color: string }[] }) {
  const { t, f } = useI18n()
  return (
    <div className="cve" role="img" aria-label={t('charts.cve.aria')}>
      {items.map((it) => (
        <div key={it.label} className="cve-row">
          <span className="cve-l">{it.label}</span>
          <span className="cve-bars">
            <span className="cve-bar"><i style={{ width: `${(it.count / it.maxCount) * 100}%`, background: it.color, opacity: 0.55 }} /><b>{t('charts.cve.detections', { n: f.num(it.count) })}</b></span>
            <span className="cve-bar"><i style={{ width: `${(it.extent / it.maxExtent) * 100}%`, background: it.color }} /><b>{t('charts.cve.extent', { v: f.pct(it.extent, 1) })}</b></span>
          </span>
        </div>
      ))}
    </div>
  )
}
