/* Illustrative diagrams for the Methodology page. They are didactic drawings, not data. */
import type { CSSProperties, ReactElement, ReactNode } from 'react'
import { useI18n } from '../i18n/useI18n'

export function Figure({ children, caption }: { children: ReactNode; caption: string }) {
  const { t } = useI18n()
  return (
    <figure className="diagram">
      <div className="diagram-tag">{t('diagrams.tag')}</div>
      {children}
      <figcaption>{caption}</figcaption>
    </figure>
  )
}

/** One SVG text line per dictionary key, `step` units apart. */
function Lines({ x, y, keys, step = 12, className = 'dg-t', anchor, style }: { x: number; y: number; keys: string[]; step?: number; className?: string; anchor?: 'start' | 'middle' | 'end'; style?: CSSProperties }) {
  const { t } = useI18n()
  return (
    <>
      {keys.map((k, i) => (
        <text key={k} x={x} y={y + i * step} textAnchor={anchor} className={className} style={style}>
          {t(k)}
        </text>
      ))}
    </>
  )
}

export function PixelDiagram() {
  const { t } = useI18n()
  const cells: ReactElement[] = []
  for (let i = 0; i < 8; i++)
    for (let j = 0; j < 8; j++) cells.push(<rect key={`${i}${j}`} x={16 + j * 17.5} y={16 + i * 17.5} width="17.5" height="17.5" className="px-v" />)
  return (
    <Figure caption={t('diagrams.pixel.caption')}>
      <svg viewBox="0 0 340 170" role="img" aria-label={t('diagrams.pixel.aria')}>
        {cells}
        <rect x="50" y="34" width="52.5" height="52.5" className="px-m" />
        <circle cx="72" cy="58" r="5" className="px-hot" />
        <circle cx="86" cy="73" r="3" className="px-hot" />
        <Lines x={176} y={40} keys={['diagrams.pixel.modis.t']} className="dg-t b" />
        <Lines x={176} y={54} keys={['diagrams.pixel.modis.l1', 'diagrams.pixel.modis.l2']} />
        <Lines x={176} y={90} keys={['diagrams.pixel.viirs.t']} className="dg-t b" style={{ fill: 'var(--cat-viirs-text)' }} />
        <Lines x={176} y={104} keys={['diagrams.pixel.viirs.l1', 'diagrams.pixel.viirs.l2']} />
        <Lines x={176} y={140} keys={['diagrams.pixel.foot.l1', 'diagrams.pixel.foot.l2']} />
      </svg>
    </Figure>
  )
}

export function FlowDiagram() {
  const { t } = useI18n()
  const box = (x: number, y: number, w: number, label: string, cls = '') => (
    <g>
      <rect x={x} y={y} width={w} height="38" rx="9" className={`fl-box ${cls}`} />
      <text x={x + w / 2} y={y + 23} textAnchor="middle" className="dg-t b">{label}</text>
    </g>
  )
  return (
    <Figure caption={t('diagrams.flow.caption')}>
      <svg viewBox="0 0 360 150" role="img" aria-label={t('diagrams.flow.aria')}>
        {box(8, 14, 82, t('diagrams.flow.pixel'))}
        {box(138, 14, 100, t('diagrams.flow.anomaly'))}
        {box(262, 14, 90, t('diagrams.flow.detection'), 'ok')}
        <path d="M90 33h44M238 33h20" className="fl-arrow" />
        {box(262, 96, 90, t('diagrams.flow.fire'), 'no')}
        <path d="M307 52v40" className="fl-arrow dashed" />
        <Lines x={300} y={72} keys={['diagrams.flow.need.l1', 'diagrams.flow.need.l2']} anchor="end" />
        <Lines x={8} y={86} keys={['diagrams.flow.unknown.t']} />
        <Lines x={8} y={104} keys={['diagrams.flow.unknown.l1', 'diagrams.flow.unknown.l2']} step={18} />
      </svg>
    </Figure>
  )
}

