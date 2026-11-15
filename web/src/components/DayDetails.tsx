import { useMemo } from 'react'
import { ArrowRight, GitCompareArrows, MapPinned, TriangleAlert } from 'lucide-react'
import type { DayRecord, SensorDay, SensorId } from '../types'
import { dataSource } from '../services'
import { useApp } from '../state/AppState'
import { useI18n } from '../i18n/useI18n'
import { Badge, Callout, CoverageBadge, SensorTag, Stat, Tip } from './ui'
import { WeeklyReferenceChart } from './Charts'

function SensorCard({ sd, block }: { sd: SensorDay; block?: string }) {
  const { t, f } = useI18n()
  const isM = sd.sensor === 'MODIS'
  const version = sd.productVersion ?? '—'
  return (
    <section className={`card sensor-card ${isM ? 'modis' : 'viirs'}`} aria-label={t('day.sensorAria', { sensor: sd.sensor })}>
      <header>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <SensorTag sensor={sd.sensor} />
          <CoverageBadge state={sd.coverageState} />
        </div>
        <span className="muted mono" style={{ fontSize: 'var(--text-xs)' }}>
          {isM ? t('day.versionBlock', { version, years: block === 'A' ? '2021–22' : '2023–25' }) : t('day.version', { version })}
        </span>
      </header>
      {!sd.valid ? (
        <Callout title={t('day.excludedA.title')}>{t('day.excludedA.body', { n: f.num(sd.detections) })}</Callout>
      ) : (
        <div className="stat-grid">
          <Stat
            label={t('metric.extent.label')}
            tip={t('day.extentTip')}
            value={f.pct(sd.extent)}
            sub={sd.extentNumerator === null ? '' : t('day.cellsOf', { a: f.num(sd.extentNumerator), b: f.num(sd.extentDenominator === null ? null : Math.round(sd.extentDenominator)) })}
          />
          <Stat label={t('metric.intensity.label')} tip={t('day.intensityTip')} value={sd.intensity === null ? '—' : f.dec(sd.intensity, 1)} sub={t('day.perActiveCell')} />
          <Stat
            label={t('metric.detections.label')}
            tip={t('day.detectionsTip')}
            value={f.num(sd.detections)}
            sub={sd.excludedDetections > 0 ? t('day.excludedByA', { n: f.num(sd.excludedDetections) }) : t('day.thisSensorOnly')}
          />
        </div>
      )}
      <table className="table" aria-label={t('day.satellitesAria', { sensor: sd.sensor })}>
        <tbody>
          {sd.satellites.map((s) => (
            <tr key={s.satellite}>
              <td>{s.satellite}</td>
              <td className="num">{t('common.detShort', { n: f.num(s.detections) })}</td>
              <td className="num muted">{s.passUtc ? `${s.passUtc} UTC` : '—'}</td>
              <td className="num muted">{t('day.covered', { v: f.pct(s.coverageFraction, 0) })}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">{t('day.coverageNote')}</p>
      {sd.unknownCells > 0 && (
        <p className="note">
          <TriangleAlert size={14} aria-hidden /> {t('day.unknownCells', { count: sd.unknownCells, n: f.num(sd.unknownCells) })}
        </p>
      )}
    </section>
  )
}

function Reference({ d, sensor }: { d: DayRecord; sensor: SensorId }) {
  const { state } = useApp()
  const { t } = useI18n()
  const ref = sensor === 'MODIS' ? d.referenceModis : d.referenceViirs
  const tone = ref.position === 'ABOVE' ? 'amber' : ref.position === 'BELOW' ? 'violet' : ref.position === 'WITHIN' ? 'green' : 'neutral'
  return (
    <div style={{ display: 'grid', gap: 6 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <SensorTag sensor={sensor} />
        <Badge tone={tone}>{t(`ref.${ref.position}.short`)}</Badge>
        <span className="muted" style={{ fontSize: 'var(--text-xs)' }}>
          {t('day.refYears', { count: ref.nReferenceYears, n: ref.nReferenceYears })} · {t('day.week', { w: d.weekOfYear })}
        </span>
      </div>
      <p className="sub" style={{ margin: 0 }}>
        {t(`ref.${ref.position}.label`)}. <span className="muted">{t(`ref.basis.${ref.basis}`)}</span>
      </p>
      <WeeklyReferenceChart year={d.year} sensor={sensor} scenario={state.scenario} highlightWeek={d.weekOfYear} />
    </div>
  )
}

export function DayDetails({ date, showMapLink = true }: { date: string; showMapLink?: boolean }) {
  const { state, go } = useApp()
  const { t, f } = useI18n()
  const d = useMemo(() => dataSource.getDay(date, state.scenario), [date, state.scenario])
  const c = d.comparison
  return (
    <div className="daydet">
      <div className="daydet-head">
        <div>
          <span className="eyebrow">{t(`day.selected.${dataSource.mode}`)}</span>
          <h2>{f.dateLong(d.date)}</h2>
        </div>
        {showMapLink && (
          <button type="button" className="btn primary" onClick={() => go('spatial', { date: d.date })}>
            <MapPinned size={16} /> {t('day.openOnMap')} <ArrowRight size={14} />
          </button>
        )}
      </div>
      {d.flags.length > 0 && (
        <div className="flags-row" role="list" aria-label={t('day.notesAria')}>
          {d.flags.map((flag) => (
            <span role="listitem" key={flag} className="badge amber">
              <TriangleAlert size={12} aria-hidden /> {t(`flags.${flag}`)}
            </span>
          ))}
        </div>
      )}
      {d.divergence && (
        <Callout tone="info" title={t('day.divergence.title')}>
          {t(`day.divergence.${d.divergence.kind}`, { sensor: d.divergence.sensor })}
        </Callout>
      )}
      <div className="sensor-grid">
        {state.sensor !== 'VIIRS' && <SensorCard sd={d.modis} block={d.modisBlock} />}
        {state.sensor !== 'MODIS' && <SensorCard sd={d.viirs} />}
      </div>
      {state.sensor === 'ALL' && (
        <section className="card" aria-label={t('day.comparisonAria')}>
          <header>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <GitCompareArrows size={16} aria-hidden /> {t('day.agreement.title')}
              <Tip>{t('day.agreement.tip')}</Tip>
            </h3>
            <Badge tone={c.comparable ? 'green' : 'magenta'}>{c.comparable ? t('common.comparable') : t('common.notComparable')}</Badge>
          </header>
          {c.K === null ? (
            <Callout title={t('day.kNa.title')}>
              {c.reason ? t(`comparison.reason.${c.reason}`) : t('day.kNa.notComputed')} {t('day.kNa.body')}
            </Callout>
          ) : (
            <>
              <div className="stat-grid">
                <Stat label="K" value={f.dec(c.K, 2)} sub={t('day.chance', { v: f.dec(c.Knull, 2) })} />
                <Stat label={t('day.modisConfirmed')} value={f.pct(c.modisConfirmedShare, 0)} sub={t('day.cellsOfFull', { a: f.num(c.both), b: f.num(c.both + c.onlyModis) })} />
                <Stat label={t('day.passOffset')} value={c.passOffsetMin === null ? '—' : t('common.minutes', { n: c.passOffsetMin })} sub={t(`day.passOffsetSub.${dataSource.mode}`)} />
              </div>
              <div className="venn" role="img" aria-label={t('day.vennAria', { m: c.onlyModis, b: c.both, v: c.onlyViirs })}>
                <span style={{ flex: Math.max(c.onlyModis, 0.6) }} className="m">{t('day.venn.onlyModis', { n: f.num(c.onlyModis) })}</span>
                <span style={{ flex: Math.max(c.both, 0.6) }} className="b">{t('day.venn.both', { n: f.num(c.both) })}</span>
                <span style={{ flex: Math.max(c.onlyViirs, 0.6) }} className="v">{t('day.venn.onlyViirs', { n: f.num(c.onlyViirs) })}</span>
              </div>
            </>
          )}
        </section>
      )}
      <section className="card" aria-label={t('day.refAria')}>
        <header>
          <h3>{t('day.ref.title')}</h3>
          <Tip>{t('day.ref.tip')}</Tip>
        </header>
        <div className="ref-grid">
          {state.sensor !== 'VIIRS' && <Reference d={d} sensor="MODIS" />}
          {state.sensor !== 'MODIS' && <Reference d={d} sensor="VIIRS" />}
        </div>
      </section>
    </div>
  )
}
