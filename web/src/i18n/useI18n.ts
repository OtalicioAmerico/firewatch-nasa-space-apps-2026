import { useMemo } from 'react'
import { useApp } from '../state/AppState'
import { translate, type Lang, type Params, type TFn } from './index'
import { makeFormatters, type Formatters } from './format'

export interface I18n {
  lang: Lang
  t: TFn
  f: Formatters
}

/** Translation function and locale formatters bound to the language chosen in the interface. */
export function useI18n(): I18n {
  const { state } = useApp()
  return useMemo(() => ({ lang: state.lang, t: (key: string, params?: Params) => translate(state.lang, key, params), f: makeFormatters(state.lang) }), [state.lang])
}
