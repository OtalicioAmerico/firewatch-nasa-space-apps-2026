import { useEffect } from 'react'
import { Sidebar, Topbar } from './components/Shell'
import { DataBoundary } from './components/DataBoundary'
import { useApp } from './state/AppState'
import { useI18n } from './i18n/useI18n'
import { OverviewPage } from './pages/OverviewPage'
import { CalendarPage } from './pages/CalendarPage'
import { SpatialPage } from './pages/SpatialPage'
import { MethodologyPage } from './pages/MethodologyPage'

export default function App() {
  const { state } = useApp()
  const { t } = useI18n()
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [state.page])
  useEffect(() => {
    document.title = t('app.title')
  }, [t])
  return (
    <div className="shell">
      <a className="skip" href="#main">{t('app.skip')}</a>
      <Sidebar />
      <div className="main">
        <Topbar />
        <main id="main" className={`content${state.page === 'spatial' ? ' full' : ''}`} key={state.page}>
          <DataBoundary needs={[]} init>
            {state.page === 'overview' && <OverviewPage />}
            {state.page === 'calendar' && <CalendarPage />}
            {state.page === 'spatial' && <SpatialPage />}
            {state.page === 'methodology' && <MethodologyPage />}
          </DataBoundary>
        </main>
      </div>
    </div>
  )
}
