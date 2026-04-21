import type { HTMLAttributes } from 'react'

/** Alertas: coral + texto navy */
export function AlertBanner({
  children,
  className = '',
  ...rest
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="alert"
      className={`rounded-lg border border-brand-coral/40 bg-brand-coral px-4 py-3 font-body text-[14px] text-brand-navy ${className}`}
      {...rest}
    >
      {children}
    </div>
  )
}
