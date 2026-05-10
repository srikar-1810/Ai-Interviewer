import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'

interface RadarDataPoint {
  metric: string
  score: number
}

interface RadarGraphProps {
  data: RadarDataPoint[]
  color?: string
  height?: number
}

export default function RadarGraph({ data, color = '#d97706', height = 260 }: RadarGraphProps) {
  if (data.length === 0) return null

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="68%">
        <defs>
          <linearGradient id="radarFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.25} />
            <stop offset="100%" stopColor={color} stopOpacity={0.04} />
          </linearGradient>
        </defs>
        <PolarGrid stroke="rgba(255,255,255,0.05)" />
        <PolarAngleAxis dataKey="metric" tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
        <Radar
          name="Score" dataKey="score" stroke={color} strokeWidth={2}
          fill="url(#radarFill)" fillOpacity={0.6}
          dot={{ fill: color, stroke: '#0a0a0f', strokeWidth: 2, r: 3 }}
          activeDot={{ fill: color, stroke: '#0a0a0f', strokeWidth: 2, r: 5 }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
