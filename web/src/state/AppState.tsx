import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, type ReactNode } from 'react'
import { BASE, parseHash, toHash, type AppState, type PageId, type Theme } from './model'
import { readStoredLang, storeLang, type Lang } from '../i18n'

export type { AppState, PageId, Theme } from './model'

type Action =
  | { type: 'go'; page: PageId; patch?: Partial<AppState> }
  | { type: 'patch'; patch: Partial<AppState> }
  | { type: 'selectDate'; date: string }

function reducer(s: AppState, a: Action): AppState {
  switch (a.type) {
    case 'go':
      return { ...s, ...a.patch, page: a.page, navOpen: false }
    case 'patch':
      return { ...s, ...a.patch }
    case 'selectDate':
      return { ...s, date: a.date, selectedCellId: null }
  }
}

function initialLang(): Lang {
  return readStoredLang(typeof localStorage === 'undefined' ? null : localStorage)
}

function initialTheme(): Theme {
  try {
    const t = localStorage.getItem('nfc-theme')
    if (t === 'ikarus-dark' || t === 'ikarus-light') return t
  } catch {
    /* storage unavailable: default to light */
  }
  return 'ikarus-light'
}

interface Ctx {
  state: AppState
  go: (page: PageId, patch?: Partial<AppState>) => void
  patch: (patch: Partial<AppState>) => void
  selectDate: (date: string) => void
  toggleTheme: () => void
  setLang: (lang: Lang) => void
}

const AppCtx = createContext<Ctx | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, () => {
    const base = { ...BASE, theme: initialTheme(), lang: initialLang() }
    return parseHash(window.location.hash, base)
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', state.theme)
    try {
      localStorage.setItem('nfc-theme', state.theme)
    } catch {
      /* ignore */
    }
  }, [state.theme])

  useEffect(() => {
    document.documentElement.setAttribute('lang', state.lang)
    storeLang(typeof localStorage === 'undefined' ? null : localStorage, state.lang)
  }, [state.lang])

  useEffect(() => {
    const h = toHash(state)
    if (window.location.hash !== h) window.history.replaceState(null, '', h)
  }, [state])

  useEffect(() => {
    const onHash = () => dispatch({ type: 'patch', patch: parseHash(window.location.hash, state) })
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [state])

  const go = useCallback((page: PageId, patch?: Partial<AppState>) => dispatch({ type: 'go', page, patch }), [])
  const patch = useCallback((p: Partial<AppState>) => dispatch({ type: 'patch', patch: p }), [])
  const selectDate = useCallback((date: string) => dispatch({ type: 'selectDate', date }), [])
  const toggleTheme = useCallback(() => dispatch({ type: 'patch', patch: { theme: state.theme === 'ikarus-light' ? 'ikarus-dark' : 'ikarus-light' } }), [state.theme])

  const setLang = useCallback((lang: Lang) => dispatch({ type: 'patch', patch: { lang } }), [])
  const value = useMemo(() => ({ state, go, patch, selectDate, toggleTheme, setLang }), [state, go, patch, selectDate, toggleTheme, setLang])
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>
}

export function useApp(): Ctx {
  const c = useContext(AppCtx)
  if (!c) throw new Error('useApp outside AppProvider')
  return c
}
