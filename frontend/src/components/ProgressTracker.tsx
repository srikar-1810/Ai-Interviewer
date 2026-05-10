import { Check } from 'lucide-react'

interface ProgressTrackerProps {
  current: number
  total: number
  labels?: string[]
}

export default function ProgressTracker({ current, total, labels }: ProgressTrackerProps) {
  const steps = Array.from({ length: total }, (_, i) => i + 1)

  return (
    <div className="flex items-center">
      {steps.map((step, i) => {
        const done = step <= current
        const active = step === current
        return (
          <div key={step} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1.5">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300
                ${done ? 'bg-accent-amber text-white shadow-lg shadow-accent-amber/20' :
                  active ? 'bg-white/[0.08] text-white border border-white/[0.15]' :
                  'bg-white/[0.03] text-on-surface-dim/40 border border-white/[0.06]'}`}>
                {done ? <Check className="w-3.5 h-3.5" /> : step}
              </div>
              {labels?.[i] && (
                <span className={`text-[8px] uppercase tracking-wider whitespace-nowrap
                  ${done ? 'text-white/60' : active ? 'text-white/40' : 'text-white/15'}`}>
                  {labels[i]}
                </span>
              )}
            </div>
            {i < total - 1 && (
              <div className={`flex-1 h-[2px] mx-1.5 rounded-full transition-all duration-300
                ${done ? 'bg-accent-amber' : 'bg-white/[0.05]'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
