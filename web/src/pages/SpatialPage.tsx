import { useEffect, useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight, Crosshair, Layers, Search } from 'lucide-react'
import { useApp } from '../state/AppState'
import { dataSource, type Need } from '../services'
import { useI18n } from '../i18n/useI18n'
import { MapView } from '../components/MapView'
import { EvidencePanel } from '../components/EvidencePanel'
import { DataBoundary } from '../components/DataBoundary'
import { Badge, Empty, Legend, Seg, SensorTag } from '../components/ui'
import { addDays } from '../lib/format'

export function SpatialPage() {
  const { state } = useApp()
  const year = Number(state.date.slice(0, 4))
  const needs: Need[] = [{ kind: 'year', year }, { kind: 'cells', date: state.date }]
  return (
    <DataBoundary needs={needs}>
      <SpatialInner />
    </DataBoundary>
  )
}

function SpatialInner() {
  const { state, patch, selectDate } = useApp()
  const { t, f } = useI18n()
  const [reset, setReset] = useState(0)
  // municipality at the point the user tapped; only valid for the cell tapped, and dropped on any other way of selecting a cell
  const [tapped, setTapped] = useState<{ cellId: string; name: string } | null>(null)
  // any way of closing the panel (button, Escape, date change, URL) forgets the tapped point, so a later selection of the same cell never reuses it
  useEffect(() => {
    if (!state.selectedCellId) setTapped(null)
  }, [state.selectedCellId])
  const range = dataSource.getRange()
  const cells = useMemo(() => dataSource.getCellDays(state.date, state.scenario), [state.date, state.scenario])
  const day = useMemo(() => dataSource.getDay(state.date, state.scenario), [state.date, state.scenario])
  const top = useMemo(
    () =>
      cells
        .filter((c) => c.category !== 'NONE')
        .filter((c) => (state.sensor === 'MODIS' ? c.modisCount > 0 : state.sensor === 'VIIRS' ? c.viirsCount > 0 : true))
        .sort((a, b) => b.modisCount + b.viirsCount - (a.modisCount + a.viirsCount))
        .slice(0, 12),
    [cells, state.sensor],
  )
  const counts = useMemo(() => {
    const k = { BOTH: 0, MODIS_ONLY: 0, VIIRS_ONLY: 0, UNCERTAIN: 0 }
    for (const c of cells) if (c.category in k) k[c.category as keyof typeof k]++
    return k
  }, [cells])

  return (
    <div className="spatial">
      <div className="sp-toolbar" role="toolbar" aria-label={t('spatial.controls')}>
        <div className="datepick">
          <button type="button" className="icon-btn" aria-label={t('common.previousDay')} disabled={state.date <= range.first} onClick={() => selectDate(addDays(state.date, -1))}>
            <ChevronLeft size={18} />
          </button>
          <label className="sr" htmlFor="sp-date">{t('spatial.date')}</label>
          <input id="sp-date" type="date" lang={state.lang} min={range.first} max={range.last} value={state.date} onChange={(e) => e.target.value && selectDate(e.target.value)} />
          <button type="button" className="icon-btn" aria-label={t('common.nextDay')} disabled={state.date >= range.last} onClick={() => selectDate(addDays(state.date, 1))}>
            <ChevronRight size={18} />
          </button>
        </div>
        <Seg
          label={t('spatial.sensor')}
          value={state.sensor}
          onChange={(s) => patch({ sensor: s })}
          options={[
            { id: 'ALL', label: t('spatial.sensorBoth') },
            { id: 'MODIS', label: <><i className="dot modis" /> MODIS</> },
            { id: 'VIIRS', label: <><i className="dot viirs" /> VIIRS</> },
          ]}
        />
        <div className="layers" role="group" aria-label={t('spatial.layers')}>
          <Layers size={16} aria-hidden />
          <label><input type="checkbox" checked={state.showCells} onChange={(e) => patch({ showCells: e.target.checked })} /> {t('spatial.layer.cells')}</label>
          <label><input type="checkbox" checked={state.showPoints} onChange={(e) => patch({ showPoints: e.target.checked })} /> {t(`spatial.layer.points.${dataSource.mode}`)}</label>
          <label><input type="checkbox" checked={state.showMunicipalities} onChange={(e) => patch({ showMunicipalities: e.target.checked })} /> {t('spatial.layer.municipalities')}</label>
        </div>
        <button type="button" className="btn sm" onClick={() => setReset((n) => n + 1)}>
          <Crosshair size={14} /> {t('spatial.resetView')}
        </button>
      </div>
      <div className="sp-body">
        <div className="map-wrap">
          <MapView
            date={state.date}
            sensor={state.sensor}
            scenario={state.scenario}
            selectedCellId={state.selectedCellId}
            onSelectCell={(id, mun) => {
              setTapped(id && mun ? { cellId: id, name: mun } : null)
              patch({ selectedCellId: id })
            }}
            showCells={state.showCells}
            showPoints={state.showPoints}
            showMunicipalities={state.showMunicipalities}
            resetKey={reset}
          />
          <div className="map-chip"><b>{f.dateLong(state.date)}</b> · {t(`spatial.chip.${dataSource.mode}`, { scenario: state.scenario })}</div>
          <div className="map-legend">
            <Legend />
            {state.scenario === 'A' && <span className="legend"><span><i className="sw excluded" /> {t('spatial.excludedA')}</span></span>}
          </div>
        </div>
        <aside className="sp-side" aria-label={t('spatial.side.aria')}>
          <section className="card">
            <header>
              <h3>{t('spatial.summary')}</h3>
              <Badge tone={day.comparison.comparable ? 'green' : 'magenta'}>{day.comparison.comparable ? t('common.comparable') : t('common.notComparable')}</Badge>
            </header>
            <div className="mini-grid">
              <div><SensorTag sensor="MODIS" /><b>{f.pct(day.modis.extent)}</b><span className="muted">{t('common.detShort', { n: f.num(day.modis.detections) })}</span></div>
              <div><SensorTag sensor="VIIRS" /><b>{f.pct(day.viirs.extent)}</b><span className="muted">{t('common.detShort', { n: f.num(day.viirs.detections) })}</span></div>
              <div>
                <span className="muted">{t('spatial.agreement')}</span>
                <b>K {day.comparison.K === null ? t('common.na') : f.dec(day.comparison.K, 2)}</b>
                <span className="muted">{day.comparison.K === null ? t('common.notApplicable') : t('day.chance', { v: f.dec(day.comparison.Knull, 2) })}</span>
              </div>
            </div>
            <div className="counts">
              <span><i className="sw both" /> {t('spatial.count.both', { n: f.num(counts.BOTH) })}</span>
              <span><i className="sw modis" /> {t('spatial.count.modis', { n: f.num(counts.MODIS_ONLY) })}</span>
              <span><i className="sw viirs" /> {t('spatial.count.viirs', { n: f.num(counts.VIIRS_ONLY) })}</span>
              <span><i className="sw uncertain" /> {t('spatial.count.uncertain', { n: f.num(counts.UNCERTAIN) })}</span>
            </div>
            {day.flags.map((flag) => (<span key={flag} className="badge amber">{t(`flags.${flag}`)}</span>))}
          </section>
          <section className="card">
            <header>
              <h3><Search size={14} aria-hidden /> {t('spatial.top.title')} <span className="muted">({t('spatial.top.hint')})</span></h3>
            </header>
            {top.length === 0 ? (
              <Empty title={t('spatial.top.empty.title')}>{t('spatial.top.empty.body')}</Empty>
            ) : (
              <table className="table">
                <thead>
                  <tr><th>{t('spatial.top.cell')}</th><th>{t('spatial.top.category')}</th><th className="num">M</th><th className="num">V</th></tr>
                </thead>
                <tbody>
                  {top.map((c) => (
                    <tr key={c.cell.id} className={`clickable${state.selectedCellId === c.cell.id ? ' on' : ''}`}>
                      <td>
                        <button type="button" className="linkish" onClick={() => { setTapped(null); patch({ selectedCellId: c.cell.id }) }} aria-label={t('spatial.top.open', { cell: c.cell.id })}>
                          {c.cell.i}, {c.cell.j}
                        </button>
                      </td>
                      <td>{t(`category.${c.category}.short`)}</td>
                      <td className="num">{c.modisCount}</td>
                      <td className="num">{c.viirsCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </aside>
        {state.selectedCellId && (
          <EvidencePanel
            cellId={state.selectedCellId}
            municipality={state.showMunicipalities && tapped?.cellId === state.selectedCellId ? tapped.name : null}
            onClose={() => { setTapped(null); patch({ selectedCellId: null }) }}
          />
        )}
      </div>
    </div>
  )
}
