import { useMemo } from 'react'
import { ArrowRight, BookOpen, CalendarDays, Map as MapIcon, Sparkles } from 'lucide-react'
import type { ExampleStory, SensorId, YearSummary } from '../types'
import { useApp } from '../state/AppState'
import { dataSource } from '../services'
import { useI18n } from '../i18n/useI18n'
import { T } from '../i18n/Rich'
import { DataBoundary } from '../components/DataBoundary'
import { MapView } from '../components/MapView'
import { MonthCalendar } from '../components/MonthCalendar'
import { CountVsExtent, YearStrip } from '../components/Charts'
import { Badge, Callout, Legend, Seg, SensorTag, Stat, Tip } from '../components/ui'
import { clampDate } from '../lib/format'

type Sum = YearSummary['MODIS']

function SensorKpi({ sensor, s, days, year }: { sensor: SensorId; s: Sum; days: number; year: number }) {
  const { t, f } = useI18n()
  return (
    <section className={`card kpi ${sensor === 'MODIS' ? 'modis' : 'viirs'}`}>
      <header>
        <SensorTag sensor={sensor} />
        <span className="muted" style={{ fontSize: 'var(--text-xs)' }}>{t(sensor === 'MODIS' ? 'overview.kpi.modisSat' : 'overview.kpi.viirsSat')}</span>
      </header>
      <div className="stat-grid">
        <Stat label={t('overview.kpi.extent')} tip={t('overview.kpi.extentTip')} value={f.pct(s.medianExtent)} sub={t('overview.kpi.extentSub', { year })} />
        <Stat label={t('metric.intensity.label')} tip={t('overview.kpi.intensityTip')} value={s.medianIntensity === null ? '—' : f.dec(s.medianIntensity, 1)} sub={t('overview.kpi.intensitySub')} />
        <Stat label={t('metric.detections.label')} tip={t('overview.kpi.detectionsTip')} value={f.num(s.detections)} sub={t('overview.kpi.detectionsSub', { year })} />
      </div>
      <p className="note">
        {t('overview.kpi.uncertain', { a: f.num(s.uncertainDays), b: f.num(days) })}
        {s.excludedDays ? ` · ${t('overview.kpi.excluded', { n: f.num(s.excludedDays) })}` : ''}.
      </p>
    </section>
  )
}

/** Weekly facts of a documented real example: count and extent are read against the available reference, never merged. */
function ExampleFacts({ e }: { e: ExampleStory }) {
  const { t, f } = useI18n()
  const w = e.weekly
  if (!w) return null
  const tone = (p: string) => (p === 'ABOVE' ? 'amber' : p === 'BELOW' ? 'violet' : p === 'WITHIN' ? 'green' : 'neutral')
  const range = (r: [number, number] | null, pct: boolean) => (r ? ` (${pct ? f.pct(r[0]) : f.num(r[0])}–${pct ? f.pct(r[1]) : f.num(r[1])})` : '')
  return (
    <ul className="facts" aria-label={t('overview.facts.aria', { sensor: w.sensor, week: w.week, year: w.year })}>
      <li>
        <span>{t('metric.detections.label')}: <b>{f.num(w.detections)}</b>{range(w.detectionsRef, false)}</span>
        <Badge tone={tone(w.detectionsPosition)}>{t(`ref.${w.detectionsPosition}.short`)}</Badge>
      </li>
      <li>
        <span>{t('metric.extent.label')}: <b>{f.pct(w.extent)}</b>{range(w.extentRef, true)}</span>
        <Badge tone={tone(w.extentPosition)}>{t(`ref.${w.extentPosition}.short`)}</Badge>
      </li>
    </ul>
  )
}

export function OverviewPage() {
  const { state } = useApp()
  const year = Number(state.date.slice(0, 4))
  return (
    <DataBoundary needs={[{ kind: 'year', year }, { kind: 'cells', date: state.date }]}>
      <OverviewInner />
    </DataBoundary>
  )
}

