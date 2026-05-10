import { useRef, useEffect } from 'react'

interface AudioVisualizerProps {
  isActive: boolean
  barCount?: number
  height?: number
  color?: string
}

export default function AudioVisualizer({ isActive, barCount = 48, height = 48, color = '#d97706' }: AudioVisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const bars = containerRef.current.querySelectorAll<HTMLDivElement>('.wave-bar')
    if (!isActive) {
      bars.forEach(b => { b.style.height = '3px' })
      return
    }
    let frame: number
    const animate = () => {
      bars.forEach(bar => {
        const h = Math.random() * height * 0.75 + 2
        bar.style.height = `${h}px`
      })
      frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [isActive, height])

  return (
    <div ref={containerRef} className="flex items-center gap-[2px]" style={{ height }}>
      {Array.from({ length: barCount }).map((_, i) => {
        const fade = i < 4 ? (i + 1) / 5 : i > barCount - 5 ? (barCount - i) / 5 : 1
        return (
          <div
            key={i}
            className="wave-bar rounded-full transition-all duration-75"
            style={{
              width: Math.max(2, (height / barCount) * 1.2),
              height: '3px',
              background: color,
              opacity: 0.2 + fade * 0.8,
              borderRadius: '1px',
            }}
          />
        )
      })}
    </div>
  )
}
