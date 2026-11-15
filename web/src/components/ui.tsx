import type { ReactNode } from 'react'
import { AlertTriangle, Info } from 'lucide-react'
import type { CoverageState, SensorFilter } from '../types'
import { COVERAGE_TONE } from '../lib/format'
import { dataSource } from '../services'
import { useI18n } from '../i18n/useI18n'

type Tone = 'green' | 'amber' | 'violet' | 'magenta' | 'neutral' | 'modis' | 'viirs' | 'both'

export function Badge({ tone, children, title }: { tone: Tone; children: ReactNode; title?: string }) {
  return (
    <span className={`badge ${tone}`} title={title}>
      {children}
    </span>
  )
}

export function Tip({ children, label }: { children: ReactNode; label?: string }) {
  const { t } = useI18n()
  return (
    <span className="tip">
      <button type="button" aria-label={label ?? t('common.moreInfo')}>
        <Info size={14} aria-hidden />
      </button>
      <span className="pop" role="tooltip">
        {children}
      </span>
    </span>
  )
}

export function Seg<T extends string>({
  value,
  options,
  onChange,
  label,
  compact,
}: {
  value: T
  options: { id: T; label: ReactNode; title?: string; ariaLabel?: string }[]
  onChange: (v: T) => void
  label: string
  compact?: boolean
}) {
  return (
    <div className={`seg${compact ? ' compact' : ''}`} role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <button key={o.id} type="button" role="radio" aria-checked={o.id === value} aria-label={o.ariaLabel} title={o.title} onClick={() => onChange(o.id)}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function CoverageBadge({ state }: { state: CoverageState }) {
  const { t } = useI18n()
  return (
    <Badge tone={COVERAGE_TONE[state]} title={t(`coverage.${state}.tip`)}>
      {t(`coverage.${state}.label`)}
    </Badge>
  )
}

export function SensorTag({ sensor }: { sensor: Exclude<SensorFilter, 'ALL'> | 'BOTH' }) {
  const { t } = useI18n()
  const cls = sensor === 'MODIS' ? 'modis' : sensor === 'VIIRS' ? 'viirs' : 'both'
  return (
    <Badge tone={cls}>
      <i className={`dot ${cls}`} aria-hidden /> {sensor === 'BOTH' ? t('sensor.both') : sensor}
    </Badge>
  )
}

export function Callout({ children, tone = 'warn', title }: { children: ReactNode; tone?: 'warn' | 'info'; title?: string }) {
  return (
    <div className={`callout${tone === 'info' ? ' info' : ''}`} role="note">
      {tone === 'info' ? <Info size={18} aria-hidden /> : <AlertTriangle size={18} aria-hidden />}
      <div>
        {title && <b>{title} </b>}
        {children}
      </div>
    </div>
  )
}

export function Stat({ label, value, sub, tip }: { label: ReactNode; value: ReactNode; sub?: ReactNode; tip?: ReactNode }) {
  return (
    <div className="stat">
      <span className="k">
        {label}
        {tip && <Tip>{tip}</Tip>}
      </span>
      <span className="v">{value}</span>
      {sub && <span className="d">{sub}</span>}
    </div>
  )
}

export function Empty({ icon, title, children }: { icon?: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="empty" role="status">
      {icon}
      <b>{title}</b>
      {children && <span>{children}</span>}
    </div>
  )
}

export function Legend() {
  const { t } = useI18n()
  return (
    <div className="legend" aria-label={t('legend.aria')}>
      <span>
        <i className="sw both" /> {t('category.BOTH.label')}
      </span>
      <span>
        <i className="sw modis" /> {t('category.MODIS_ONLY.label')}
      </span>
      <span>
        <i className="sw viirs" /> {t('category.VIIRS_ONLY.label')}
      </span>
      <span>
        <i className="sw uncertain" /> {t('category.UNCERTAIN.label')}
      </span>
      {dataSource.mode === 'REAL' && (
        <span>
          <i className="sw border" /> {t('legend.border')}
        </span>
      )}
    </div>
  )
}
