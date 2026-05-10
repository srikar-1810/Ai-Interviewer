import { AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area } from 'recharts'

interface DataPoint {
  label: string
  value: number
}

interface ScoreGraphProps {
  data: DataPoint[]
  color?: string
  height?: number
}

export default function ScoreGraph({ data, color = '#d97706', height = 160 }: ScoreGraphProps) {
  if (data.length < 2) return null

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
        <defs>
          <linearGradient id={`area-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.2} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis dataKey="label" tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 10 }} domain={[0, 100]} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{
            background: 'rgba(10,10,15,0.95)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '12px',
            backdropFilter: 'blur(20px)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          }}
          labelStyle={{ color: 'rgba(255,255,255,0.6)', fontSize: 11 }}
          itemStyle={{ color: '#fff', fontSize: 13, fontWeight: 600 }}
        />
        <Area
          type="monotone" dataKey="value" stroke={color} strokeWidth={2}
          fill={`url(#area-${color.replace('#', '')})`}
          dot={{ fill: color, stroke: '#0a0a0f', strokeWidth: 2, r: 3 }}
          activeDot={{ fill: color, stroke: '#0a0a0f', strokeWidth: 2, r: 5 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
