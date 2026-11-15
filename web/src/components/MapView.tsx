import { useEffect, useMemo, useRef, useState } from 'react'
import { Map, NavigationControl, Popup, ScaleControl, setWorkerUrl } from 'maplibre-gl'
// The production build does not emit the worker by itself: register it as an asset URL (dev resolves it from the module).
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { GeoJSONSource, MapLayerMouseEvent, StyleSpecification } from 'maplibre-gl'
import type { Feature } from 'geojson'
import 'maplibre-gl/dist/maplibre-gl.css'
import { MapPinOff } from 'lucide-react'
import type { CellDay, Scenario, SensorFilter } from '../types'
import { dataSource } from '../services'
import { MUNICIPALITIES, OUTLINE_FEATURE, cellFeatureCollection } from '../geo/region'
import { useApp } from '../state/AppState'
import { useI18n } from '../i18n/useI18n'
import { Empty } from './ui'

setWorkerUrl(workerUrl)

// No base-map tiles and no network requests: the map draws only the public region geometry and the cells of the data source.
const STYLE: StyleSpecification = { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#eaf0f6' } }] }

const escapeHtml = (v: string): string => v.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string)

const css = (name: string): string => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#888'

type Disp = 'BOTH' | 'MODIS' | 'VIIRS' | 'UNCERTAIN' | 'EXCL' | 'NONE'

function displayOf(cd: CellDay, sensor: SensorFilter, scenario: Scenario): { disp: Disp; lvl: number } {
  const lv = (n: number) => Math.min(1, 0.35 + 0.6 * Math.sqrt(n / 12))
  if (sensor === 'ALL') {
    if (scenario === 'A' && cd.excludedInA) return { disp: 'EXCL', lvl: 0.5 }
    const map: Record<string, Disp> = { BOTH: 'BOTH', MODIS_ONLY: 'MODIS', VIIRS_ONLY: 'VIIRS', UNCERTAIN: 'UNCERTAIN', NONE: 'NONE' }
    return { disp: map[cd.category], lvl: cd.category === 'BOTH' ? lv(Math.max(cd.modisCount, cd.viirsCount / 3)) : lv(cd.category === 'MODIS_ONLY' ? cd.modisCount : cd.viirsCount / 3) }
  }
  const n = sensor === 'MODIS' ? cd.modisCount : cd.viirsCount
  const cov = sensor === 'MODIS' ? cd.modisCoverage : cd.viirsCoverage
  if (scenario === 'A' && cov !== 'CORROBORATED') return { disp: n > 0 || cov === 'INDETERMINATE' ? 'EXCL' : 'NONE', lvl: 0.5 }
  if (n > 0) return { disp: sensor, lvl: lv(sensor === 'VIIRS' ? n / 3 : n) }
  return { disp: cov === 'INDETERMINATE' ? 'UNCERTAIN' : 'NONE', lvl: 0.5 }
}

function hatch(color: string): { width: number; height: number; data: Uint8Array } {
  const s = 12
  const c = document.createElement('canvas')
  c.width = c.height = s
  const g = c.getContext('2d')!
  g.strokeStyle = color
  g.lineWidth = 1.6
  g.globalAlpha = 0.75
  for (let k = -s; k <= s * 2; k += 6) {
    g.beginPath()
    g.moveTo(k, s)
    g.lineTo(k + s, 0)
    g.stroke()
  }
  return { width: s, height: s, data: new Uint8Array(g.getImageData(0, 0, s, s).data.buffer) }
}

interface Props {
  date: string
  sensor: SensorFilter
  scenario: Scenario
  selectedCellId: string | null
  /** `municipality`: IBGE municipality under the clicked/tapped point (null when unknown or the layer is off); never derived from the cell. */
  onSelectCell: (id: string | null, municipality?: string | null) => void
  showCells: boolean
  showPoints: boolean
  showMunicipalities: boolean
  resetKey?: number
  compact?: boolean
}

