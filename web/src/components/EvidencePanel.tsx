import { useEffect, useMemo, useRef, useState } from 'react'
import { CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-react'
import type { CellDay, CoverageState, DayRecord } from '../types'
import { dataSource } from '../services'
import { useApp } from '../state/AppState'
import { isCloseKey } from '../state/model'
import { useI18n } from '../i18n/useI18n'
import { Badge, Callout, CoverageBadge, SensorTag, Stat } from './ui'
import { DataBoundary } from './DataBoundary'
import { addDays } from '../lib/format'

const SHOWN = 40

/** `municipality`: name of the IBGE polygon at the point the user tapped on the map. Omitted when there is no such point (list or keyboard selection) or it cannot be identified. */
export function EvidencePanel({ cellId, onClose, municipality }: { cellId: string; onClose: () => void; municipality?: string | null }) {
  const { state } = useApp()
  const { t, f } = useI18n()
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    // Remember what opened the drawer so focus can go back to it when it closes.
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    closeRef.current?.focus()
    return () => {
      if (opener && opener.isConnected && opener !== document.body) opener.focus()
    }
  }, [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isCloseKey(e)) onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const year = Number(state.date.slice(0, 4))
  const cell = dataSource.getCells().find((c) => c.id === cellId)
  return (
    <aside className="drawer" role="dialog" aria-modal="false" aria-label={t('evidence.aria', { cell: cellId })}>
      <div className="drawer-head">
        <div>
          <span className="eyebrow">{t(`evidence.eyebrow.${dataSource.mode}`)}</span>
          <h2>{t('evidence.cell', { i: cell?.i ?? '', j: cell?.j ?? '' })}</h2>
          {municipality && (
            <div className="drawer-mun">
              <span className="muted">{t('evidence.municipality')}:</span> <b>{municipality}</b>
            </div>
          )}
          {cell && (
            <div className="muted mono" style={{ fontSize: 'var(--text-xs)' }}>
              {cell.id} · {f.dec(cell.lat0, 2)}° / {f.dec(cell.lat1, 2)}° · {f.dec(cell.lon0, 2)}° / {f.dec(cell.lon1, 2)}° ({t('evidence.cellSize')})
            </div>
          )}
        </div>
        <button ref={closeRef} type="button" className="icon-btn" onClick={onClose} aria-label={t('evidence.close')}>
          <X size={18} />
        </button>
      </div>
      <div className="drawer-body">
        <DataBoundary needs={[{ kind: 'year', year }, { kind: 'cells', date: state.date }, { kind: 'detections', date: state.date }]}>
          <EvidenceBody cellId={cellId} />
        </DataBoundary>
      </div>
    </aside>
  )
}

