import { useState, useRef, useCallback, useEffect } from 'react'

export function useTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)
  const queueRef = useRef<string[]>([])

  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel()
    }
  }, [])

  const speak = useCallback((text: string, onEnd?: () => void) => {
    if (!('speechSynthesis' in window)) {
      onEnd?.()
      return
    }
    window.speechSynthesis.cancel()

    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/[*_`#-]/g, '')
      .replace(/\n+/g, '. ')
      .trim()
    if (!cleanText) {
      onEnd?.()
      return
    }

    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.rate = 0.95
    utterance.pitch = 1.0
    utterance.volume = 1.0

    const voices = window.speechSynthesis.getVoices()
    const preferred = voices.find(v => v.name.includes('Samantha') || v.name.includes('Google') || v.lang.startsWith('en'))
    if (preferred) utterance.voice = preferred

    utterance.onstart = () => {
      setIsSpeaking(true)
      setIsPaused(false)
    }
    utterance.onend = () => {
      setIsSpeaking(false)
      setIsPaused(false)
      if (queueRef.current.length > 0) {
        const next = queueRef.current.shift()
        if (next) setTimeout(() => speak(next, onEnd), 300)
      } else {
        onEnd?.()
      }
    }
    utterance.onerror = () => {
      setIsSpeaking(false)
      setIsPaused(false)
      onEnd?.()
    }

    utteranceRef.current = utterance
    console.log('AI starting to speak:', cleanText)
    window.speechSynthesis.speak(utterance)
  }, [])

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel()
    setIsSpeaking(false)
    setIsPaused(false)
    queueRef.current = []
  }, [])

  const pause = useCallback(() => {
    if (window.speechSynthesis?.speaking) {
      window.speechSynthesis.pause()
      setIsPaused(true)
    }
  }, [])

  const resume = useCallback(() => {
    if (window.speechSynthesis?.paused) {
      window.speechSynthesis.resume()
      setIsPaused(false)
    }
  }, [])

  return { speak, stop, pause, resume, isSpeaking, isPaused }
}

export function useSTT() {
  const [isListening, setIsListening] = useState(false)
  const isListeningRef = useRef(false)
  const [transcript, setTranscript] = useState('')
  const recognitionRef = useRef<any>(null)
  const finalTranscriptRef = useRef('')

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      console.warn('Speech recognition is not supported in this browser')
      return
    }

    const rec = new SpeechRecognition()
    rec.continuous = true
    rec.interimResults = true
    rec.lang = 'en-US'

    rec.onresult = (event: any) => {
      let final = finalTranscriptRef.current
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript + ' '
        } else {
          interim += result[0].transcript
        }
      }
      finalTranscriptRef.current = final
      setTranscript((final + interim).trim())
    }

    rec.onend = () => {
      if (isListeningRef.current) {
        try { rec.start() } catch (e) { 
          setIsListening(false)
          isListeningRef.current = false
        }
      }
    }

    rec.onerror = (event: any) => {
      console.error('STT error:', event.error)
      if (event.error !== 'no-speech') {
        setIsListening(false)
        isListeningRef.current = false
      }
    }

    recognitionRef.current = rec

    return () => {
      try { rec.stop() } catch (e) {}
    }
  }, [])

  const start = useCallback(() => {
    setTranscript('')
    finalTranscriptRef.current = ''
    console.log('Attempting to start STT...')
    try {
      if (!recognitionRef.current) {
        console.warn('STT recognition object not initialized')
        return
      }
      isListeningRef.current = true
      recognitionRef.current.start()
      setIsListening(true)
      console.log('STT started successfully')
    } catch (e) {
      console.error('STT start failed:', e)
    }
  }, [])

  const stop = useCallback(() => {
    try { recognitionRef.current?.stop() } catch (e) {}
    setIsListening(false)
    isListeningRef.current = false
  }, [])

  const resetTranscript = useCallback(() => {
    finalTranscriptRef.current = ''
    setTranscript('')
  }, [])

  return { isListening, transcript, start, stop, resetTranscript }
}
