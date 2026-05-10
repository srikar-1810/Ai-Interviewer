interface ScoreGaugeProps {
  value: number
  label: string
  size?: 'sm' | 'md' | 'lg'
  gradient?: 'amber' | 'cyan' | 'slate'
  sublabel?: string
}

const gradients = {
  amber: { from: '#f59e0b', to: '#d97706' },
  cyan: { from: '#0891b2', to: '#0284c7' },
  slate: { from: '#64748b', to: '#475569' },
}

const sizeMap = { sm: 60, md: 84, lg: 116 }
const strokeMap = { sm: 5, md: 6, lg: 8 }

export default function ScoreGauge({ value, label, size = 'md', gradient = 'amber', sublabel }: ScoreGaugeProps) {
  const d = sizeMap[size]
  const sw = strokeMap[size]
  const r = (d - sw) / 2
  const cx = d / 2
  const cy = d / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (Math.min(value, 100) / 100) * circ
  const g = gradients[gradient]

  return (
    <div className="flex flex-col items-center gap-1.5">
      <svg width={d} height={d} viewBox={`0 0 ${d} ${d}`}>
        <defs>
          <linearGradient id={`sg-${gradient}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={g.from} />
            <stop offset="100%" stopColor={g.to} />
          </linearGradient>
          <filter id={`sgg-${gradient}`}>
            <feGaussianBlur stdDeviation="1.5" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={sw} />
        <circle
          cx={cx} cy={cy} r={r} fill="none" stroke={`url(#sg-${gradient})`} strokeWidth={sw}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          filter={`url(#sgg-${gradient})`}
          style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)' }}
        />
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
          fill="white" fontSize={d * 0.28} fontWeight="700" fontFamily="inherit">
          {value}
        </text>
      </svg>
      <span className="text-[10px] text-on-surface-dim uppercase tracking-[0.12em] font-medium">{label}</span>
      {sublabel && <span className="text-[8px] text-on-surface-dim/60">{sublabel}</span>}
    </div>
  )
}