export function MapView({ date, sensor, scenario, selectedCellId, onSelectCell, showCells, showPoints, showMunicipalities, resetKey = 0, compact }: Props) {
  const { state } = useApp()
  const { t } = useI18n()
  const host = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const readyRef = useRef(false)
  const [failed, setFailed] = useState(false)
  const [, bump] = useState(0)
  const [detTick, setDetTick] = useState(0) // bumps when the detections of the month finish loading, so the points are drawn
  const cells = dataSource.getCells()
  const cellDays = useMemo(() => dataSource.getCellDays(date, scenario), [date, scenario])
  const onSelectRef = useRef(onSelectCell)
  onSelectRef.current = onSelectCell
  const cdRef = useRef(cellDays)
  cdRef.current = cellDays
  const tRef = useRef(t)
  tRef.current = t
  const munPopupRef = useRef<Popup | null>(null)
  const showMunRef = useRef(showMunicipalities)
  showMunRef.current = showMunicipalities
  const showCellsRef = useRef(showCells)
  showCellsRef.current = showCells

  // create the map once
  useEffect(() => {
    if (!host.current) return
    let map: Map
    try {
      const region = dataSource.getRegion()
      map = new Map({
        container: host.current,
        style: STYLE,
        bounds: [[region.bbox[0], region.bbox[1]], [region.bbox[2], region.bbox[3]]],
        fitBoundsOptions: { padding: compact ? 14 : { top: 36, right: 36, bottom: 96, left: 36 } },
        attributionControl: false,
        dragRotate: false,
        pitchWithRotate: false,
        minZoom: 4.5,
        maxZoom: 11,
      })
    } catch {
      setFailed(true)
      return
    }
    mapRef.current = map
    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    if (!compact) map.addControl(new ScaleControl({ unit: 'metric' }), 'bottom-left')
    map.touchZoomRotate.disableRotation()
    const popup = new Popup({ closeButton: false, closeOnClick: false, offset: 10, className: 'nfc-popup' })
    // municipality name: identified by the IBGE polygon under the pointer (not by the 0.25 degree cell); only while the layer is on
    const munPopup = new Popup({ closeButton: false, closeOnClick: false, offset: 12, className: 'nfc-popup nfc-mun-popup' })
    munPopupRef.current = munPopup
    let munTimer: ReturnType<typeof setTimeout> | undefined
    const munNameAt = (p: MapLayerMouseEvent['point']): string | null => {
      if (!map.getLayer('mun-fill')) return null
      const name = map.queryRenderedFeatures(p, { layers: ['mun-fill'] })[0]?.properties?.nm
      return typeof name === 'string' && name ? name : null
    }
    const munAt = (p: MapLayerMouseEvent['point']): string | null => (showMunRef.current ? munNameAt(p) : null)
    const showMun = (e: MapLayerMouseEvent, name: string) => {
      const el = document.createElement('div')
      el.className = 'map-mun'
      el.textContent = name
      munPopup.setLngLat(e.lngLat).setDOMContent(el).addTo(map)
    }
    map.on('load', () => {
      map.addSource('mun', { type: 'geojson', data: MUNICIPALITIES })
      map.addSource('outline', { type: 'geojson', data: OUTLINE_FEATURE })
      map.addSource('cells', { type: 'geojson', data: cellFeatureCollection(dataSource.getCells(), () => ({ disp: 'NONE', lvl: 0.5 })), promoteId: 'id' })
      map.addSource('points', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      map.addLayer({ id: 'mun-fill', type: 'fill', source: 'mun', paint: { 'fill-color': '#f9fbfd', 'fill-opacity': 1 } })
      map.addLayer({ id: 'mun-line', type: 'line', source: 'mun', paint: { 'line-color': '#b6c3d4', 'line-width': 0.6 } })
      map.addLayer({
        id: 'cells-fill',
        type: 'fill',
        source: 'cells',
        paint: {
          'fill-color': ['match', ['get', 'disp'], 'BOTH', '#0e9f6e', 'MODIS', '#d97706', 'VIIRS', '#6d4ae0', 'rgba(0,0,0,0)'],
          'fill-opacity': ['match', ['get', 'disp'], 'NONE', 0, 'UNCERTAIN', 0, 'EXCL', 0, ['get', 'lvl']],
        },
      })
      map.addLayer({ id: 'cells-hatch', type: 'fill', source: 'cells', filter: ['in', ['get', 'disp'], ['literal', ['UNCERTAIN', 'EXCL']]], paint: { 'fill-pattern': 'hatch', 'fill-opacity': ['match', ['get', 'disp'], 'EXCL', 0.55, 0.95] } })
      map.addLayer({ id: 'cells-line', type: 'line', source: 'cells', paint: { 'line-color': '#7b8ba3', 'line-opacity': 0.22, 'line-width': 0.5 } })
      // border cells (centre outside the state outline): dashed outline, so the area outside the territory is not read as part of it
      map.addLayer({ id: 'cells-border', type: 'line', source: 'cells', filter: ['==', ['get', 'boundary'], 1], paint: { 'line-color': '#7b8ba3', 'line-opacity': 0.9, 'line-width': 1, 'line-dasharray': [2, 2] } })
      map.addLayer({ id: 'outline', type: 'line', source: 'outline', paint: { 'line-color': '#152238', 'line-width': 2.2 } })
      map.addLayer({
        id: 'points-circle',
        type: 'circle',
        source: 'points',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 2.2, 9, 5],
          'circle-color': ['match', ['get', 'sensor'], 'MODIS', '#d97706', '#6d4ae0'],
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 1,
        },
      })
      map.addLayer({ id: 'cells-sel', type: 'line', source: 'cells', filter: ['==', ['get', 'id'], ''], paint: { 'line-color': '#58ed85', 'line-width': 3.2 } })
      map.addLayer({ id: 'cells-sel-under', type: 'line', source: 'cells', filter: ['==', ['get', 'id'], ''], paint: { 'line-color': '#152238', 'line-width': 6, 'line-opacity': 0.5 } }, 'cells-sel')
      readyRef.current = true
      bump((n) => n + 1)
    })
    map.on('click', 'cells-fill', (e) => {
      const f = e.features?.[0]
      if (f) onSelectRef.current(String(f.properties?.id), munAt(e.point))
    })
    map.on('click', 'cells-hatch', (e) => {
      const f = e.features?.[0]
      if (f) onSelectRef.current(String(f.properties?.id), munAt(e.point))
    })
    const hover = (e: MapLayerMouseEvent) => {
      const f = e.features?.[0]
      if (!f) return
      map.getCanvas().style.cursor = 'pointer'
      const cd = cdRef.current.find((c) => c.cell.id === f.properties?.id)
      if (!cd) return
      munPopup.remove()
      const mun = munAt(e.point)
      const tt = tRef.current
      popup
        .setLngLat(e.lngLat)
        .setHTML(`<div class="map-pop">${mun ? `<strong class="map-mun-name">${escapeHtml(mun)}</strong>` : ''}<b>${cd.cell.id}</b><span>${tt(`category.${cd.category}.label`)}</span><span>${tt(`map.pop.counts.${dataSource.mode}`, { m: cd.modisCount, v: cd.viirsCount })}</span></div>`)
        .addTo(map)
    }
    map.on('mousemove', 'cells-fill', hover)
    map.on('mousemove', 'cells-hatch', hover)
    const leave = () => {
      map.getCanvas().style.cursor = ''
      popup.remove()
    }
    map.on('mouseleave', 'cells-fill', leave)
    map.on('mouseleave', 'cells-hatch', leave)
    // desktop: municipality tooltip on hover where no cell tooltip is shown (cells layer off, or no cell under the pointer)
    map.on('mousemove', (e) => {
      if (!window.matchMedia('(hover: hover)').matches) return
      const overCell = showCellsRef.current && map.getLayer('cells-fill') && map.queryRenderedFeatures(e.point, { layers: ['cells-fill', 'cells-hatch'] }).length > 0
      const name = overCell ? null : munAt(e.point)
      if (name) {
        map.getCanvas().style.cursor = ''
        showMun(e, name)
      } else if (!overCell) munPopup.remove()
    })
    map.getCanvas().addEventListener('mouseleave', () => munPopup.remove())
    // touch: tap shows the municipality name for a few seconds (the tap still selects the cell as before)
    map.on('click', (e) => {
      if (window.matchMedia('(hover: hover)').matches) return
      const name = munAt(e.point)
      clearTimeout(munTimer)
      if (!name) return munPopup.remove()
      showMun(e, name)
      munTimer = setTimeout(() => munPopup.remove(), 3500)
    })
    const ro = new ResizeObserver(() => map.resize())
    ro.observe(host.current)
    return () => {
      clearTimeout(munTimer)
      munPopup.remove()
      ro.disconnect()
      readyRef.current = false
      map.remove()
      mapRef.current = null
    }
  }, [compact])

  // theme colours
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current) return
    map.setPaintProperty('bg', 'background-color', css('--map-bg'))
    map.setPaintProperty('mun-fill', 'fill-color', css('--map-land'))
    map.setPaintProperty('mun-line', 'line-color', css('--map-line'))
    map.setPaintProperty('outline', 'line-color', css('--map-outline'))
    map.setPaintProperty('cells-fill', 'fill-color', ['match', ['get', 'disp'], 'BOTH', css('--cat-both'), 'MODIS', css('--cat-modis'), 'VIIRS', css('--cat-viirs'), 'rgba(0,0,0,0)'])
    map.setPaintProperty('points-circle', 'circle-color', ['match', ['get', 'sensor'], 'MODIS', css('--cat-modis'), css('--cat-viirs')])
    map.setPaintProperty('cells-sel', 'line-color', state.theme === 'ikarus-dark' ? '#ffffff' : '#0e9f6e')
    map.setPaintProperty('cells-border', 'line-color', css('--map-outline'))
    if (map.hasImage('hatch')) map.removeImage('hatch')
    map.addImage('hatch', hatch(css('--cat-uncertain')))
  }, [state.theme, readyRef.current])

  // data
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current) return
    const byId = new globalThis.Map(cellDays.map((c) => [c.cell.id, c]))
    const fc = cellFeatureCollection(cells, (c) => {
      const cd = byId.get(c.id)!
      return { ...displayOf(cd, sensor, scenario), mc: cd.modisCount, vc: cd.viirsCount }
    })
    ;(map.getSource('cells') as GeoJSONSource).setData(fc)
  }, [cellDays, cells, sensor, scenario, readyRef.current])

  // layer visibility
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current) return
    const vis = (id: string, on: boolean) => map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none')
    vis('cells-fill', showCells)
    vis('cells-hatch', showCells)
    vis('cells-line', showCells)
    vis('cells-border', showCells)
    vis('mun-line', showMunicipalities)
    vis('points-circle', showPoints)
    if (!showMunicipalities) munPopupRef.current?.remove()
  }, [showCells, showPoints, showMunicipalities, readyRef.current])

  // individual detection points (needs the detections of the month to be loaded when enabled)
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current) return
    const features: Feature[] = []
    if (showPoints && !dataSource.isReady({ kind: 'detections', date })) {
      // load the detections of the month on demand, then redraw
      let alive = true
      dataSource
        .ensure({ kind: 'detections', date })
        .then(() => alive && setDetTick((n) => n + 1))
        .catch(() => undefined)
      return () => {
        alive = false
      }
    }
    if (showPoints) {
      for (const cd of cellDays) {
        const n = (sensor === 'VIIRS' ? 0 : cd.modisCount) + (sensor === 'MODIS' ? 0 : cd.viirsCount)
        if (n === 0) continue
        for (const d of dataSource.getDetections(date, cd.cell.id)) {
          if (sensor !== 'ALL' && d.sensor !== sensor) continue
          features.push({ type: 'Feature', properties: { sensor: d.sensor }, geometry: { type: 'Point', coordinates: [d.lon, d.lat] } })
        }
      }
    }
    ;(map.getSource('points') as GeoJSONSource).setData({ type: 'FeatureCollection', features })
  }, [showPoints, cellDays, sensor, date, detTick, readyRef.current])

  // selection
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current) return
    map.setFilter('cells-sel', ['==', ['get', 'id'], selectedCellId ?? ''])
    map.setFilter('cells-sel-under', ['==', ['get', 'id'], selectedCellId ?? ''])
  }, [selectedCellId, readyRef.current])

  // reset view
  useEffect(() => {
    const map = mapRef.current
    if (!map || !readyRef.current || resetKey === 0) return
    const region = dataSource.getRegion()
    map.fitBounds([[region.bbox[0], region.bbox[1]], [region.bbox[2], region.bbox[3]]], { padding: compact ? 14 : { top: 36, right: 36, bottom: 96, left: 36 }, duration: 500 })
  }, [resetKey, compact])

  if (failed) {
    return <Empty icon={<MapPinOff size={28} />} title={t('map.failed.title')}>{t('map.failed.body', { n: cells.length })}</Empty>
  }
  return (
    <>
      <div ref={host} className="map" role="application" aria-label={t(`map.aria.${dataSource.mode}`, { n: cells.length })} />
      <div className="map-attrib">{t(`map.attribution.${dataSource.mode}`)}</div>
    </>
  )
}
