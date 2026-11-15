import { useMemo } from 'react'
import { ArrowRight } from 'lucide-react'
import { useApp } from '../state/AppState'
import { dataSource } from '../services'
import { useI18n } from '../i18n/useI18n'
import { T } from '../i18n/Rich'
import { Callout } from '../components/ui'
import { DataBoundary } from '../components/DataBoundary'
import { WeeklyReferenceChart } from '../components/Charts'
import { ExtentDiagram, FlowDiagram, PixelDiagram, SwathDiagram, VennDiagram } from '../components/Diagrams'
import type { ExampleStory } from '../types'

const SECTIONS = ['sensors', 'detection', 'extent', 'coverage', 'agreement', 'history', 'limits'] as const

function Example({ story, label }: { story: ExampleStory | undefined; label: string }) {
  const { go } = useApp()
  if (!story) return null
  return (
    <button type="button" className="btn sm example-btn" onClick={() => go('calendar', { date: story.date, metric: story.metric, sensor: story.sensor, selectedCellId: null })}>
      <span>{label}</span> <ArrowRight size={13} aria-hidden />
    </button>
  )
}

export function MethodologyPage() {
  const { state } = useApp()
  const { t } = useI18n()
  const mode = dataSource.mode
  const examples = useMemo(() => dataSource.getExamples(), [])
  const ex = (id: string): ExampleStory | undefined => examples.find((e) => e.id === id)
  const year = Number(state.date.slice(0, 4))
  return (
    <div className="method">
      <nav className="method-nav card" aria-label={t('method.navAria')}>
        {SECTIONS.map((id, i) => (
          <a key={id} href={`#${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }}>
            {i + 1} · {t(`method.nav.${id}`)}
          </a>
        ))}
        <div className="callout" style={{ marginTop: 8 }}>
          <span><T k={`method.navNote.${mode}`} /></span>
        </div>
      </nav>
      <div className="method-body">
        <section id="sensors" className="card">
          <header><h2>1 · {t('method.sensors.title')}</h2></header>
          <div className="two">
            <div>
              <p>{t('method.sensors.p1')}</p>
              <ul className="bul">
                <li>{t('method.sensors.b1')}</li>
                <li>{t('method.sensors.b2')}</li>
                <li>{t('method.sensors.b3')}</li>
              </ul>
              <Example story={ex('aqua-partial')} label={t('method.sensors.example')} />
            </div>
            <PixelDiagram />
          </div>
        </section>
        <section id="detection" className="card">
          <header><h2>2 · {t('method.detection.title')}</h2></header>
          <div className="two">
            <div>
              <p>{t('method.detection.p1')}</p>
              <p><T k="method.detection.p2" /></p>
            </div>
            <FlowDiagram />
          </div>
        </section>
        <section id="extent" className="card">
          <header><h2>3 · {t('method.extent.title')}</h2></header>
          <div className="two">
            <div>
              <p><T k="method.extent.p1" /></p>
              <p>{t('method.extent.p2')}</p>
              <Example story={ex('count-vs-extent')} label={t(`method.extent.example.${mode}`)} />
            </div>
            <ExtentDiagram />
          </div>
        </section>
        <section id="coverage" className="card">
          <header><h2>4 · {t('method.coverage.title')}</h2></header>
          <div className="two">
            <div>
              <p><T k="method.coverage.p1" /></p>
              <p>{t('method.coverage.p2')}</p>
              <div className="btn-row">
                <Example story={ex('incomplete')} label={t('method.coverage.exampleIncomplete')} />
                <Example story={ex('conflict')} label={t('method.coverage.exampleConflict')} />
              </div>
            </div>
            <SwathDiagram />
          </div>
        </section>
        <section id="agreement" className="card">
          <header><h2>5 · {t('method.agreement.title')}</h2></header>
          <div className="two">
            <div>
              <p><T k="method.agreement.p1" /></p>
              <p>{t('method.agreement.p2')}</p>
              <Example story={ex('agree')} label={t('method.agreement.example')} />
            </div>
            <VennDiagram />
          </div>
        </section>
        <section id="history" className="card">
          <header><h2>6 · {t('method.history.title')}</h2></header>
          <div className="two">
            <div>
              <p>{t('method.history.p1')}</p>
              <p>{t('method.history.p2')}</p>
              <p>{t('method.history.p3')}</p>
              <Example story={ex('reference')} label={t('method.history.example')} />
            </div>
            <div>
              <DataBoundary needs={[{ kind: 'year', year }]}>
                <WeeklyReferenceChart year={year} sensor="VIIRS" scenario={state.scenario} highlightWeek={26} />
              </DataBoundary>
              <p className="note" style={{ marginTop: 6 }}>{t(`method.history.chartNote.${mode}`, { year })}</p>
            </div>
          </div>
        </section>
        <section id="limits" className="card">
          <header><h2>7 · {t('method.limits.title')}</h2></header>
          <ul className="bul">
            <li><T k="method.limits.i1" /></li>
            <li><T k="method.limits.i2" /></li>
            <li><T k="method.limits.i3" /></li>
            <li><T k="method.limits.i4" /></li>
            <li><T k="method.limits.i5" /></li>
            <li><T k="method.limits.i6" /></li>
            <li>{t('method.limits.i7')}</li>
            <li>{t('method.limits.i8')}</li>
            <li>{t('method.limits.i9')}</li>
          </ul>
          <Callout title={t(`method.about.${mode}.title`)}>{t(`method.about.${mode}.body`)}</Callout>
        </section>
      </div>
    </div>
  )
}
