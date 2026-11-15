import assert from 'node:assert/strict'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, it } from 'node:test'
import { DEFAULT_LANG, DICTS, LANGS, parseLang, readStoredLang, storeLang, translate } from '../src/i18n/index.ts'
import { makeFormatters } from '../src/i18n/format.ts'
import { BASE, parseHash, toHash } from '../src/state/model.ts'

const pt = DICTS['pt-BR']
const en = DICTS['en-US']

function sources(dir: string, out: string[] = []): string[] {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f)
    if (statSync(p).isDirectory()) sources(p, out)
    else if (/\.tsx?$/.test(f) && !p.includes(join('src', 'mock')) && !p.includes(join('src', 'i18n'))) out.push(p)
  }
  return out
}

describe('language selection', () => {
  it('Portuguese (Brazil) is the default', () => {
    assert.equal(DEFAULT_LANG, 'pt-BR')
    assert.equal(BASE.lang, 'pt-BR')
    assert.equal(readStoredLang(null), 'pt-BR')
    assert.equal(readStoredLang({ getItem: () => null }), 'pt-BR')
    assert.deepEqual(LANGS, ['pt-BR', 'en-US'])
  })
  it('persists the preference and survives unavailable storage', () => {
    const mem = new Map<string, string>()
    const storage = { getItem: (k: string) => mem.get(k) ?? null, setItem: (k: string, v: string) => void mem.set(k, v) }
    storeLang(storage, 'en-US')
    assert.equal(readStoredLang(storage), 'en-US')
    const broken = { getItem: () => { throw new Error('blocked') }, setItem: () => { throw new Error('blocked') } }
    assert.equal(readStoredLang(broken), 'pt-BR')
    assert.doesNotThrow(() => storeLang(broken, 'en-US'))
  })
  it('switching language keeps date, filters, scenario and selected cell', () => {
    const s = { ...BASE, page: 'spatial' as const, date: '2023-06-08', sensor: 'VIIRS' as const, metric: 'intensity' as const, scenario: 'A' as const, selectedCellId: 'g0.25_-40_-192', lang: 'pt-BR' as const }
    const back = parseHash(toHash({ ...s, lang: 'en-US' }), { ...BASE, lang: 'pt-BR' })
    assert.equal(back.lang, 'en-US')
    for (const k of ['page', 'date', 'sensor', 'metric', 'scenario', 'selectedCellId'] as const) assert.equal(back[k], s[k], k)
    assert.equal(parseLang('en'), 'en-US')
    assert.equal(parseHash('#/overview?lang=xx', BASE).lang, 'pt-BR')
  })
})

describe('dictionaries', () => {
  it('have exactly the same keys', () => {
    assert.deepEqual(Object.keys(pt).sort(), Object.keys(en).sort())
  })
  it('every key used by the source code resolves in both languages', () => {
    const missing: string[] = []
    for (const p of sources('src')) {
      const s = readFileSync(p, 'utf8')
      const keys = new Set<string>()
      for (const m of s.matchAll(/\bt\(\s*'([^']+)'/g)) keys.add(m[1])
      for (const m of s.matchAll(/\bk="([^"]+)"/g)) keys.add(m[1])
      for (const m of s.matchAll(/keys=\{\[([^\]]+)\]\}/g)) for (const k of m[1].matchAll(/'([^']+)'/g)) keys.add(k[1])
      for (const k of keys) {
        const base = k
        if (!(base in pt) && !(`${base}_other` in pt)) missing.push(`pt:${k}`)
        if (!(base in en) && !(`${base}_other` in en)) missing.push(`en:${k}`)
      }
    }
    assert.deepEqual(missing, [])
  })
  it('dynamic key families are complete', () => {
    const fam: string[] = []
    for (const s of ['CORROBORATED', 'PARTIAL', 'INDETERMINATE', 'NO_COVERAGE_CORROBORATED']) fam.push(`coverage.${s}.label`, `coverage.${s}.tip`)
    for (const c of ['BOTH', 'MODIS_ONLY', 'VIIRS_ONLY', 'UNCERTAIN', 'NONE']) fam.push(`category.${c}.label`, `category.${c}.short`, `evidence.why.${c}`)
    for (const r of ['ABOVE', 'WITHIN', 'BELOW', 'INSUFFICIENT', 'NO_DATA']) fam.push(`ref.${r}.short`, `ref.${r}.label`)
    for (const r of ['INSUFFICIENT_COVERAGE', 'NO_ACTIVE_CELLS']) fam.push(`comparison.reason.${r}`)
    for (const f of ['AQUA', 'TERRA', 'N20']) for (const k of ['PARTIAL', 'INCOMPLETE', 'CONFLICT']) fam.push(`flags.${f}_${k}`)
    for (const m of ['MOCK', 'REAL']) {
      fam.push(`mode.${m}.label`, `mode.${m}.note`, `evidence.limits.body.${m}`, `method.about.${m}.body`)
      for (const id of ['count-vs-extent', 'agree', 'conflict', 'incomplete', 'aqua-partial', 'reference']) fam.push(`examples.${m}.${id}.title`, `examples.${m}.${id}.summary`, `examples.${m}.${id}.lesson`)
    }
    for (const id of ['extent-vs-count']) fam.push(`examples.REAL.${id}.title`)
    for (const m of ['extent', 'intensity', 'detections', 'concordance']) fam.push(`metric.${m}.label`, `metric.${m}.help`)
    const bad = fam.filter((k) => !(k in pt) || !(k in en))
    assert.deepEqual(bad, [])
  })
  it('missing keys are visible, never silent', () => {
    assert.equal(translate('pt-BR', 'no.such.key'), '⟦no.such.key⟧')
  })
  it('long Portuguese texts are really translated', () => {
    const same = Object.keys(en).filter((k) => en[k].length > 30 && en[k] === pt[k])
    assert.deepEqual(same, [])
  })
  it('interpolates parameters and plurals', () => {
    assert.equal(translate('pt-BR', 'day.refYears', { count: 1, n: 1 }), '1 ano de referência')
    assert.equal(translate('pt-BR', 'day.refYears', { count: 3, n: 3 }), '3 anos de referência')
    assert.equal(translate('en-US', 'day.refYears', { count: 1, n: 1 }), '1 reference year')
  })
})