export function ExtentDiagram() {
  const { t } = useI18n()
  const grid = (active: [number, number][], x0: number, cls: string, label: string, sub: string) => (
    <g>
      {Array.from({ length: 36 }, (_, k) => {
        const i = Math.floor(k / 6)
        const j = k % 6
        const on = active.some(([a, b]) => a === i && b === j)
        return <rect key={k} x={x0 + j * 20} y={14 + i * 20} width="18" height="18" rx="3" className={on ? cls : 'ex-off'} />
      })}
      <text x={x0 + 60} y="152" textAnchor="middle" className="dg-t b">{label}</text>
      <text x={x0 + 60} y="167" textAnchor="middle" className="dg-t">{sub}</text>
    </g>
  )
  const spread: [number, number][] = [[0, 1], [0, 4], [1, 2], [2, 0], [2, 5], [3, 3], [4, 1], [4, 4], [5, 2], [1, 5], [3, 0], [5, 5]]
  const concentrated: [number, number][] = [[2, 2], [2, 3], [3, 2]]
  return (
    <Figure caption={t('diagrams.extent.caption')}>
      <svg viewBox="0 0 320 176" role="img" aria-label={t('diagrams.extent.aria')}>
        {grid(spread, 12, 'ex-on', t('diagrams.extent.spread'), t('diagrams.extent.dets'))}
        {grid(concentrated, 176, 'ex-on hot', t('diagrams.extent.packed'), t('diagrams.extent.dets'))}
      </svg>
    </Figure>
  )
}

export function SwathDiagram() {
  const { t } = useI18n()
  return (
    <Figure caption={t('diagrams.swath.caption')}>
      <svg viewBox="0 0 360 170" role="img" aria-label={t('diagrams.swath.aria')}>
        <rect x="14" y="12" width="200" height="140" rx="10" className="sw-region" />
        <rect x="14" y="12" width="120" height="140" rx="10" className="sw-cov" />
        <rect x="134" y="12" width="40" height="140" className="sw-part" />
        <text x="74" y="86" textAnchor="middle" className="dg-t b">{t('diagrams.swath.covered')}</text>
        <text x="154" y="86" textAnchor="middle" className="dg-t b" style={{ transform: 'rotate(-90deg)', transformOrigin: '154px 86px' }}>{t('diagrams.swath.partial')}</text>
        <text x="194" y="86" textAnchor="middle" className="dg-t b">{t('diagrams.swath.unknown')}</text>
        <Lines x={228} y={40} keys={['diagrams.swath.rules.t']} className="dg-t b" />
        <Lines x={228} y={58} keys={['diagrams.swath.rules.l1', 'diagrams.swath.rules.l2', 'diagrams.swath.rules.l3']} />
        <Lines x={228} y={102} keys={['diagrams.swath.rules.l4', 'diagrams.swath.rules.l5']} />
        <Lines x={228} y={134} keys={['diagrams.swath.rules.l6', 'diagrams.swath.rules.l7']} />
      </svg>
    </Figure>
  )
}

export function VennDiagram() {
  const { t } = useI18n()
  return (
    <Figure caption={t('diagrams.venn.caption')}>
      <svg viewBox="0 0 380 150" role="img" aria-label={t('diagrams.venn.aria')}>
        <circle cx="110" cy="76" r="54" className="vn-m" />
        <circle cx="170" cy="76" r="54" className="vn-v" />
        <text x="78" y="80" textAnchor="middle" className="dg-t b">{t('diagrams.venn.onlyModis')}</text>
        <text x="140" y="80" textAnchor="middle" className="dg-t b">{t('diagrams.venn.both')}</text>
        <text x="204" y="80" textAnchor="middle" className="dg-t b">{t('diagrams.venn.onlyViirs')}</text>
        <Lines x={240} y={60} keys={['diagrams.venn.formula']} className="dg-t b" />
        <Lines x={240} y={78} keys={['diagrams.venn.chance.l1', 'diagrams.venn.chance.l2']} step={14} />
      </svg>
    </Figure>
  )
}
