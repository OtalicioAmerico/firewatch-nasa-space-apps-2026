/**
 * Public, crawlable pages of Firewatch (SEO). Pure functions: they return strings and touch no file.
 *
 * The app is a single-page React application with hash routes (`/#/about`), which search engines do not treat as separate
 * pages. Search engines need real URLs with real HTML. These builders generate it at build time from the SAME sources as the
 * app (the i18n dictionaries and `src/about/team.ts`), so the public pages cannot drift from the application text.
 * Nothing here is scientific content of its own: no number, result or claim is written in this file.
 */
import { DICTS, type Lang } from '../../src/i18n/index.ts'
import { CONTRIBUTING_URL, GITHUB_URL, MEMBERS, REGIONS_GUIDE_URL, initials } from '../../src/about/team.ts'

export const SITE = 'https://firewatch.ikarusaurora.tech'
export const LICENSE_URL = 'https://opensource.org/licenses/MIT'

export type PageId = 'home' | 'about' | 'method'

export interface PageDef {
  id: PageId
  lang: Lang
  /**
   * Canonical path. Either `/` (the application shell) or a single `.html` file at the root of the build. The production Caddy
   * serves a path only when it is exactly a regular file (`try_files {path} /index.html`); `/dir/` falls back to the shell.
   */
  path: string
}

export const PAGES: PageDef[] = [
  { id: 'home', lang: 'pt-BR', path: '/' },
  { id: 'home', lang: 'en-US', path: '/en.html' },
  { id: 'about', lang: 'pt-BR', path: '/sobre.html' },
  { id: 'about', lang: 'en-US', path: '/about.html' },
  { id: 'method', lang: 'pt-BR', path: '/metodologia.html' },
  { id: 'method', lang: 'en-US', path: '/methodology.html' },
]

/** hreflang value of each language (language only for English, so it also matches other English locales). */
export const HREFLANG: Record<Lang, string> = { 'pt-BR': 'pt-BR', 'en-US': 'en' }
const OG_LOCALE: Record<Lang, string> = { 'pt-BR': 'pt_BR', 'en-US': 'en_US' }

export function url(path: string): string {
  return SITE + path
}

export function pageFor(id: PageId, lang: Lang): PageDef {
  const p = PAGES.find((x) => x.id === id && x.lang === lang)
  if (!p) throw new Error(`no page ${id}/${lang}`)
  return p
}

export function tr(lang: Lang, key: string): string {
  const v = DICTS[lang][key]
  if (v === undefined) throw new Error(`missing i18n key ${lang}:${key}`)
  return v
}

export function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/** Same light markup as the app (`**bold**`, `_italic_`), after HTML-escaping, never injecting HTML. */
export function rich(text: string): string {
  return esc(text).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/(^|[^\w])_([^_]+)_/g, '$1<i>$2</i>')
}

export function titleOf(p: PageDef): string {
  return tr(p.lang, p.id === 'home' ? 'seo.home.title' : p.id === 'about' ? 'seo.about.title' : 'seo.method.title')
}

export function descriptionOf(p: PageDef): string {
  return tr(p.lang, p.id === 'home' ? 'seo.home.description' : p.id === 'about' ? 'seo.about.description' : 'seo.method.description')
}

/** Deep link into the interactive application (hash routes), keeping the language. */
export function appLink(lang: Lang, route: 'overview' | 'about' | 'methodology'): string {
  return `/#/${route}?lang=${lang}`
}