describe('scientific terminology', () => {
  it('uses the agreed Portuguese terms', () => {
    assert.equal(pt['metric.extent.label'], 'Extensão espacial')
    assert.equal(pt['metric.intensity.label'], 'Intensidade de detecções')
    assert.equal(pt['metric.detections.label'], 'Detecções brutas')
    assert.equal(pt['category.MODIS_ONLY.label'], 'Somente MODIS')
    assert.equal(pt['category.VIIRS_ONLY.label'], 'Somente VIIRS')
    assert.equal(pt['category.UNCERTAIN.label'], 'Cobertura incerta')
    assert.equal(pt['common.comparable'], 'Comparável')
    assert.equal(pt['common.notComparable'], 'Não comparável')
    assert.equal(pt['ref.INSUFFICIENT.short'], 'Referência histórica insuficiente')
    assert.equal(pt['ref.ABOVE.short'], 'Acima da referência disponível')
    assert.equal(pt['ref.BELOW.short'], 'Abaixo da referência disponível')
    assert.equal(pt['nav.calendar'], 'Calendário histórico')
  })
  it('mode banners match the required wording', () => {
    assert.equal(pt['mode.MOCK.label'], 'DEMONSTRAÇÃO · DADOS SIMULADOS')
    assert.equal(pt['mode.REAL.label'], 'ANÁLISE EXPERIMENTAL · DADOS NASA')
    assert.equal(en['mode.MOCK.label'], 'DEMO MODE · SIMULATED DATA')
  })
  it('keeps the essential scientific warnings in both languages', () => {
    assert.match(pt['method.limits.i1'], /Detecção térmica ≠ incêndio confirmado/)
    assert.match(en['method.limits.i1'], /Thermal detection ≠ confirmed fire/)
    for (const k of ['i2', 'i3', 'i4', 'i5', 'i6']) assert.ok(pt[`method.limits.${k}`].includes('≠') && en[`method.limits.${k}`].includes('≠'))
    for (const lang of [pt, en]) for (const k of Object.keys(lang)) assert.ok(!/\bfogo confirmado\b|\bconfirmed burn\b/i.test(lang[k]), k)
    for (const t of ['MODIS', 'VIIRS', 'NASA FIRMS', 'CMR', 'FRP']) assert.ok(Object.values(pt).some((v) => v.includes(t)), t)
  })
})

describe('formatting (Intl, UTC days)', () => {
  const p = makeFormatters('pt-BR')
  const e = makeFormatters('en-US')
  it('numbers and percentages follow the locale', () => {
    assert.equal(p.num(1038), '1.038')
    assert.equal(e.num(1038), '1,038')
    assert.equal(p.pct(0.216), '21,6%')
    assert.equal(e.pct(0.216), '21.6%')
    assert.equal(p.dec(0.42, 2), '0,42')
    assert.equal(e.num(null), '—')
  })
  it('dates and months are translated and never shifted by the time zone', () => {
    assert.equal(p.date('2024-07-19'), '19/07/2024')
    assert.equal(e.date('2024-07-19'), 'Jul 19, 2024')
    assert.equal(p.date('2024-01-01'), '01/01/2024')
    assert.equal(e.date('2025-12-31'), 'Dec 31, 2025')
    assert.match(p.dateLong('2024-07-19'), /sex/i)
    assert.equal(p.monthLong(7).toLowerCase(), 'julho')
    assert.equal(e.monthLong(7), 'July')
    assert.equal(p.monthShort(3).toLowerCase(), 'mar')
    assert.equal(p.monthYear(2024, 9), 'Setembro 2024')
    assert.equal(p.weekdayShort(0).toLowerCase(), 'seg')
    assert.equal(e.weekdayShort(0), 'Mon')
  })
})
