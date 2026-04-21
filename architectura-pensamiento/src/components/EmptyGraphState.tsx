/** Estado vacío empático — sin gamificación de puntos */
export function EmptyGraphState() {
  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-surface-card px-6 py-10 text-center font-body">
      <p className="text-[15px] leading-[1.65] text-brand-navy">
        Aún no hay conexiones — sé el primero en trazarlas.
      </p>
    </div>
  )
}
