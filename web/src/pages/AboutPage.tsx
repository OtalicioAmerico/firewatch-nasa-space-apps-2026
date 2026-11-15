import type { ReactNode } from 'react'
import { ArrowRight, BookOpen, ExternalLink, Info, Sprout } from 'lucide-react'
import { useApp } from '../state/AppState'
import { useI18n } from '../i18n/useI18n'
import { T } from '../i18n/Rich'
import { CONTRIBUTING_URL, GITHUB_URL, MEMBERS, REGIONS_GUIDE_URL, initials, type Member } from '../about/team'

/** External link: always a new tab, never leaks the opener; the new-tab notice is available to screen readers. */
function ExtLink({ href, className, label, children }: { href: string; className?: string; label?: string; children: ReactNode }) {
  const { t } = useI18n()
  return (
    <a href={href} className={className} target="_blank" rel="noopener noreferrer" aria-label={label ? `${label} ${t('about.team.newTab')}` : undefined}>
      {children}
      {!label && <span className="sr-only"> {t('about.team.newTab')}</span>}
    </a>
  )
}

function MemberCard({ m }: { m: Member }) {
  const { state } = useApp()
  const { t } = useI18n()
  const lang = state.lang
  const quote = m.quote[lang]
  return (
    <article className="card member" aria-labelledby={`member-${m.id}`}>
      <div className="member-head">
        <span className="avatar" aria-hidden>{initials(m.name)}</span>
        <div>
          <h3 id={`member-${m.id}`}>{m.name}</h3>
          {m.alias && <div className="muted member-alias">{m.alias}</div>}
          <ExtLink className="member-ig" href={m.instagramUrl} label={`${t('about.team.instagram', { name: m.name })}: ${m.instagramHandle}`}>
            {m.instagramHandle} <ExternalLink size={12} aria-hidden />
          </ExtLink>
        </div>
      </div>
      <blockquote className="member-quote" lang={lang}>
        {quote.map((p, i) => <p key={i}>{p}</p>)}
      </blockquote>
      {lang !== 'pt-BR' && (
        <details className="member-original">
          <summary>{t('about.team.original')}</summary>
          <blockquote lang="pt-BR">
            {m.quote['pt-BR'].map((p, i) => <p key={i}>{p}</p>)}
          </blockquote>
        </details>
      )}
    </article>
  )
}

const JOIN_ITEMS = ['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7'] as const

export function AboutPage() {
  const { go } = useApp()
  const { t } = useI18n()
  return (
    <div className="about">
      <section className="hero about-hero" aria-labelledby="about-h">
        <div className="hero-copy">
          <span className="eyebrow">{t('about.hero.eyebrow')}</span>
          <h2 id="about-h">{t('about.hero.title')}</h2>
          <p className="about-highlight">{t('about.hero.highlight')}</p>
          <p>{t('about.hero.p1')}</p>
          <p>{t('about.hero.p2')}</p>
          <p>{t('about.hero.p3')}</p>
          <div className="hero-meta">
            <span className="chip">{t('about.hero.chipRegion')}</span>
            <span className="chip">{t('about.hero.chipData')}</span>
            <span className="chip">{t('about.hero.chipMethod')}</span>
          </div>
        </div>
        <div className="hero-card">
          <div className="callout">
            <Info size={16} aria-hidden />
            <span><T k="about.hero.notice" /></span>
          </div>
        </div>
      </section>

      <section className="card about-story" aria-labelledby="about-story-h">
        <h2 id="about-story-h">{t('about.story.title')}</h2>
        <div className="about-story-grid">
          <div>
            <p>{t('about.story.p1')}</p>
            <p>{t('about.story.p2')}</p>
          </div>
          <div>
            <p>{t('about.story.p3')}</p>
            <div className="callout">
              <Info size={16} aria-hidden />
              <span>{t('about.story.note')}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="about-team" aria-labelledby="about-team-h">
        <div className="about-team-head">
          <h2 id="about-team-h">{t('about.team.title')}</h2>
          <p>{t('about.team.intro')}</p>
        </div>
        <div className="team-grid">
          {MEMBERS.map((m) => <MemberCard key={m.id} m={m} />)}
        </div>
      </section>

      <section className="card about-join" aria-labelledby="about-join-h">
        <header>
          <h2 id="about-join-h"><Sprout size={18} aria-hidden /> {t('about.join.title')}</h2>
        </header>
        <p>{t('about.join.lead')}</p>
        <ul className="bul">
          {JOIN_ITEMS.map((k) => <li key={k}><T k={`about.join.${k}`} /></li>)}
        </ul>
        <p><T k="about.join.pilot" /></p>
        <p className="about-pull">{t('about.join.quote')}</p>
        <div className="about-actions">
          <ExtLink className="btn accent" href={GITHUB_URL}>
            <ExternalLink size={16} aria-hidden /> {t('about.join.github')}
          </ExtLink>
          <ExtLink className="btn" href={CONTRIBUTING_URL}>{t('about.join.contributing')}</ExtLink>
          <ExtLink className="btn" href={REGIONS_GUIDE_URL}>{t('about.join.regions')}</ExtLink>
          <button type="button" className="btn ghost" onClick={() => go('methodology')}>
            <BookOpen size={16} aria-hidden /> {t('about.join.methodology')} <ArrowRight size={14} aria-hidden />
          </button>
        </div>
        <p className="muted about-fine">{t('about.join.note')}</p>
      </section>

      <section className="about-close" aria-labelledby="about-close-h">
        <h2 id="about-close-h" className="about-close-quote">{t('about.close.quote')}</h2>
        <p className="about-close-brand">{t('about.close.brand')}</p>
        <p className="about-close-last">{t('about.close.last')}</p>
        <p className="about-close-note">{t('about.close.note')}</p>
      </section>
    </div>
  )
}