function OverviewInner() {
  const { state, go, patch, selectDate } = useApp()
  const { t, f } = useI18n()
  const year = Number(state.date.slice(0, 4))
  const month = Number(state.date.slice(5, 7))
  const years = dataSource.getYears()
  const sum = useMemo(() => dataSource.getYearSummary(year, state.scenario), [year, state.scenario])
  const series = useMemo(() => dataSource.getYearSeries(year, state.scenario), [year, state.scenario])
  const examples = useMemo(() => dataSource.getExamples(), [])
  const featured = examples.filter((e) => e.featured)
  const pair = examples.find((e) => e.id === 'count-vs-extent' && e.relatedDate)
  const pairDays = useMemo(() => {
    if (!pair || !pair.relatedDate || !dataSource.isReady({ kind: 'year', year: Number(pair.date.slice(0, 4)) })) return null
    const a = dataSource.getDay(pair.date, state.scenario)
    const b = dataSource.getDay(pair.relatedDate, state.scenario)
    const maxC = Math.max(a.modis.detections, b.modis.detections)
    const maxE = Math.max(a.modis.extent ?? 0, b.modis.extent ?? 0)
    return [a, b].map((d) => ({ label: f.date(d.date), count: d.modis.detections, extent: d.modis.extent ?? 0, maxCount: maxC, maxExtent: maxE || 1, color: 'var(--cat-modis)' }))
  }, [pair, state.scenario, f])
  const day = useMemo(() => dataSource.getDay(state.date, state.scenario), [state.date, state.scenario])

  const open = (e: ExampleStory) => go('calendar', { date: e.date, metric: e.metric, sensor: e.sensor, selectedCellId: null })
  const exParams = (e: ExampleStory) => ({ a: f.date(e.date), b: e.relatedDate ? f.date(e.relatedDate) : '', week: e.weekly?.week ?? '', year: e.weekly?.year ?? '' })

  return (
    <>
      <section className="hero" aria-labelledby="hero-h">
        <div className="hero-copy">
          <span className="eyebrow">{t('overview.hero.eyebrow')}</span>
          <h2 id="hero-h">{t('overview.hero.title')}</h2>
          <p>{t('overview.hero.body')}</p>
          <div className="hero-actions">
            <button type="button" className="btn accent" onClick={() => go('calendar')}>
              <CalendarDays size={16} /> {t('overview.hero.explore')} <ArrowRight size={14} />
            </button>
            <button type="button" className="btn ghost light" onClick={() => go('spatial')}>
              <MapIcon size={16} /> {t('overview.hero.map')}
            </button>
            <button type="button" className="btn ghost light" onClick={() => go('methodology')}>
              <BookOpen size={16} /> {t('overview.hero.method')}
            </button>
          </div>
          <div className="hero-meta">
            <span className="chip">{t('overview.chip.region')}</span>
            <span className="chip">2021 – 2025</span>
            <span className="chip">{t('overview.chip.cells')}</span>
            <span className="chip">{t(`overview.chip.products.${dataSource.mode}`)}</span>
          </div>
        </div>
        <div className="hero-card" aria-label={t('overview.card.aria')}>
          <div className="muted" style={{ fontSize: 'var(--text-xs)', fontWeight: 600 }}>{t('calendar.year')}</div>
          <Seg label={t('calendar.year')} value={String(year)} onChange={(v) => selectDate(clampDate(Number(v), month, Number(state.date.slice(8))))} options={years.map((y) => ({ id: String(y), label: String(y) }))} />
          <div className="muted" style={{ fontSize: 'var(--text-xs)', fontWeight: 600, marginTop: 10 }}>{t('overview.card.region')}</div>
          <div className="hero-region"><b>Tocantins</b><span>{t('overview.card.regionSub')}</span></div>
          <div className="callout" style={{ marginTop: 10 }}>
            <Sparkles size={16} aria-hidden />
            <span><T k={`overview.card.notice.${dataSource.mode}`} /></span>
          </div>
        </div>
      </section>

      <div className="kpi-row">
        <SensorKpi sensor="MODIS" s={sum.MODIS} days={sum.days} year={year} />
        <SensorKpi sensor="VIIRS" s={sum.VIIRS} days={sum.days} year={year} />
        <section className="card kpi">
          <header>
            <Badge tone="both">{t('overview.cmp.title')}</Badge>
            <Tip>{t('overview.cmp.tip')}</Tip>
          </header>
          <div className="stat-grid">
            <Stat label={t('overview.cmp.days')} value={f.pct(sum.comparableDays / sum.days, 0)} sub={t('overview.cmp.daysSub', { a: f.num(sum.comparableDays), b: f.num(sum.days) })} />
            <Stat label={t('overview.cmp.k')} value={sum.medianK === null ? t('common.na') : f.dec(sum.medianK, 2)} sub={t('overview.cmp.kSub', { n: f.num(sum.kDays) })} tip={t('overview.cmp.kTip')} />
            <Stat label={t('scenario.label')} value={state.scenario} sub={t(`scenario.${state.scenario}.short`)} />
          </div>
          <p className="note">{t('overview.cmp.note')}</p>
        </section>
      </div>

      <div className="ov-main">
        <section className="card map-card" aria-label={t('overview.map.aria')}>
          <header>
            <div>
              <h2>{t('overview.map.title')}</h2>
              <p className="sub">{t(`overview.map.sub.${dataSource.mode}`, { date: f.dateLong(state.date) })}</p>
            </div>
            <button type="button" className="btn sm primary" onClick={() => go('spatial')}>
              <MapIcon size={14} /> {t('overview.map.open')}
            </button>
          </header>
          <div className="map-frame">
            <MapView date={state.date} sensor="ALL" scenario={state.scenario} selectedCellId={state.selectedCellId} onSelectCell={(id) => { patch({ selectedCellId: id }); if (id) go('spatial', { selectedCellId: id }) }} showCells showPoints={false} showMunicipalities compact />
            <span className="map-chip"><b>{t(`overview.map.chip.${dataSource.mode}`)}</b></span>
          </div>
          <Legend />
          <p className="note">
            {t('overview.map.note')} <b>{day.comparison.K === null ? t('common.na') : f.dec(day.comparison.K, 2)}</b>
            {day.comparison.K === null ? ` (${day.comparison.reason ? t(`comparison.reason.${day.comparison.reason}`) : t('common.notApplicable')})` : ''}.
          </p>
        </section>
        <section className="card" aria-label={t('overview.cal.aria')}>
          <header>
            <div>
              <h2>{f.monthYear(year, month)}</h2>
              <p className="sub">{t('overview.cal.sub')}</p>
            </div>
            <button type="button" className="btn sm primary" onClick={() => go('calendar', { sensor: 'ALL', metric: 'extent' })}>
              <CalendarDays size={14} /> {t('overview.cal.full')}
            </button>
          </header>
          <MonthCalendar year={year} month={month} scenario={state.scenario} sensor="ALL" metric="extent" selected={state.date} onSelect={(d) => selectDate(d)} />
          <YearStrip series={series} selectedMonth={month} onSelect={(m) => selectDate(`${year}-${String(m).padStart(2, '0')}-15`)} />
        </section>
      </div>

      <section className="card dont" aria-labelledby="dont-h">
        <header>
          <div>
            <h2 id="dont-h">{t('overview.dont.title')}</h2>
            <p className="sub">{t(`overview.dont.sub.${dataSource.mode}`)}</p>
          </div>
        </header>
        <div className="dont-grid">
          {featured.map((e, i) => (
            <article key={e.id}>
              <h3>{i + 1} · {t(`examples.${dataSource.mode}.${e.id}.title`)}</h3>
              <p>{t(`examples.${dataSource.mode}.${e.id}.summary`, exParams(e))}</p>
              {e.id === 'count-vs-extent' && pairDays && <CountVsExtent items={pairDays} />}
              <ExampleFacts e={e} />
              <p className="lesson">{t(`examples.${dataSource.mode}.${e.id}.lesson`)}</p>
              <button type="button" className="btn sm" onClick={() => open(e)}>
                {t('overview.dont.show')} <ArrowRight size={13} />
              </button>
            </article>
          ))}
        </div>
        <Callout tone="info" title={t('overview.dont.never.title')}>
          {t('overview.dont.never.body')}
        </Callout>
      </section>
    </>
  )
}
