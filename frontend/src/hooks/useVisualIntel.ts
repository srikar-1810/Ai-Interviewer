import { useState, useRef, useCallback, useEffect } from 'react'
import { api } from '../lib/api'

export interface VisualMetrics {
  eyeContactPct: number
  positiveExpressionPct: number
  neutralExpressionPct: number
  negativeExpressionPct: number
  uprightPosturePct: number
  engagementScore: number
  stressLevel: number
  nervousnessIndicator: number
  dominantExpression: string
  faceDetected: boolean
  smileConfidence: number
  attentionScore: number
  headYaw: number
  headPitch: number
  headRoll: number
  headMovementVelocity: number
  blinkDetected: boolean
  blinkRate: number
  expressionConfidence: number
}

export interface VisualHistoryEntry {
  time: number
  eyeContact: number
  engagement: number
  attention: number
  posture: number
  stress: number
}

const DEFAULT_METRICS: VisualMetrics = {
  eyeContactPct: 0, positiveExpressionPct: 0, neutralExpressionPct: 0,
  negativeExpressionPct: 0, uprightPosturePct: 0, engagementScore: 0,
  stressLevel: 0, nervousnessIndicator: 0, dominantExpression: 'neutral',
  faceDetected: false, smileConfidence: 0, attentionScore: 0,
  headYaw: 0, headPitch: 0, headRoll: 0, headMovementVelocity: 0,
  blinkDetected: false, blinkRate: 0, expressionConfidence: 0,
}

interface UseVisualIntelOptions {
  interval?: number
  enabled?: boolean
}

export function useVisualIntel(options: UseVisualIntelOptions = {}) {
  const { interval = 3000, enabled = false } = options
  const [metrics, setMetrics] = useState<VisualMetrics>(DEFAULT_METRICS)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<VisualHistoryEntry[]>([])
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  const captureFrame = useCallback(async () => {
    const video = videoRef.current
    if (!video || !video.videoWidth || !video.videoHeight) return null
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas')
    }
    const canvas = canvasRef.current
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.translate(canvas.width, 0)
    ctx.scale(-1, 1)
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    return new Promise<string | null>((resolve) => {
      canvas.toBlob(
        async (blob) => {
          if (!blob) { resolve(null); return }
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64 = reader.result as string
            resolve(base64.split(',')[1])
          }
          reader.onerror = () => resolve(null)
          reader.readAsDataURL(blob)
        },
        'image/jpeg', 0.6
      )
    })
  }, [])

  const analyzeFrame = useCallback(async () => {
    if (!enabled) return
    setIsAnalyzing(true)
    try {
      const frame = await captureFrame()
      if (!frame) { setIsAnalyzing(false); return }
      const result = await api.interview.visual.analyze({ image: frame })
      const m: VisualMetrics = {
        eyeContactPct: result.eyeContactPct ?? 0,
        positiveExpressionPct: result.positiveExpressionPct ?? 0,
        neutralExpressionPct: result.neutralExpressionPct ?? 0,
        negativeExpressionPct: result.negativeExpressionPct ?? 0,
        uprightPosturePct: result.uprightPosturePct ?? 0,
        engagementScore: result.engagementScore ?? 0,
        stressLevel: result.stressLevel ?? 0,
        nervousnessIndicator: result.nervousnessIndicator ?? 0,
        dominantExpression: result.dominantExpression ?? 'neutral',
        faceDetected: result.faceDetected ?? false,
        smileConfidence: result.smileConfidence ?? 0,
        attentionScore: result.attentionScore ?? 0,
        headYaw: result.headYaw ?? 0,
        headPitch: result.headPitch ?? 0,
        headRoll: result.headRoll ?? 0,
        headMovementVelocity: result.headMovementVelocity ?? 0,
        blinkDetected: result.blinkDetected ?? false,
        blinkRate: result.blinkRate ?? 0,
        expressionConfidence: result.expressionConfidence ?? 0,
      }
      setMetrics(m)
      setHistory(prev => {
        const entry: VisualHistoryEntry = {
          time: Date.now(),
          eyeContact: m.eyeContactPct,
          engagement: m.engagementScore,
          attention: m.attentionScore,
          posture: m.uprightPosturePct,
          stress: m.stressLevel,
        }
        const next = [...prev, entry]
        return next.length > 30 ? next.slice(-30) : next
      })
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Visual analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }, [captureFrame, enabled])

  const start = useCallback((videoEl: HTMLVideoElement) => {
    videoRef.current = videoEl
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(analyzeFrame, interval)
    setTimeout(analyzeFrame, 500)
  }, [analyzeFrame, interval])

  const stop = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
    videoRef.current = null
  }, [])

  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current) }, [])

  return { metrics, isAnalyzing, error, start, stop, history, DEFAULT_METRICS }
}
