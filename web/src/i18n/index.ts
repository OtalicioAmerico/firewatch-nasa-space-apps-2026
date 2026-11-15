/**
 * Minimal in-house i18n (no runtime dependency, see docs/RESULTADOS_MISSAO_06B.md).
 * Dictionaries are nested JSON files grouped by screen/feature; they are flattened to dotted keys.
 * Missing keys render as ⟦key⟧ so they are impossible to overlook (and are caught by the tests).
 */
import ptBR from './pt-BR.json' with { type: 'json' }
import enUS from './en-US.json' with { type: 'json' }

export type Lang = 'pt-BR' | 'en-US'
export const LANGS: Lang[] = ['pt-BR', 'en-US']
export const DEFAULT_LANG: Lang = 'pt-BR'

type Dict = { [k: string]: string | Dict }
export type Params = Record<string, string | number>

function flatten(d: Dict, prefix = '', out: Record<string, string> = {}): Record<string, string> {
  for (const [k, v] of Object.entries(d)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (typeof v === 'string') out[key] = v
    else flatten(v, key, out)
  }
  return out
}

export const DICTS: Record<Lang, Record<string, string>> = {
  'pt-BR': flatten(ptBR as Dict),
  'en-US': flatten(enUS as Dict),
}

export function parseLang(v: string | null | undefined): Lang | null {
  if (!v) return null
  const s = v.toLowerCase()
  if (s === 'pt-br' || s === 'pt') return 'pt-BR'
  if (s === 'en-us' || s === 'en') return 'en-US'
  return null
}

const plural = new Map<Lang, Intl.PluralRules>()

/** Translate `key`. With `params.count`, keys `<key>_one` / `<key>_other` are used when present. `{name}` placeholders are replaced. */
export function translate(lang: Lang, key: string, params?: Params): string {
  const dict = DICTS[lang]
  let k = key
  if (params && typeof params.count === 'number') {
    let pr = plural.get(lang)
    if (!pr) {
      pr = new Intl.PluralRules(lang)
      plural.set(lang, pr)
    }
    const cat = pr.select(params.count) === 'one' ? 'one' : 'other'
    if (`${key}_${cat}` in dict) k = `${key}_${cat}`
  }
  const raw = dict[k]
  if (raw === undefined) return `⟦${key}⟧`
  return params ? raw.replace(/\{(\w+)\}/g, (m, name: string) => (name in params ? String(params[name]) : m)) : raw
}

export type TFn = (key: string, params?: Params) => string

export const LANG_STORAGE_KEY = 'nfc-lang'

/** Language saved in the browser, or the default (pt-BR). Storage may be unavailable (private mode): never throws. */
export function readStoredLang(storage: Pick<Storage, 'getItem'> | null | undefined): Lang {
  try {
    return parseLang(storage?.getItem(LANG_STORAGE_KEY)) ?? DEFAULT_LANG
  } catch {
    return DEFAULT_LANG
  }
}

export function storeLang(storage: Pick<Storage, 'setItem'> | null | undefined, lang: Lang): void {
  try {
    storage?.setItem(LANG_STORAGE_KEY, lang)
  } catch {
    /* ignore: the preference simply is not persisted */
  }
}
