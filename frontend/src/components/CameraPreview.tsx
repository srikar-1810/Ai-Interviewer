import { useEffect, useRef, useState } from 'react'
import { Camera, CameraOff, AlertCircle, Eye, Heart, Zap, Brain, Activity } from 'lucide-react'
import { useVisualIntel, VisualMetrics, VisualHistoryEntry } from '../hooks/useVisualIntel'

interface CameraPreviewProps {
  className?: string
  autoStart?: boolean
  onMetricsUpdate?: (metrics: VisualMetrics) => void
}

function EngagementMeter({ value, label, color }: { value: number; label: string; color: string }) {
  const r = 18
  const stroke = 4
  const circ = 2 * Math.PI * r
  const offset = circ - (Math.min(value, 99) / 100) * circ
  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className="relative" style={{ width: (r + stroke) * 2, height: (r + stroke) * 2 }}>
        <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${(r + stroke) * 2} ${(r + stroke) * 2}`}>
          <circle cx={r + stroke} cy={r + stroke} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
          <circle cx={r + stroke} cy={r + stroke} r={r} fill="none" stroke="currentColor" strokeWidth={stroke}
            strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" className={color} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-[9px] font-bold ${color.replace('stroke-', 'text-')}`}>{value}</span>
        </div>
      </div>
      <span className="text-[7px] text-white/50 uppercase tracking-wider">{label}</span>
    </div>
  )
}

function MiniSparkline({ data, color = 'stroke-accent-amber' }: { data: VisualHistoryEntry[]; color?: string }) {
  if (data.length < 2) return null
  const values = data.map(d => d.engagement)
  const max = Math.max(...values, 1)
  const h = 20; const w = 60
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - (v / max) * h}`).join(' ')
  return (
    <svg width={w} height={h} className="shrink-0">
      <polyline fill="none" stroke="currentColor" strokeWidth="1.5" points={pts} className={color} />
    </svg>
  )
}

function ScoreBar({ label, value, icon: Icon, color }: { label: string; value: number; icon: any; color: string }) {
  const barColor = value >= 70 ? 'bg-accent-amber' : value >= 45 ? 'bg-accent-amber' : 'bg-accent-rose'
  return (
    <div className="flex items-center gap-2">
      <Icon className={`w-3 h-3 ${color} shrink-0`} />
      <div className="flex-1 min-w-0">
        <div className="flex justify-between text-[8px] text-white/50 mb-0.5">
          <span>{label}</span>
          <span>{value}</span>
        </div>
        <div className="h-1 bg-white/[0.06] rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${barColor} transition-all duration-300`} style={{ width: `${value}%` }} />
        </div>
      </div>
    </div>
  )
}

