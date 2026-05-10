interface SkeletonProps {
  className?: string
  count?: number
}

export function Skeleton({ className = 'skeleton-text', count = 1 }: SkeletonProps) {
  if (count === 1) return <div className={className} />
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={className} />
      ))}
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-3">
        <div className="skeleton h-10 w-10 rounded-lg" />
        <div className="space-y-2 flex-1">
          <div className="skeleton h-4 w-1/3 rounded" />
          <div className="skeleton h-3 w-1/2 rounded" />
        </div>
      </div>
      <div className="skeleton h-20 w-full rounded-lg" />
      <div className="flex gap-2">
        <div className="skeleton h-6 w-16 rounded-full" />
        <div className="skeleton h-6 w-20 rounded-full" />
      </div>
    </div>
  )
}

export function SkeletonPage() {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="space-y-3">
        <div className="skeleton h-8 w-64 rounded-lg" />
        <div className="skeleton h-4 w-96 rounded" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </div>
  )
}
