import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { describe, it } from 'node:test'
import { DICTS } from '../src/i18n/index.ts'
import { MEMBERS } from '../src/about/team.ts'
import { HREFLANG, PAGES, SITE, descriptionOf, jsonLd, metaTags, pageFor, robotsTxt, shellFallback, sitemapXml, staticPage, titleOf } from '../scripts/seo/site.ts'

const pt = DICTS['pt-BR']
const en = DICTS['en-US']
const CSS = '/assets/index-test.css'
const PATHS = PAGES.map((p) => p.path)

function attr(html: string, re: RegExp): string[] {
  return [...html.matchAll(re)].map((m) => m[1])
}

describe('SEO: pages and metadata', () => {
  it('has six canonical public URLs: the shell at "/" and five single .html files at the root (no directory URLs)', () => {
    assert.deepEqual(PATHS, ['/', '/en.html', '/sobre.html', '/about.html', '/metodologia.html', '/methodology.html'])
    for (const p of PATHS) assert.ok(p === '/' || /^\/[a-z-]+\.html$/.test(p), p)
    for (const p of PATHS) assert.ok(!p.includes('#') && !p.includes('?') && !/\/.+\//.test(p), p)
    assert.equal(new Set(PATHS).size, PATHS.length)
  })
  it('uses the agreed title and descriptions, and keeps them unique per page', () => {
    assert.equal(titleOf(pageFor('home', 'pt-BR')), 'Firewatch | MODIS e VIIRS — Dados NASA FIRMS')
    assert.equal(descriptionOf(pageFor('home', 'pt-BR')), 'Explore dados históricos de detecções térmicas da NASA em Tocantins, Brasil, de 2021 a 2025. Compare observações MODIS e VIIRS em mapas e calendários interativos.')
    assert.equal(descriptionOf(pageFor('home', 'en-US')), 'Explore historical NASA thermal detections in Tocantins, Brazil, from 2021 to 2025. Compare MODIS and VIIRS observations through interactive maps and calendars.')
    assert.equal(pt['app.title'], titleOf(pageFor('home', 'pt-BR')))
    assert.equal(en['app.title'], titleOf(pageFor('home', 'en-US')))
    const titles = PAGES.map(titleOf)
    const descs = PAGES.map(descriptionOf)
    assert.equal(new Set(titles).size, PAGES.length)
    assert.equal(new Set(descs).size, PAGES.length)
    for (const t of titles) assert.ok(t.length <= 75, t)
    for (const d of descs) assert.ok(d.length >= 70 && d.length <= 170, `${d.length}: ${d}`)
  })
  it('every page has canonical (absolute https, no fragment), reciprocal hreflang, Open Graph and Twitter Card, and is never noindex', () => {
    for (const p of PAGES) {
      const m = metaTags(p)
      assert.deepEqual(attr(m, /<link rel="canonical" href="([^"]+)"/g), [SITE + p.path])
      assert.ok(!/noindex|nofollow/i.test(m), p.path)
      const alts = Object.fromEntries([...m.matchAll(/<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"/g)].map((x) => [x[1], x[2]]))
      assert.equal(alts[HREFLANG['pt-BR']], SITE + pageFor(p.id, 'pt-BR').path)
      assert.equal(alts[HREFLANG['en-US']], SITE + pageFor(p.id, 'en-US').path)
      assert.equal(alts['x-default'], SITE + pageFor(p.id, 'pt-BR').path)
      assert.deepEqual(attr(m, /property="og:url" content="([^"]+)"/g), [SITE + p.path])
      assert.equal(attr(m, /property="og:title" content="([^"]+)"/g).length, 1)
      assert.equal(attr(m, /name="twitter:card" content="([^"]+)"/g)[0], 'summary')
      assert.ok(!/og:image|twitter:image/.test(m), 'no share image without a confirmed asset')
      assert.equal((m.match(/<title>/g) ?? []).length, 1)
      assert.equal((m.match(/name="description"/g) ?? []).length, 1)
    }
  })
})

describe('SEO: structured data', () => {
  it('is valid JSON-LD on the landing pages only, with documented facts and nothing invented', () => {
    for (const p of PAGES) {
      const m = metaTags(p)
      assert.equal(m.includes('application/ld+json'), p.id === 'home', p.path)
    }
    for (const lang of ['pt-BR', 'en-US'] as const) {
      const g = JSON.parse(JSON.stringify(jsonLd(lang))) as { '@graph': Record<string, unknown>[] }
      const types = g['@graph'].map((n) => n['@type'])
      assert.deepEqual(types, ['WebApplication', 'SoftwareSourceCode', 'Person'])
      const [app, code, person] = g['@graph']
      assert.equal(app.url, `${SITE}/`)
      assert.equal(app.isAccessibleForFree, true)
      assert.equal(code.codeRepository, 'https://github.com/OtalicioAmerico/firewatch-nasa-space-apps-2026')
      assert.equal(person.name, MEMBERS[0].name)
      assert.equal(person.alternateName, 'Ikarus Aurora')
      const text = JSON.stringify(g)
      assert.ok(!/aggregateRating|"review"|"award"|ratingValue|interactionStatistic|"Organization"|endors|certif/i.test(text))
    }
  })
})

describe('SEO: robots.txt and sitemap.xml', () => {
  it('robots allows crawling and points to the sitemap (and is not used as security)', () => {
    const r = robotsTxt()
    assert.match(r, /^User-agent: \*$/m)
    assert.match(r, /^Allow: \/$/m)
    assert.match(r, new RegExp(`^Sitemap: ${SITE}/sitemap\\.xml$`, 'm'))
    assert.ok(!/^Disallow:/m.test(r))
  })
  it('sitemap lists only the canonical public URLs (https, absolute, no hash routes, no data, no lastmod)', () => {
    const x = sitemapXml()
    const locs = attr(x, /<loc>([^<]+)<\/loc>/g)
    assert.deepEqual(locs, PATHS.map((p) => SITE + p))
    assert.ok(!/#|\/data\/|\/api\/|\.json|lastmod/.test(x))
    const hrefs = attr(x, /href="([^"]+)"/g)
    for (const h of hrefs) assert.ok(locs.includes(h), h)
    assert.equal(hrefs.length, PAGES.length * 3)
  })
})

describe('SEO: static pages are real HTML without JavaScript', () => {
  const pages = PAGES.filter((p) => p.path !== '/').map((p) => ({ p, html: staticPage(p, CSS) }))
  it('each has a lang attribute, exactly one h1, a skip link, landmarks and no script that loads code', () => {
    for (const { p, html } of pages) {
      assert.match(html, new RegExp(`<html lang="${p.lang}"`), p.path)
      assert.equal((html.match(/<h1[ >]/g) ?? []).length, 1, p.path)
      assert.match(html, /class="skip" href="#main"/)
      assert.ok(html.includes('<main id="main"') && html.includes('<header') && html.includes('<footer'))
      assert.ok(!/<script[^>]+src=/.test(html), 'no external script')
      assert.ok(html.includes(`<link rel="stylesheet" href="${CSS}">`))
    }
  })
  it('internal links resolve to public pages, to the interactive app or to anchors of the same page; external links are safe', () => {
    for (const { p, html } of pages) {
      for (const h of attr(html, /<a [^>]*href="([^"]+)"/g)) {
        if (h.startsWith('http')) continue
        if (h.startsWith('#')) assert.ok(html.includes(`id="${h.slice(1)}"`), `${p.path} anchor ${h}`)
        else if (h.startsWith('/#/')) assert.match(h, /^\/#\/(overview|about|methodology)\?lang=(pt-BR|en-US)$/)
        else assert.ok(PATHS.includes(h), `${p.path} -> ${h}`)
      }
      for (const a of html.match(/<a [^>]*target="_blank"[^>]*>/g) ?? []) assert.match(a, /rel="noopener noreferrer"/)
    }
  })
  it('about pages carry every testimonial in full (originals in Portuguese), names and Instagram links', () => {
    for (const lang of ['pt-BR', 'en-US'] as const) {
      const html = staticPage(pageFor('about', lang), CSS)
      for (const m of MEMBERS) {
        assert.ok(html.includes(m.name) && html.includes(m.instagramUrl) && html.includes(m.instagramHandle))
        for (const q of m.quote[lang]) assert.ok(html.includes(q.replace(/&/g, '&amp;')), `${lang}:${m.id}`)
        for (const q of m.quote['pt-BR']) assert.ok(html.includes(q), `original ${lang}:${m.id}`)
      }
    }
  })
  it('methodology pages carry every section and every limitation of the application', () => {
    for (const lang of ['pt-BR', 'en-US'] as const) {
      const html = staticPage(pageFor('method', lang), CSS)
      const d = DICTS[lang]
      for (const id of ['sensors', 'detection', 'extent', 'coverage', 'agreement', 'history']) assert.ok(html.includes(`id="${id}"`), id)
      for (const k of ['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9']) {
        const plain = d[`method.limits.${k}`].replace(/\*\*|_/g, '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        assert.ok(html.replace(/<\/?[bi]>/g, '').includes(plain), `${lang}:${k}`)
      }
      assert.match(html, /≠/)
    }
  })
  it('never promises forecasts, real-time alerts, confirmed fires or burned area, and never claims NASA endorsement', () => {
    const all = [...pages.map((x) => x.html), shellFallback(pageFor('home', 'pt-BR')), shellFallback(pageFor('home', 'en-US'))].join('\n')
    assert.ok(!/alertas? em tempo real|real-time alerts?|previs[aã]o de inc[eê]ndios|fire forecast|endorsed by NASA|endossad/i.test(all))
    // "burned area" appears in the methodology only to say what the metrics are NOT; no other page may mention it
    const others = [...pages.filter((x) => x.p.id !== 'method').map((x) => x.html), shellFallback(pageFor('home', 'pt-BR')), shellFallback(pageFor('home', 'en-US'))].join('\n')
    assert.ok(!/[aá]rea queimada|burned area/i.test(others))
    for (const x of pages.filter((y) => y.p.id === 'method')) assert.match(x.html, /não é área queimada|not burned area/)
    assert.ok(pt['seo.home.limits'].includes('Não é um produto oficial da NASA'))
    assert.ok(en['seo.home.limits'].includes('It is not an official NASA product'))
  })
})

describe('SEO: shell fallback and built output', () => {
  it('the shell fallback repeats the landing content and links to the public pages', () => {
    const f = shellFallback(pageFor('home', 'pt-BR'))
    for (const p of ['/sobre.html', '/metodologia.html', '/en.html']) assert.ok(f.includes(`href="${p}"`), p)
    assert.ok(f.includes(pt['seo.home.h1']) && f.includes(pt['seo.home.limits'].replace(/\*\*/g, '')))
  })
  const dist = 'dist'
  const built = existsSync(`${dist}/sitemap.xml`)
  it('dist (after npm run build) contains the pages, robots.txt, sitemap.xml and a shell with real metadata', { skip: !built }, () => {
    for (const p of PAGES) assert.ok(existsSync(p.path === '/' ? `${dist}/index.html` : `${dist}${p.path}`), p.path)
    for (const old of ['sobre', 'en', 'about', 'metodologia', 'methodology']) assert.ok(!existsSync(`${dist}/${old}/index.html`), `old directory URL ${old}/`)
    assert.equal(readFileSync(`${dist}/robots.txt`, 'utf8'), robotsTxt())
    assert.equal(readFileSync(`${dist}/sitemap.xml`, 'utf8'), sitemapXml())
    const shell = readFileSync(`${dist}/index.html`, 'utf8')
    assert.ok(shell.includes(`<link rel="canonical" href="${SITE}/">`))
    assert.equal((shell.match(/<title>/g) ?? []).length, 1)
    assert.equal((shell.match(/name="description"/g) ?? []).length, 1)
    assert.match(shell, /<script type="module"[^>]*src="\/assets\/index-[^"]+\.js"/)
    assert.ok(shell.includes('<div id="root">') && shell.includes('seo-fallback'))
  })
})
