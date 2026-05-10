import { useState, useRef, useCallback, useEffect } from 'react'
import { api } from '../lib/api'

export interface AudioMetrics {
  confidenceScore: number
  communicationClarityScore: number
  hesitationScore: number
  pitchVariation: number
  f0Mean: number
  toneStability: number
  energyStability: number
  silenceRatio: number
  speechRateWpm: number
  duration: number
}

const DEFAULT_METRICS: AudioMetrics = {
  confidenceScore: 50,
  communicationClarityScore: 50,
  hesitationScore: 0,
  pitchVariation: 0,
  f0Mean: 0,
  toneStability: 50,
  energyStability: 50,
  silenceRatio: 0,
  speechRateWpm: 0,
  duration: 0,
}

export function useAudioIntel() {
  const [metrics, setMetrics] = useState<AudioMetrics>(DEFAULT_METRICS)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const isRecordingRef = useRef(false)

  const startRecording = useCallback(async () => {
    chunksRef.current = []
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = recorder
      isRecordingRef.current = true

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.start(250)
    } catch (e) {
      setError('Microphone access denied for audio analysis')
      console.warn('AudioIntel: mic access failed', e)
    }
  }, [])

  const stopRecording = useCallback((): Promise<string | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current
      const stream = streamRef.current

      if (!recorder || recorder.state === 'inactive') {
        if (stream) stream.getTracks().forEach((t) => t.stop())
        streamRef.current = null
        isRecordingRef.current = false
        resolve(null)
        return
      }

      recorder.onstop = async () => {
        isRecordingRef.current = false
        if (stream) stream.getTracks().forEach((t) => t.stop())
        streamRef.current = null

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        chunksRef.current = []
        if (blob.size < 100) {
          resolve(null)
          return
        }

        const reader = new FileReader()
        reader.onloadend = () => {
          const base64 = reader.result as string
          resolve(base64.split(',')[1])
        }
        reader.onerror = () => resolve(null)
        reader.readAsDataURL(blob)
      }

      recorder.stop()
    })
  }, [])

  const analyzeAudio = useCallback(async (audioB64: string, transcript?: string) => {
    if (!audioB64) return
    setIsAnalyzing(true)
    try {
      const result = await api.interview.audio.analyze({ audio: audioB64, transcript })
      if (result.error) {
        setError(result.error)
        return
      }
      const m = result.audioMetrics as AudioMetrics
      setMetrics(m)
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Audio analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }, [])

  useEffect(() => {
    return () => {
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop())
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop() } catch {}
      }
    }
  }, [])

  return { metrics, isAnalyzing, error, startRecording, stopRecording, analyzeAudio, DEFAULT_METRICS }
}