// ── structured data ──────────────────────────────────────────────────────────────────────────────────────────────────
/** schema.org graph. Only facts that are documented in the project: no ratings, users, awards, certifications or NASA endorsement. */
export function jsonLd(lang: Lang): object {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebApplication',
        '@id': `${SITE}/#webapp`,
        name: 'Firewatch',
        url: `${SITE}/`,
        description: tr(lang, 'seo.home.description'),
        applicationCategory: 'EducationalApplication',
        applicationSubCategory: lang === 'pt-BR' ? 'Exploração de dados científicos (experimental)' : 'Scientific data exploration (experimental)',
        operatingSystem: 'Any',
        browserRequirements: 'Requires JavaScript',
        isAccessibleForFree: true,
        inLanguage: ['pt-BR', 'en-US'],
        keywords: 'NASA FIRMS, MODIS, VIIRS, thermal detections, remote sensing, Tocantins, NASA Space Apps Challenge 2026',
        creator: { '@id': `${SITE}/#author` },
      },
      {
        '@type': 'SoftwareSourceCode',
        '@id': `${SITE}/#source`,
        name: 'Firewatch',
        codeRepository: GITHUB_URL,
        license: LICENSE_URL,
        programmingLanguage: ['TypeScript', 'Python'],
        creator: { '@id': `${SITE}/#author` },
        targetProduct: { '@id': `${SITE}/#webapp` },
      },
      {
        '@type': 'Person',
        '@id': `${SITE}/#author`,
        name: MEMBERS[0].name,
        alternateName: 'Ikarus Aurora',
      },
    ],
  }
}

// ── page shell ───────────────────────────────────────────────────────────────────────────────────────────────────────
function alternates(p: PageDef): string {
  const pt = pageFor(p.id, 'pt-BR')
  const en = pageFor(p.id, 'en-US')
  return [
    `<link rel="alternate" hreflang="${HREFLANG['pt-BR']}" href="${url(pt.path)}">`,
    `<link rel="alternate" hreflang="${HREFLANG['en-US']}" href="${url(en.path)}">`,
    `<link rel="alternate" hreflang="x-default" href="${url(pt.path)}">`,
  ].join('\n')
}

/** Metadata shared by every public page: title, description, canonical, hreflang, Open Graph, Twitter Card, JSON-LD (home only). */
export function metaTags(p: PageDef): string {
  const title = esc(titleOf(p))
  const desc = esc(descriptionOf(p))
  const other = p.lang === 'pt-BR' ? 'en-US' : 'pt-BR'
  const lines = [
    `<title>${title}</title>`,
    `<meta name="description" content="${desc}">`,
    `<link rel="canonical" href="${url(p.path)}">`,
    alternates(p),
    `<meta property="og:type" content="website">`,
    `<meta property="og:site_name" content="Firewatch">`,
    `<meta property="og:title" content="${title}">`,
    `<meta property="og:description" content="${desc}">`,
    `<meta property="og:url" content="${url(p.path)}">`,
    `<meta property="og:locale" content="${OG_LOCALE[p.lang]}">`,
    `<meta property="og:locale:alternate" content="${OG_LOCALE[other]}">`,
    `<meta name="twitter:card" content="summary">`,
    `<meta name="twitter:title" content="${title}">`,
    `<meta name="twitter:description" content="${desc}">`,
  ]
  if (p.id === 'home') lines.push(`<script type="application/ld+json">${JSON.stringify(jsonLd(p.lang)).replace(/</g, '\\u003c')}</script>`)
  return lines.join('\n')
}

function siteHeader(p: PageDef): string {
  const lang = p.lang
  const other = pageFor(p.id, lang === 'pt-BR' ? 'en-US' : 'pt-BR')
  const link = (id: PageId, key: string) => {
    const t = pageFor(id, lang)
    return `<a href="${t.path}"${t.path === p.path ? ' aria-current="page"' : ''}>${esc(tr(lang, key))}</a>`
  }
  return `<header class="sp-header">
<a class="sp-brand" href="${pageFor('home', lang).path}">Firewatch</a>
<nav class="sp-nav" aria-label="${esc(tr(lang, 'seo.nav.aria'))}">
${link('home', 'seo.nav.home')}
${link('about', 'seo.nav.about')}
${link('method', 'seo.nav.method')}
<a href="${GITHUB_URL}" target="_blank" rel="noopener noreferrer">${esc(tr(lang, 'seo.nav.github'))}<span class="sr-only"> ${esc(tr(lang, 'about.team.newTab'))}</span></a>
<a href="${other.path}" hreflang="${HREFLANG[other.lang]}" lang="${other.lang}">${esc(tr(lang, 'seo.nav.otherLang'))}</a>
<a class="btn accent" href="${appLink(lang, 'overview')}">${esc(tr(lang, 'seo.nav.app'))}</a>
</nav>
</header>`
}

