import type { ReactNode } from 'react'

type Props = {
  title: string
  subtitle?: string
  children: ReactNode
}

/** Shell: navy + texto blanco; contenido en surface.base */
export function AppShell({ title, subtitle, children }: Props) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="bg-brand-navy px-6 py-6 text-white">
        <p className="font-body text-[12px] font-medium uppercase tracking-wider text-white/70">
          Arquitectura de Pensamiento
        </p>
        <h1 className="font-display text-display text-white">{title}</h1>
        {subtitle ? (
          <p className="mt-2 max-w-2xl font-body text-[15px] leading-[1.65] text-white/85">
            {subtitle}
          </p>
        ) : null}
      </header>
      <main className="flex-1 bg-surface-base px-4 py-8 sm:px-8 md:px-10">
        <div className="mx-auto max-w-5xl">{children}</div>
      </main>
    </div>
  )
}
