import { useEffect, useState, type ReactNode } from 'react'
import { Database, LoaderCircle } from 'lucide-react'
import { dataSource, type Need } from '../services'
import { useI18n } from '../i18n/useI18n'
import { Empty } from './ui'

/**
 * Renders its children only when the data they read is available. Data that is not bundled is fetched on demand
 * (year, cells of the month, detections of the month). If it cannot be loaded the unavailability is shown;
 * no value is ever invented to fill the gap.
 */
export function DataBoundary({ needs, children, init = false }: { needs: Need[]; children: ReactNode; init?: boolean }) {
  const { t } = useI18n()
  const [, setTick] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [inited, setInited] = useState(!init)
  const key = JSON.stringify(needs)
  const ready = inited && needs.every((n) => dataSource.isReady(n))

  useEffect(() => {
    let alive = true
    setError(null)
    const run = async () => {
      if (init) {
        await dataSource.init()
        if (alive) setInited(true)
      }
      await Promise.all(needs.filter((n) => !dataSource.isReady(n)).map((n) => dataSource.ensure(n)))
      if (alive) setTick((x) => x + 1)
    }
    run().catch((e: unknown) => {
      if (alive) setError(e instanceof Error ? e.message : String(e))
    })
    return () => {
      alive = false
    }
    // `needs` is represented by `key`
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, attempt, init])

  if (error) {
    return (
      <Empty icon={<Database size={28} aria-hidden />} title={t('data.unavailable.title')}>
        {t('data.unavailable.body')} <span className="mono">{error}</span>{' '}
        <button type="button" className="btn sm" onClick={() => setAttempt((a) => a + 1)}>
          {t('common.retry')}
        </button>
      </Empty>
    )
  }
  if (!ready) {
    return (
      <div className="empty" role="status" aria-live="polite">
        <LoaderCircle size={22} className="spin" aria-hidden />
        <b>{t('data.loading')}</b>
      </div>
    )
  }
  return <>{children}</>
}
