import wingUrl from '../assets/brand/ikarus-wing-white.svg'
import { useI18n } from '../i18n/useI18n'

/** Official Ikarus Aurora wing mark (reused as-is from the Ikarus Aurora brand assets, white variant for the navy sidebar). */
export function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden>
      <img src={wingUrl} alt="" />
    </span>
  )
}

export function Brand() {
  const { t } = useI18n()
  return (
    <div className="brand" role="img" aria-label={`${t('brand.name')} · ${t('brand.tagline')}`}>
      <BrandMark />
      <div aria-hidden>
        <b>{t('brand.name')}</b>
        <small>{t('brand.tagline')}</small>
      </div>
    </div>
  )
}