function siteFooter(lang: Lang): string {
  return `<footer class="sp-footer"><p>${esc(tr(lang, 'about.close.note'))}</p></footer>`
}

function ext(href: string, label: string, lang: Lang, cls = 'btn'): string {
  return `<a class="${cls}" href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(label)}<span class="sr-only"> ${esc(tr(lang, 'about.team.newTab'))}</span></a>`
}

// ── page bodies ──────────────────────────────────────────────────────────────────────────────────────────────────────
/** Landing content (also the no-JavaScript fallback inside the application shell at `/`). Whole page; h1 inside the hero. */
export function homeMain(lang: Lang, h: 'h1' | 'h2' = 'h1'): string {
  const t = (k: string) => tr(lang, k)
  return `<section class="hero about-hero" aria-labelledby="home-h">
<div class="hero-copy">
<span class="eyebrow">${esc(t('about.hero.eyebrow'))}</span>
<${h} id="home-h">${esc(t('seo.home.h1'))}</${h}>
<p class="about-highlight">${esc(t('seo.home.description'))}</p>
<div class="hero-meta"><span class="chip">${esc(t('about.hero.chipRegion'))}</span><span class="chip">${esc(t('about.hero.chipData'))}</span><span class="chip">${esc(t('about.hero.chipMethod'))}</span></div>
<div class="hero-actions"><a class="btn accent" href="${appLink(lang, 'overview')}">${esc(t('seo.nav.app'))}</a> <a class="btn ghost light" href="${pageFor('method', lang).path}">${esc(t('seo.nav.method'))}</a> <a class="btn ghost light" href="${pageFor('about', lang).path}">${esc(t('seo.nav.about'))}</a></div>
</div>
<div class="hero-card"><div class="callout"><span>${rich(t('seo.home.limits'))}</span></div></div>
</section>
<section class="card" aria-labelledby="home-what-h">
<h2 id="home-what-h">${esc(t('seo.home.whatTitle'))}</h2>
<ul class="bul">
${['w1', 'w2', 'w3', 'w4'].map((k) => `<li>${rich(t('seo.home.' + k))}</li>`).join('\n')}
</ul>
</section>
<section class="card" aria-labelledby="home-src-h">
<h2 id="home-src-h">${esc(t('seo.home.sourcesTitle'))}</h2>
<p>${esc(t('seo.home.sources'))}</p>
<div class="about-actions">${ext(GITHUB_URL, t('about.join.github'), lang, 'btn accent')}${ext(CONTRIBUTING_URL, t('about.join.contributing'), lang)}${ext(REGIONS_GUIDE_URL, t('about.join.regions'), lang)}</div>
</section>`
}

