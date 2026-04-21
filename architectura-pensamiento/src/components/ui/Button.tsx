import type { ButtonHTMLAttributes } from 'react'

type ButtonVariant = 'primary' | 'secondary'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
}

/** CTA primario: esmeralda. Secundario: contorno navy. Sin Playfair en UI. */
export function Button({
  variant = 'primary',
  className = '',
  children,
  ...rest
}: Props) {
  const base =
    'font-body font-medium text-[15px] leading-snug rounded-lg px-4 py-2.5 transition ' +
    'focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-brand-emerald ' +
    'disabled:opacity-50 disabled:pointer-events-none'
  const styles =
    variant === 'primary'
      ? 'bg-brand-emerald text-white border-2 border-brand-emerald hover:brightness-105'
      : 'bg-transparent text-brand-navy border-2 border-brand-navy hover:bg-surface-card'
  return (
    <button type="button" className={`${base} ${styles} ${className}`} {...rest}>
      {children}
    </button>
  )
}