function EvidenceBody({ cellId }: { cellId: string }) {
  const { state, selectDate, go, patch } = useApp()
  const { t, f } = useI18n()
  const [all, setAll] = useState(false)
  const cd = useMemo(() => dataSource.getCellDays(state.date, state.scenario).find((c) => c.cell.id === cellId), [state.date, state.scenario, cellId])
  const day = useMemo(() => dataSource.getDay(state.date, state.scenario), [state.date, state.scenario])
  const dets = useMemo(() => dataSource.getDetections(state.date, cellId), [state.date, cellId])
  const range = dataSource.getRange()
  if (!cd) return null
  const shown = all ? dets : dets.slice(0, SHOWN)

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <button className="btn sm" type="button" aria-label={t('common.previousDay')} disabled={state.date <= range.first} onClick={() => selectDate(addDays(state.date, -1))}>
          <ChevronLeft size={14} />
        </button>
        <b>{f.dateLong(state.date)}</b>
        <button className="btn sm" type="button" aria-label={t('common.nextDay')} disabled={state.date >= range.last} onClick={() => selectDate(addDays(state.date, 1))}>
          <ChevronRight size={14} />
        </button>
        <span style={{ flex: 1 }} />
        <button className="btn sm" type="button" onClick={() => go('calendar', { selectedCellId: null })}>
          <CalendarDays size={14} /> {t('nav.calendar')}
        </button>
      </div>

      <section aria-labelledby="ev-int" className="card" style={{ boxShadow: 'none' }}>
        <h3 id="ev-int">{t('evidence.interpretation')}</h3>
        <div>
          {cd.category === 'BOTH' ? <SensorTag sensor="BOTH" /> : cd.category === 'MODIS_ONLY' ? <SensorTag sensor="MODIS" /> : cd.category === 'VIIRS_ONLY' ? <SensorTag sensor="VIIRS" /> : <Badge tone="neutral">{t(`category.${cd.category}.label`)}</Badge>}
          {state.scenario === 'A' && cd.excludedInA && (
            <>
              {' '}
              <Badge tone="neutral" title={t('evidence.excludedA.tip')}>{t('evidence.excludedA')}</Badge>
            </>
          )}
        </div>
        <p className="sub" style={{ margin: 0 }}>{t(`evidence.why.${cd.category}`)}</p>
        {cd.cell.boundary && <p className="note">{t('evidence.boundary')}</p>}
      </section>

      <section aria-labelledby="ev-sat" className="card" style={{ boxShadow: 'none' }}>
        <h3 id="ev-sat">{t('evidence.sat.title')}</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>{t('evidence.sat.satellite')}</th>
                <th className="num"><abbr title={t('metric.detections.label')} style={{ textDecoration: 'none' }}>{t('evidence.sat.det')}</abbr></th>
                <th className="num">{t('evidence.sat.pass')}</th>
                <th>{t('evidence.sat.coverage')}</th>
                <th className="num">{t('evidence.sat.version')}</th>
              </tr>
            </thead>
            <tbody>
              <SatRow name="Terra" n={cd.terra} cd={cd} day={day} />
              <SatRow name="Aqua" n={cd.aqua} cd={cd} day={day} />
              <SatRow name="NOAA-20" n={cd.noaa20} cd={cd} day={day} />
            </tbody>
          </table>
        </div>
        <p className="note">{t('evidence.sat.note')}</p>
      </section>

      <section aria-labelledby="ev-cmp" className="card" style={{ boxShadow: 'none' }}>
        <h3 id="ev-cmp">{t('evidence.cmp.title')}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
          <Stat
            label={t('common.comparable')}
            value={day.comparison.comparable ? t('common.yes') : t('common.no')}
            sub={day.comparison.comparable ? t('evidence.cmp.cells', { n: f.num(day.comparison.comparableCells) }) : day.comparison.reason ? t(`comparison.reason.${day.comparison.reason}`) : ''}
          />
          <Stat label="K" value={day.comparison.K === null ? t('common.na') : f.dec(day.comparison.K, 2)} sub={day.comparison.K === null ? t('evidence.cmp.kNa') : t('day.chance', { v: f.dec(day.comparison.Knull, 2) })} />
          <Stat label={t('day.passOffset')} value={day.comparison.passOffsetMin === null ? '—' : t('common.minutes', { n: day.comparison.passOffsetMin })} sub="Aqua − NOAA-20" />
        </div>
      </section>

      <section aria-labelledby="ev-det">
        <h3 id="ev-det" style={{ margin: '0 0 8px', fontSize: 'var(--text-sm)' }}>
          {t('evidence.det.title')} <span className="muted">({t(`evidence.det.count.${dataSource.mode}`, { n: f.num(dets.length) })})</span>
        </h3>
        {dets.length === 0 ? (
          <div className="empty" role="status">
            <b>{t('evidence.det.empty.title')}</b>
            <span>{t('evidence.det.empty.body')}</span>
          </div>
        ) : (
          <>
            <ul className="det-list">
              {shown.map((d) => (
                <li key={d.id} className="det">
                  <span className="t">{d.timeUtc} UTC</span>
                  <span>
                    <SensorTag sensor={d.sensor} /> <span className="muted">{d.satellite}</span>
                  </span>
                  <span className="muted mono">{d.dayNight === null ? '—' : t(`evidence.det.dn.${d.dayNight}`)}</span>
                  <span className="m">
                    <span>{t('evidence.det.lat')} <b>{f.dec(d.lat, 4)}</b></span>
                    <span>{t('evidence.det.lon')} <b>{f.dec(d.lon, 4)}</b></span>
                    <span>FRP <b>{d.frpMw === null ? '—' : `${f.dec(d.frpMw, 1)} MW`}</b></span>
                    <span>{t('evidence.det.confidence')} <b>{d.confidence ?? '—'}</b></span>
                    <span>{t('evidence.det.pixel')} <b>{d.pixelKm ? `${f.dec(d.pixelKm[0], 2)} × ${f.dec(d.pixelKm[1], 2)} km` : '—'}</b></span>
                    <span>{t('evidence.sat.version')} <b>{d.productVersion ?? '—'}</b></span>
                    <span className="mono" style={{ wordBreak: 'break-all' }} title={d.sourceSha256}>
                      {d.sourceSha256 ? `${t('evidence.det.source')}: ${d.sourceSha256.slice(0, 12)}… · ${t('evidence.det.line', { n: d.sourceLine ?? '—' })}` : d.sourceFile}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
            {dets.length > SHOWN && !all && (
              <button type="button" className="btn sm" onClick={() => setAll(true)}>
                {t('evidence.det.showAll', { n: f.num(dets.length) })}
              </button>
            )}
          </>
        )}
      </section>

      <Callout title={t('evidence.limits.title')}>{t(`evidence.limits.body.${dataSource.mode}`)}</Callout>
      <button type="button" className="btn" onClick={() => patch({ selectedCellId: null })}>
        {t('evidence.clear')}
      </button>
    </>
  )
}

function SatRow({ name, n, cd, day }: { name: 'Terra' | 'Aqua' | 'NOAA-20'; n: number; cd: CellDay; day: DayRecord }) {
  const { t } = useI18n()
  const sats = [...day.modis.satellites, ...day.viirs.satellites]
  const s = sats.find((x) => x.satellite === name)!
  const own = cd.satCoverage?.[name]
  const cov: CoverageState = own ? own.state : name === 'NOAA-20' ? cd.viirsCoverage : s.coverageState
  return (
    <tr>
      <td>
        <SensorTag sensor={name === 'NOAA-20' ? 'VIIRS' : 'MODIS'} /> <span className="muted">{name}</span>
      </td>
      <td className="num">{n}</td>
      <td className="num">{s.passUtc ?? '—'}</td>
      <td>
        <CoverageBadge state={cov} />
        {own && own.state === 'PARTIAL' && <span className="muted"> {t('evidence.sat.fraction', { v: Math.round(own.fraction * 100) })}</span>}
      </td>
      <td className="num">{s.productVersion ?? '—'}</td>
    </tr>
  )
}