/** Static twin of `AboutPage.tsx`: same classes, same dictionary keys, same member data. */
export function aboutMain(lang: Lang): string {
  const t = (k: string) => tr(lang, k)
  const member = (m: (typeof MEMBERS)[number]) => {
    const quote = m.quote[lang].map((q) => `<p>${esc(q)}</p>`).join('\n')
    const original = lang !== 'pt-BR' ? `\n<details class="member-original"><summary>${esc(t('about.team.original'))}</summary><blockquote lang="pt-BR">${m.quote['pt-BR'].map((q) => `<p>${esc(q)}</p>`).join('\n')}</blockquote></details>` : ''
    const label = `${t('about.team.instagram').replace('{name}', m.name)}: ${m.instagramHandle} ${t('about.team.newTab')}`
    return `<article class="card member" aria-labelledby="member-${m.id}">
<div class="member-head"><span class="avatar" aria-hidden="true">${esc(initials(m.name))}</span><div>
<h3 id="member-${m.id}">${esc(m.name)}</h3>
${m.alias ? `<div class="muted member-alias">${esc(m.alias)}</div>` : ''}
<a class="member-ig" href="${esc(m.instagramUrl)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(label)}">${esc(m.instagramHandle)}</a>
</div></div>
<blockquote class="member-quote" lang="${lang}">
${quote}
</blockquote>${original}
</article>`
  }
  return `<section class="hero about-hero" aria-labelledby="about-h">
<div class="hero-copy">
<span class="eyebrow">${esc(t('about.hero.eyebrow'))}</span>
<h1 id="about-h">${esc(t('about.hero.title'))}</h1>
<p class="about-highlight">${esc(t('about.hero.highlight'))}</p>
<p>${esc(t('about.hero.p1'))}</p>
<p>${esc(t('about.hero.p2'))}</p>
<p>${esc(t('about.hero.p3'))}</p>
<div class="hero-meta"><span class="chip">${esc(t('about.hero.chipRegion'))}</span><span class="chip">${esc(t('about.hero.chipData'))}</span><span class="chip">${esc(t('about.hero.chipMethod'))}</span></div>
</div>
<div class="hero-card"><div class="callout"><span>${rich(t('about.hero.notice'))}</span></div></div>
</section>
<section class="card about-story" aria-labelledby="about-story-h">
<h2 id="about-story-h">${esc(t('about.story.title'))}</h2>
<div class="about-story-grid">
<div><p>${esc(t('about.story.p1'))}</p><p>${esc(t('about.story.p2'))}</p></div>
<div><p>${esc(t('about.story.p3'))}</p><div class="callout"><span>${esc(t('about.story.note'))}</span></div></div>
</div>
</section>
<section class="about-team" aria-labelledby="about-team-h">
<div class="about-team-head"><h2 id="about-team-h">${esc(t('about.team.title'))}</h2><p>${esc(t('about.team.intro'))}</p></div>
<div class="team-grid">
${MEMBERS.map(member).join('\n')}
</div>
</section>
<section class="card about-join" aria-labelledby="about-join-h">
<h2 id="about-join-h">${esc(t('about.join.title'))}</h2>
<p>${esc(t('about.join.lead'))}</p>
<ul class="bul">
${['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7'].map((k) => `<li>${rich(t('about.join.' + k))}</li>`).join('\n')}
</ul>
<p>${rich(t('about.join.pilot'))}</p>
<p class="about-pull">${esc(t('about.join.quote'))}</p>
<div class="about-actions">${ext(GITHUB_URL, t('about.join.github'), lang, 'btn accent')}${ext(CONTRIBUTING_URL, t('about.join.contributing'), lang)}${ext(REGIONS_GUIDE_URL, t('about.join.regions'), lang)}<a class="btn ghost" href="${pageFor('method', lang).path}">${esc(t('about.join.methodology'))}</a></div>
<p class="muted about-fine">${esc(t('about.join.note'))}</p>
</section>
<section class="about-close" aria-labelledby="about-close-h">
<h2 id="about-close-h" class="about-close-quote">${esc(t('about.close.quote'))}</h2>
<p class="about-close-brand">${esc(t('about.close.brand'))}</p>
<p class="about-close-last">${esc(t('about.close.last'))}</p>
<p class="about-close-note">${esc(t('about.close.note'))}</p>
</section>`
}

const METHOD_SECTIONS: { id: string; title: string; keys: string[]; list?: string[] }[] = [
  { id: 'sensors', title: 'method.sensors.title', keys: ['method.sensors.p1'], list: ['method.sensors.b1', 'method.sensors.b2', 'method.sensors.b3'] },
  { id: 'detection', title: 'method.detection.title', keys: ['method.detection.p1', 'method.detection.p2'] },
  { id: 'extent', title: 'method.extent.title', keys: ['method.extent.p1', 'method.extent.p2'] },
  { id: 'coverage', title: 'method.coverage.title', keys: ['method.coverage.p1', 'method.coverage.p2'] },
  { id: 'agreement', title: 'method.agreement.title', keys: ['method.agreement.p1', 'method.agreement.p2'] },
  { id: 'history', title: 'method.history.title', keys: ['method.history.p1', 'method.history.p2', 'method.history.p3'] },
]
const LIMIT_KEYS = ['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9'].map((k) => `method.limits.${k}`)

