import { Fragment, type ReactNode } from 'react'
import { useI18n } from './useI18n'
import type { Params } from './index'

/** Renders a translated string with light markup: **bold** and _italic_ (no HTML is ever injected). */
export function richText(text: string): ReactNode[] {
  const out: ReactNode[] = []
  const re = /(\*\*[^*]+\*\*|_[^_]+_)/g
  let last = 0
  let m: RegExpExecArray | null
  let k = 0
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(<Fragment key={k++}>{text.slice(last, m.index)}</Fragment>)
    const tok = m[0]
    out.push(tok.startsWith('**') ? <b key={k++}>{tok.slice(2, -2)}</b> : <i key={k++}>{tok.slice(1, -1)}</i>)
    last = m.index + tok.length
  }
  if (last < text.length) out.push(<Fragment key={k++}>{text.slice(last)}</Fragment>)
  return out
}

export function T({ k, params }: { k: string; params?: Params }) {
  const { t } = useI18n()
  return <>{richText(t(k, params))}</>
}
