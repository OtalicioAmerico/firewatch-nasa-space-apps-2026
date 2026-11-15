import type { ReactNode } from 'react'
import { BookOpen, CalendarDays, FlaskConical, LayoutDashboard, Map as MapIcon, Menu, Moon, Sun, Users } from 'lucide-react'
import { Brand } from './Brand'
import { Seg, Tip } from './ui'
import { useApp, type PageId } from '../state/AppState'
import { dataSource } from '../services'
import { useI18n } from '../i18n/useI18n'
import { LANGS, type Lang } from '../i18n'

const NAV: { id: PageId; icon: ReactNode }[] = [
  { id: 'overview', icon: <LayoutDashboard size={18} /> },
  { id: 'calendar', icon: <CalendarDays size={18} /> },
  { id: 'spatial', icon: <MapIcon size={18} /> },
  { id: 'methodology', icon: <BookOpen size={18} /> },
  { id: 'about', icon: <Users size={18} /> },
]

export function DemoPill({ top }: { top?: boolean }) {
  const { t } = useI18n()
  return (
    <span className={`demo-pill${top ? ' top' : ''}${dataSource.mode === 'REAL' ? ' real' : ''}`} title={t(`mode.${dataSource.mode}.note`)}>
      <i aria-hidden /> {t(`mode.${dataSource.mode}.label`)}
    </span>
  )
}

export function LanguageSwitch() {
  const { state, setLang } = useApp()
  const { t } = useI18n()
  return (
    <Seg<Lang>
      compact
      label={t('lang.label')}
      value={state.lang}
      onChange={setLang}
      options={LANGS.map((l) => ({ id: l, label: l === 'pt-BR' ? 'PT' : 'EN', title: t(`lang.${l}`), ariaLabel: t(`lang.${l}`) }))}
    />
  )
}

export function Sidebar() {
  const { state, go, patch } = useApp()
  const { t, f } = useI18n()
  const region = dataSource.getRegion()
  return (
    <>
      <div className="scrim" data-open={state.navOpen} onClick={() => patch({ navOpen: false })} />
      <aside className="sidebar" data-open={state.navOpen} aria-label={t('nav.primary')}>
        <Brand />
        <nav className="nav" aria-label={t('nav.main')}>
          {NAV.map((n) => (
            <button key={n.id} type="button" aria-current={state.page === n.id ? 'page' : undefined} onClick={() => go(n.id)}>
              {n.icon}
              {t(`nav.${n.id}`)}
            </button>
          ))}
          <div className="nav-sub">{t('nav.shortcuts')}</div>
          <button type="button" onClick={() => go('spatial', { showCells: true, sensor: 'ALL' })}>
            <FlaskConical size={18} /> {t('nav.compareOnMap')}
          </button>
        </nav>
        <div className="side-foot">
          <div className="side-card">
            <strong>{region.name}, {t(`region.country.${region.country}`)}</strong>
            <div className="row"><span>{t('side.cells')}</span><b>{f.dec(region.cellSizeDeg, 2)}° ({t('common.experimental').toLowerCase()})</b></div>
            <div className="row"><span>{t('side.period')}</span><b>2021 – 2025</b></div>
            <div className="row"><span>{t('side.coverageRule')}</span><b>{t(`scenario.${state.scenario}.full`)}</b></div>
          </div>
          <div className="side-scn">
            <span>{t('scenario.label')}</span>
            <Seg
              compact
              label={t('scenario.labelSidebar')}
              value={state.scenario}
              onChange={(v) => patch({ scenario: v })}
              options={[
                { id: 'A', label: t('scenario.A.full') },
                { id: 'B', label: t('scenario.B.full') },
              ]}
            />
          </div>
          <DemoPill />
        </div>
      </aside>
    </>
  )
}

export function Topbar() {
  const { state, patch, toggleTheme } = useApp()
  const { t } = useI18n()
  const region = dataSource.getRegion()
  return (
    <header className="topbar">
      <button type="button" className="icon-btn menu-btn" aria-label={t('nav.open')} aria-expanded={state.navOpen} onClick={() => patch({ navOpen: !state.navOpen })}>
        <Menu size={18} />
      </button>
      <h1 className="sr-only">{t(`nav.${state.page}`)}</h1>
      <div className="topbar-context">
        <span className="topbar-eyebrow">{t('brand.product')}</span>
        <div className="topbar-titlerow">
          <span className="topbar-title">{t('brand.project')}</span>
          <span className="chip hide-sm">{region.name} · {region.country}</span>
        </div>
      </div>
      <span className="spacer" />
      <DemoPill top />
      <span className="scn">
        <Seg
          compact
          label={t('scenario.label')}
          value={state.scenario}
          onChange={(v) => patch({ scenario: v })}
          options={[
            { id: 'A', label: 'A', title: t('scenario.A.full') },
            { id: 'B', label: 'B', title: t('scenario.B.full') },
          ]}
        />
        <Tip label={t('scenario.about')}>
          <b>{t('scenario.A.full')}</b> {t('scenario.A.tip')} <b>{t('scenario.B.full')}</b> {t('scenario.B.tip')}
        </Tip>
      </span>
      <LanguageSwitch />
      <button
        type="button"
        className="icon-btn"
        onClick={toggleTheme}
        aria-label={state.theme === 'ikarus-light' ? t('theme.toDark') : t('theme.toLight')}
        title={t('theme.toggle')}
      >
        {state.theme === 'ikarus-light' ? <Moon size={18} /> : <Sun size={18} />}
      </button>
    </header>
  )
}