/** Static twin of `MethodologyPage.tsx` (text only: the diagrams, the example buttons and the chart need the application). */
export function methodMain(lang: Lang): string {
  const t = (k: string) => tr(lang, k)
  const toc = [...METHOD_SECTIONS.map((s) => ({ id: s.id, label: t('method.nav.' + s.id) })), { id: 'limits', label: t('method.nav.limits') }]
  const sections = METHOD_SECTIONS.map(
    (s, i) => `<section id="${s.id}" class="card" aria-labelledby="${s.id}-h">
<h2 id="${s.id}-h">${i + 1} · ${esc(t(s.title))}</h2>
${s.keys.map((k) => `<p>${rich(t(k))}</p>`).join('\n')}
${s.list ? `<ul class="bul">\n${s.list.map((k) => `<li>${rich(t(k))}</li>`).join('\n')}\n</ul>` : ''}
</section>`,
  ).join('\n')
  return `<section class="card" aria-labelledby="method-h">
<span class="eyebrow">${esc(t('about.hero.eyebrow'))}</span>
<h1 id="method-h">${esc(t('seo.method.h1'))}</h1>
<p>${esc(t('seo.method.description'))}</p>
<p>${rich(t('method.navNote.REAL'))}</p>
<div class="about-actions"><a class="btn accent" href="${appLink(lang, 'methodology')}">${esc(t('seo.nav.openMethod'))}</a></div>
<nav aria-label="${esc(t('seo.nav.contents'))}"><ul class="bul">
${toc.map((x) => `<li><a href="#${x.id}">${esc(x.label)}</a></li>`).join('\n')}
</ul></nav>
</section>
${sections}
<section id="limits" class="card" aria-labelledby="limits-h">
<h2 id="limits-h">7 · ${esc(t('method.limits.title'))}</h2>
<ul class="bul">
${LIMIT_KEYS.map((k) => `<li>${rich(t(k))}</li>`).join('\n')}
</ul>
<div class="callout"><span><b>${esc(t('method.about.REAL.title'))}</b> ${esc(t('method.about.REAL.body'))}</span></div>
</section>`
}

/** Full HTML document of a static public page. `cssHref` is the hashed application stylesheet (same look as the app, no JavaScript). */
export function staticPage(p: PageDef, cssHref: string): string {
  const main = p.id === 'home' ? homeMain(p.lang) : p.id === 'about' ? aboutMain(p.lang) : methodMain(p.lang)
  return `<!doctype html>
<html lang="${p.lang}" data-theme="ikarus-light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#152238">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
${metaTags(p)}
<link rel="stylesheet" href="${cssHref}">
<script>try{var t=localStorage.getItem('nfc-theme');if(t==='ikarus-dark'||t==='ikarus-light')document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>
</head>
<body class="static-page">
<a class="skip" href="#main">${esc(tr(p.lang, 'app.skip'))}</a>
${siteHeader(p)}
<main id="main" class="content sp-content">
${main}
</main>
${siteFooter(p.lang)}
</body>
</html>
`
}

/** Fallback shown only when JavaScript is off (hidden once it runs; React replaces it on mount). Same content as the landing page. */
export function shellFallback(p: PageDef): string {
  return `<div class="seo-fallback static-page">
${siteHeader(p)}
<main class="content sp-content">
<p class="callout"><span>${esc(tr(p.lang, 'seo.home.noscript'))}</span></p>
${homeMain(p.lang, 'h1')}
</main>
${siteFooter(p.lang)}
</div>`
}

export function robotsTxt(): string {
  return `User-agent: *
Allow: /

Sitemap: ${SITE}/sitemap.xml
`
}

/** Only the canonical public pages, absolute HTTPS, with hreflang alternates. No `lastmod`: there is no verifiable per-page date. */
export function sitemapXml(): string {
  const urls = PAGES.map((p) => {
    const alts = [
      `<xhtml:link rel="alternate" hreflang="${HREFLANG['pt-BR']}" href="${url(pageFor(p.id, 'pt-BR').path)}"/>`,
      `<xhtml:link rel="alternate" hreflang="${HREFLANG['en-US']}" href="${url(pageFor(p.id, 'en-US').path)}"/>`,
      `<xhtml:link rel="alternate" hreflang="x-default" href="${url(pageFor(p.id, 'pt-BR').path)}"/>`,
    ].join('\n    ')
    return `  <url>\n    <loc>${url(p.path)}</loc>\n    ${alts}\n  </url>`
  }).join('\n')
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls}
</urlset>
`
}
