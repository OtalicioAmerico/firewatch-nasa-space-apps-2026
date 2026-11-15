import { useMemo, useRef, type CSSProperties, type KeyboardEvent, type ReactNode } from 'react'
import { AlertTriangle, CircleHelp } from 'lucide-react'
import type { CoverageState, DayRecord, MetricId, Scenario, SensorFilter, SensorId } from '../types'
import { dataSource } from '../services'
import { formatValue, level, maxes, valueOf } from '../lib/scale'
import { useI18n } from '../i18n/useI18n'
import type { TFn } from '../i18n'
import type { Formatters } from '../i18n/format'

const WORST: CoverageState[] = ['INDETERMINATE', 'PARTIAL', 'NO_COVERAGE_CORROBORATED', 'CORROBORATED']

function worst(states: CoverageState[]): CoverageState {
  for (const s of WORST) if (states.includes(s)) return s
  return 'CORROBORATED'
}

interface Props {
  year: number
  month: number
  scenario: Scenario
  sensor: SensorFilter
  metric: Exclude<MetricId, never>
  selected: string
  onSelect: (date: string) => void
}

function describe(d: DayRecord, sensor: SensorFilter, metric: MetricId, t: TFn, f: Formatters): string {
  const parts = [f.dateLong(d.date)]
  if (metric === 'concordance') {
    parts.push(d.comparison.K === null ? t('calendar.cell.kNa', { reason: d.comparison.reason ? t(`comparison.reason.${d.comparison.reason}`) : t('common.na') }) : `K ${f.dec(d.comparison.K, 2)}`)
  } else {
    if (sensor !== 'VIIRS') parts.push(`MODIS ${formatValue(valueOf(d, 'MODIS', metric), metric, f)}`)
    if (sensor !== 'MODIS') parts.push(`VIIRS ${formatValue(valueOf(d, 'VIIRS', metric), metric, f)}`)
  }
  const cov = covOf(d, sensor)
  if (cov !== 'CORROBORATED') parts.push(t(`calendar.cell.cov.${cov}`))
  return parts.join(', ')
}

function covOf(d: DayRecord, sensor: SensorFilter): CoverageState {
  if (sensor === 'MODIS') return d.modis.coverageState
  if (sensor === 'VIIRS') return d.viirs.coverageState
  return worst([d.modis.coverageState, d.viirs.coverageState])
}

export function MonthCalendar({ year, month, scenario, sensor, metric, selected, onSelect }: Props) {
  const { t, f } = useI18n()
  const days = useMemo(() => dataSource.getMonth(year, month, scenario), [year, month, scenario])
  const mx = useMemo(() => maxes(scenario), [scenario])
  const offset = (new Date(Date.UTC(year, month - 1, 1)).getUTCDay() + 6) % 7
  const refs = useRef<Record<string, HTMLButtonElement | null>>({})

  const move = (date: string, delta: number) => {
    const idx = days.findIndex((d) => d.date === date) + delta
    const target = days[Math.max(0, Math.min(days.length - 1, idx))]
    onSelect(target.date)
    queueMicrotask(() => refs.current[target.date]?.focus())
  }
  const onKey = (e: KeyboardEvent, date: string) => {
    const step: Record<string, number> = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: 7, ArrowUp: -7 }
    const delta = step[e.key]
    if (delta !== undefined) {
      e.preventDefault()
      move(date, delta)
    }
  }

  return (
    <div className="cal" role="group" aria-label={t(`calendar.groupAria.${dataSource.mode}`, { month: f.monthYear(year, month) })}>
      <div className="cal-head" aria-hidden>
        {Array.from({ length: 7 }, (_, i) => (
          <span key={i}>{f.weekdayShort(i)}</span>
        ))}
      </div>
      <div className="cal-body">
        {Array.from({ length: offset }, (_, i) => (
          <span key={`b${i}`} className="cal-blank" />
        ))}
        {days.map((d) => {
          const cov = covOf(d, sensor)
          const invalidA = scenario === 'A' && ((sensor !== 'VIIRS' && !d.modis.valid) || (sensor !== 'MODIS' && !d.viirs.valid))
          const sel = d.date === selected
          const style: CSSProperties = {}
          let content: ReactNode
          if (metric === 'concordance') {
            const K = d.comparison.K
            const lv = K === null ? 0 : Math.min(1, K / 0.6)
            if (K !== null) style.background = `color-mix(in srgb, var(--cat-both) ${Math.round(14 + lv * 66)}%, var(--color-surface))`
            content = <span className="val">{K === null ? t('common.na') : f.dec(K, 2)}</span>
          } else {
            const m = metric
            const vm = valueOf(d, 'MODIS', m)
            const vv = valueOf(d, 'VIIRS', m)
            if (sensor === 'ALL') {
              const hm = Math.round(level(vm, mx[m].MODIS) * 100)
              const hv = Math.round(level(vv, mx[m].VIIRS) * 100)
              content = (
                <>
                  <span className="bars" aria-hidden>
                    <i className="b m" style={{ height: `${Math.max(hm, vm ? 6 : 0)}%` }} />
                    <i className="b v" style={{ height: `${Math.max(hv, vv ? 6 : 0)}%` }} />
                  </span>
                  <span className="val two">
                    <b className="m">{formatValue(vm, m, f)}</b>
                    <b className="v">{formatValue(vv, m, f)}</b>
                  </span>
                </>
              )
            } else {
              const s: SensorId = sensor
              const v = s === 'MODIS' ? vm : vv
              const lv = level(v, mx[m][s])
              const col = s === 'MODIS' ? 'var(--cat-modis)' : 'var(--cat-viirs)'
              style.background = v === null ? undefined : `color-mix(in srgb, ${col} ${Math.round(8 + lv * 72)}%, var(--color-surface))`
              content = <span className="val">{formatValue(v, m, f)}</span>
            }
          }
          const cls = ['day', sel ? 'sel' : '', cov === 'PARTIAL' ? 'cov-partial' : '', cov === 'INDETERMINATE' ? 'cov-ind' : '', invalidA ? 'excl' : '', d.comparison.comparable ? '' : 'nocomp']
            .filter(Boolean)
            .join(' ')
          return (
            <button
              key={d.date}
              ref={(el) => {
                refs.current[d.date] = el
              }}
              type="button"
              className={cls}
              style={style}
              aria-pressed={sel}
              aria-label={describe(d, sensor, metric, t, f)}
              tabIndex={sel ? 0 : -1}
              onClick={() => onSelect(d.date)}
              onKeyDown={(e) => onKey(e, d.date)}
            >
              <span className="dn">{Number(d.date.slice(8))}</span>
              <span className="flags" aria-hidden>
                {cov === 'INDETERMINATE' && <CircleHelp size={12} />}
                {(cov === 'PARTIAL' || d.flags.length > 0) && cov !== 'INDETERMINATE' && <AlertTriangle size={11} />}
              </span>
              {content}
            </button>
          )
        })}
      </div>
    </div>
  )
}
