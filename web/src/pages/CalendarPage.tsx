import { useMemo } from 'react'
import { ChevronLeft, ChevronRight, Info } from 'lucide-react'
import type { MetricId, SensorFilter } from '../types'
import { useApp } from '../state/AppState'
import { dataSource } from '../services'
import { useI18n } from '../i18n/useI18n'
import { DayDetails } from '../components/DayDetails'
import { DataBoundary } from '../components/DataBoundary'
import { MonthCalendar } from '../components/MonthCalendar'
import { YearStrip } from '../components/Charts'
import { Seg, Tip } from '../components/ui'
import { addDays, clampDate } from '../lib/format'
import { METRICS } from '../lib/scale'

export function CalendarPage() {
  const { state } = useApp()
  const year = Number(state.date.slice(0, 4))
  return (
    <DataBoundary needs={[{ kind: 'year', year }]}>
      <CalendarInner />
    </DataBoundary>
  )
}

function CalendarInner() {
  const { state, patch, selectDate } = useApp()
  const { t, f } = useI18n()
  const year = Number(state.date.slice(0, 4))
  const month = Number(state.date.slice(5, 7))
  const day = Number(state.date.slice(8))
  const years = dataSource.getYears()
  const range = dataSource.getRange()
  const series = useMemo(() => dataSource.getYearSeries(year, state.scenario), [year, state.scenario])

  const shiftMonth = (delta: number) => {
    let y = year
    let m = month + delta
    if (m < 1) {
      m = 12
      y--
    }
    if (m > 12) {
      m = 1
      y++
    }
    const next = clampDate(y, m, day)
    if (next >= range.first && next <= range.last) selectDate(next)
  }
  const setMetric = (m: MetricId) => patch({ metric: m, sensor: m === 'concordance' ? 'ALL' : state.sensor })
  const setSensor = (s: SensorFilter) => patch({ sensor: s, metric: s !== 'ALL' && state.metric === 'concordance' ? 'extent' : state.metric })

  return (
    <div className="page-grid cal-page">
      <section className="card cal-card" aria-label={t('calendar.aria')}>
        <div className="toolbar">
          <Seg
            label={t('calendar.year')}
            value={String(year)}
            onChange={(v) => selectDate(clampDate(Number(v), month, day))}
            options={years.map((y) => ({ id: String(y), label: String(y) }))}
          />
          <div className="monthnav">
            <button type="button" className="icon-btn" aria-label={t('calendar.prevMonth')} onClick={() => shiftMonth(-1)} disabled={`${year}-${String(month).padStart(2, '0')}` <= range.first.slice(0, 7)}>
              <ChevronLeft size={18} />
            </button>
            <h2 aria-live="polite">{f.monthYear(year, month)}</h2>
            <button type="button" className="icon-btn" aria-label={t('calendar.nextMonth')} onClick={() => shiftMonth(1)} disabled={`${year}-${String(month).padStart(2, '0')}` >= range.last.slice(0, 7)}>
              <ChevronRight size={18} />
            </button>
          </div>
          <span style={{ flex: 1 }} />
          <Seg
            label={t('calendar.sensorFilter')}
            value={state.sensor}
            onChange={setSensor}
            options={[
              { id: 'MODIS', label: <><i className="dot modis" /> MODIS</> },
              { id: 'VIIRS', label: <><i className="dot viirs" /> VIIRS</> },
              { id: 'ALL', label: t('sensor.compare') },
            ]}
          />
        </div>
        <div className="toolbar sub">
          <Seg compact label={t('calendar.indicator')} value={state.metric} onChange={setMetric} options={METRICS.map((m) => ({ id: m, label: t(`metric.${m}.label`) }))} />
          <Tip label={t('calendar.aboutIndicator')}>{t(`metric.${state.metric}.help`)}</Tip>
          <span className="muted hint">{t(`metric.${state.metric}.help`)}</span>
        </div>
        <MonthCalendar year={year} month={month} scenario={state.scenario} sensor={state.sensor} metric={state.metric} selected={state.date} onSelect={selectDate} />
        <div className="cal-legend" aria-label={t('calendar.legend.aria')}>
          <span><i className="ramp m" /> {t('calendar.legend.modis')}</span>
          <span><i className="ramp v" /> {t('calendar.legend.viirs')}</span>
          <span><i className="ramp b" /> {t('calendar.legend.k')}</span>
          <span><i className="hx p" /> {t('calendar.legend.partial')}</span>
          <span><i className="hx i" /> {t('calendar.legend.indeterminate')}</span>
          <span><i className="hx x" /> {t('calendar.legend.excluded')}</span>
        </div>
        <div className="cal-quick">
          <button type="button" className="btn sm" onClick={() => selectDate(addDays(state.date, -1) >= range.first ? addDays(state.date, -1) : state.date)}>
            <ChevronLeft size={14} /> {t('common.previousDay')}
          </button>
          <button type="button" className="btn sm" onClick={() => selectDate(addDays(state.date, 1) <= range.last ? addDays(state.date, 1) : state.date)}>
            {t('common.nextDay')} <ChevronRight size={14} />
          </button>
          <span className="muted hint">
            <Info size={13} aria-hidden /> {t(`calendar.keysHint.${dataSource.mode}`)}
          </span>
        </div>
        <div>
          <h3 style={{ margin: '4px 0 6px', fontSize: 'var(--text-sm)' }}>{t('calendar.glance', { year })}</h3>
          <YearStrip series={series} selectedMonth={month} onSelect={(m) => selectDate(clampDate(year, m, day))} />
        </div>
      </section>
      <div className="side-col">
        <DayDetails date={state.date} />
      </div>
    </div>
  )
}