export default function CameraPreview({ className = '', autoStart = false, onMetricsUpdate }: CameraPreviewProps) {
  const [error, setError] = useState<string | null>(null)
  const [isActive, setIsActive] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [showDashboard, setShowDashboard] = useState(true)
  const videoRef = useRef<HTMLVideoElement | null>(null)

  const { metrics, isAnalyzing, start: startIntel, stop: stopIntel, history } = useVisualIntel({
    interval: 2500,
    enabled: autoStart && isActive,
  })

  const prevMetricsRef = useRef(metrics)
  useEffect(() => {
    if (onMetricsUpdate && metrics !== prevMetricsRef.current) {
      prevMetricsRef.current = metrics
      onMetricsUpdate(metrics)
    }
  }, [metrics, onMetricsUpdate])

  const setVideoRef = (el: HTMLVideoElement | null) => {
    videoRef.current = el
    if (el && isActive && stream) el.srcObject = stream
  }

  const startCamera = async () => {
    setIsStarting(true); setError(null)
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: 'user' },
        audio: false,
      })
      setStream(mediaStream); setIsActive(true)
    } catch (err: any) {
      if (err.name === 'NotAllowedError') setError('Camera access denied.')
      else setError('Could not access camera.')
    } finally { setIsStarting(false) }
  }

  const stopCamera = () => {
    stream?.getTracks().forEach(t => t.stop())
    if (videoRef.current) videoRef.current.srcObject = null
    setStream(null); setIsActive(false); stopIntel()
  }

  useEffect(() => { if (isActive && stream && videoRef.current) videoRef.current.srcObject = stream }, [isActive, stream])
  useEffect(() => {
    if (isActive && stream && videoRef.current) {
      const video = videoRef.current
      const onMeta = () => startIntel(video)
      if (video.readyState >= 1) onMeta()
      else video.addEventListener('loadeddata', onMeta, { once: true })
      return () => { video.removeEventListener('loadeddata', onMeta) }
    }
  }, [isActive, stream, startIntel])
  useEffect(() => { if (autoStart) startCamera(); return () => stopCamera() }, [autoStart])

  const exprLabel = !metrics.faceDetected ? '--' : metrics.dominantExpression.charAt(0).toUpperCase() + metrics.dominantExpression.slice(1)
  const exprColor = !metrics.faceDetected ? 'text-white/50' : metrics.dominantExpression === 'positive' ? 'text-accent-amber' : metrics.dominantExpression === 'negative' ? 'text-accent-rose' : 'text-accent-amber'

  return (
    <div className={`relative rounded-2xl overflow-hidden bg-black/40 ${className}`}>
      {!isActive ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
          {error ? (
            <>
              <AlertCircle className="w-10 h-10 text-accent-rose mb-3" />
              <p className="text-sm text-accent-rose mb-3 font-medium">{error}</p>
              <button onClick={startCamera} className="btn-secondary text-sm">Try Again</button>
            </>
          ) : (
            <>
              <div className="w-14 h-14 rounded-full bg-white/[0.04] flex items-center justify-center mb-3">
                <Camera className="w-6 h-6 text-on-surface-dim" />
              </div>
              <h4 className="font-medium text-on-surface mb-1">Camera Off</h4>
              <p className="text-xs text-on-surface-dim mb-4 max-w-[200px]">AI analyzes eye contact, expression, posture & engagement</p>
              <button onClick={startCamera} disabled={isStarting} className="btn-primary text-sm">
                {isStarting ? 'Starting...' : 'Enable Camera'}
              </button>
            </>
          )}
        </div>
      ) : (
        <>
          <video ref={setVideoRef} autoPlay playsInline muted className="w-full h-full object-cover mirror bg-black" />

          <div className="absolute top-0 left-0 right-0 p-3 flex items-center justify-between bg-gradient-to-b from-black/60 to-transparent pointer-events-none">
            <div className="flex items-center gap-2">
              <div className={`px-2 py-1 rounded text-[9px] backdrop-blur-sm flex items-center gap-1.5
                ${metrics.faceDetected ? 'bg-accent-amber/20 text-accent-amber' : 'bg-accent-rose/20 text-accent-rose'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${isAnalyzing ? 'animate-pulse bg-accent-amber' : metrics.faceDetected ? 'bg-accent-amber' : 'bg-accent-rose'}`} />
                {isAnalyzing ? 'ANALYZING' : metrics.faceDetected ? 'FACE' : 'NO FACE'}
              </div>
              {metrics.blinkDetected && (
                <div className="px-2 py-1 bg-accent-cyan/20 text-accent-cyan rounded text-[9px] backdrop-blur-sm">BLINK</div>
              )}
            </div>
            <div className="flex items-center gap-2 pointer-events-auto">
              <button onClick={() => setShowDashboard(!showDashboard)}
                className={`px-2 py-1 rounded text-[9px] backdrop-blur-sm border transition-all
                  ${showDashboard ? 'bg-accent-amber/20 text-accent-amber border-accent-amber/20' : 'bg-black/40 text-white/50 border-white/10 hover:bg-black/60'}`}>
                {showDashboard ? 'Hide' : 'Metrics'}
              </button>
              <button onClick={stopCamera} className="p-1.5 bg-black/50 hover:bg-black/70 text-white/70 rounded-lg backdrop-blur-sm transition-all border border-white/10 pointer-events-auto" title="Turn off camera">
                <CameraOff className="w-3 h-3" />
              </button>
            </div>
          </div>

          {showDashboard && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent p-3 pt-8">
              <div className="flex items-start gap-4">
                <div className="flex gap-2">
                  <EngagementMeter value={metrics.engagementScore} label="ENG" color="stroke-accent-amber" />
                  <EngagementMeter value={metrics.eyeContactPct} label="EYE" color="stroke-accent-cyan" />
                  <EngagementMeter value={metrics.attentionScore} label="FOCUS" color="stroke-accent-amber" />
                  <EngagementMeter value={metrics.uprightPosturePct} label="POST" color="stroke-accent-amber" />
                  <EngagementMeter value={metrics.smileConfidence} label="SMILE" color="stroke-accent-amber" />
                </div>

                <div className="flex-1 space-y-1 min-w-0">
                  <ScoreBar label="Eye Contact" value={metrics.eyeContactPct} icon={Eye} color="text-accent-cyan" />
                  <ScoreBar label="Engagement" value={metrics.engagementScore} icon={Zap} color="text-accent-amber" />
                  <ScoreBar label="Attention" value={metrics.attentionScore} icon={Brain} color="text-accent-amber" />
                  <ScoreBar label="Stress" value={metrics.stressLevel} icon={Heart} color="text-accent-rose" />

                  <div className="flex items-center gap-2 pt-0.5">
                    <Activity className="w-3 h-3 text-white/30" />
                    <MiniSparkline data={history} />
                    <span className="text-[7px] text-white/30">{history.length > 0 ? `${metrics.blinkRate}/min` : ''}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-1.5 mt-2 flex-wrap">
                <span className={`px-1.5 py-0.5 rounded text-[7px] backdrop-blur-sm ${exprColor} bg-black/30`}>
                  {metrics.faceDetected ? exprLabel : 'NO FACE'}
                </span>
                <span className="px-1.5 py-0.5 rounded text-[7px] bg-black/30 text-white/50 backdrop-blur-sm">
                  {metrics.headMovementVelocity.toFixed(1)}°/s
                </span>
                {metrics.smileConfidence > 60 && (
                  <span className="px-1.5 py-0.5 rounded text-[7px] bg-accent-amber/20 text-accent-amber backdrop-blur-sm">Smiling</span>
                )}
                {metrics.stressLevel > 60 && (
                  <span className="px-1.5 py-0.5 rounded text-[7px] bg-accent-rose/20 text-accent-rose backdrop-blur-sm">Stress</span>
                )}
                {metrics.nervousnessIndicator > 50 && (
                  <span className="px-1.5 py-0.5 rounded text-[7px] bg-orange-500/20 text-orange-300 backdrop-blur-sm">Nervous</span>
                )}
              </div>
            </div>
          )}
        </>
      )}
      <style>{`.mirror { transform: scaleX(-1); }`}</style>
    </div>
  )
}
