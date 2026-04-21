import type { HTMLAttributes } from 'react'

/** Logro / insight: arena + texto navy (nunca texto blanco sobre arena) */
export function AchievementBadge({
  children,
  className = '',
  ...rest
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={`inline-flex items-center rounded-full bg-brand-sand px-3 py-1 font-body text-[12px] font-medium text-brand-navy ${className}`}
      {...rest}
    >
      {children}
    </span>
  )
}
