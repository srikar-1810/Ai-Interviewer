import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useInterviewStore } from '../store/interviewStore'
import { api } from '../lib/api'
import { useTTS, useSTT } from '../hooks/useSpeech'
import {
  Mic, MicOff, Send, Loader2, Bot, User,
  ChevronDown, ChevronUp, Power, ArrowRight,
  Sparkles, MessageSquare, Brain, Zap, Heart,
  Volume2, VolumeX, Eye, Lightbulb, Layers,
  BarChart3, TrendingUp, Target, Shield,
} from 'lucide-react'
import CameraPreview from '../components/CameraPreview'
import AnimatedAI from '../components/AnimatedAI'
import AudioVisualizer from '../components/AudioVisualizer'
import ScoreGauge from '../components/ScoreGauge'
import ProgressTracker from '../components/ProgressTracker'
import ScoreGraph from '../components/ScoreGraph'
import type { VisualMetrics } from '../hooks/useVisualIntel'
import { useAudioIntel, type AudioMetrics } from '../hooks/useAudioIntel'

interface Message {
  id: string
  role: 'ai' | 'user'
  text: string
  timestamp: number
  isVoice?: boolean
}

interface TopicBadge {
  topic: string
  count: number
  depth: number
}

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'badge-success',
  medium: 'badge-warning',
  hard: 'badge-error',
}

const scoreData = (m: Record<string, number>) => [
  { label: 'Tech', value: m.technicalScore || 0 },
  { label: 'Comm', value: m.communicationScore || 0 },
  { label: 'Conf', value: m.confidenceScore || 0 },
  { label: 'Depth', value: m.depthOfKnowledge || 0 },
  { label: 'Stress', value: 100 - (m.stressLevel || 0) },
]

export default function InterviewSuite() {
  const navigate = useNavigate()
  const {
    currentQuestion, setCurrentQuestion, questions, setQuestions,
    questionIndex, nextQuestion, metrics, updateMetrics,
    coachingConfig, startInterview, endInterview, resume,
    sessionId, setSessionId, isInterviewActive,
  } = useInterviewStore()

  const [messages, setMessages] = useState<Message[]>([])
  const [textInput, setTextInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isEnding, setIsEnding] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [showMetrics, setShowMetrics] = useState(true)
  const [cameraEnabled, setCameraEnabled] = useState(true)
  const [currentDifficulty, setCurrentDifficulty] = useState(coachingConfig?.difficulty || 'medium')
  const [topicCoverage, setTopicCoverage] = useState<TopicBadge[]>([])
  const [lastAdaptation, setLastAdaptation] = useState('')
  const [lastEncouragement, setLastEncouragement] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const startingInterviewRef = useRef(false)
  const [botSpeaking, setBotSpeaking] = useState(false)
  const maxQuestions = coachingConfig?.maxQuestions ?? 8
  const lastVisMetrics = useRef<VisualMetrics | null>(null)
  const visSaveTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const scoreHistory = useRef<Array<{ label: string; value: number }[]>>([])
  const [showAiReasoning, setShowAiReasoning] = useState(false)
  const [aiReasoning, setAiReasoning] = useState('')

  const { speak, stop: stopTTS, isSpeaking } = useTTS()
  const { isListening, transcript, start: startSTT, stop: stopSTT, resetTranscript } = useSTT()
  const audioIntel = useAudioIntel()
  const wasVoiceRef = useRef(false)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => scrollToBottom(), [messages, scrollToBottom])

  const speakAsBot = useCallback((text: string): Promise<void> => {
    return new Promise((resolve) => {
      setBotSpeaking(true)
      speak(text, () => { setBotSpeaking(false); resolve() })
    })
  }, [speak])

  useEffect(() => {
    const topicMap = new Map<string, { count: number; depth: number }>()
    questions.forEach(q => {
      const t = q.topic || 'general'
      const existing = topicMap.get(t) || { count: 0, depth: 0 }
      existing.count++
      existing.depth = q.is_drill_down ? existing.depth + 1 : existing.depth
      topicMap.set(t, existing)
    })
    setTopicCoverage(Array.from(topicMap.entries()).map(([topic, info]) => ({
      topic, count: info.count, depth: info.depth,
    })))
  }, [questions])

  useEffect(() => {
    if (!coachingConfig) { navigate('/coaching'); return }
    if (startingInterviewRef.current) return
    startingInterviewRef.current = true
    startInterview()
    ;(async () => {
      try {
        const res: any = await api.interview.start({
          focusAreas: coachingConfig.focusAreas,
          difficulty: coachingConfig.difficulty,
          role: coachingConfig.role || 'Software Engineer',
          resumeId: (resume as any)?.id,
        })
        const q = res.question
        setCurrentQuestion(q)
        setQuestions([q])
        if (q.difficulty) setCurrentDifficulty(q.difficulty)
        if (res.session_id) setSessionId(res.session_id)
        const m: Message = { id: 'msg-' + Date.now(), role: 'ai', text: q.text, timestamp: Date.now() }
        setMessages([m])
        await speakAsBot(q.text)
      } catch (e) {
        console.error('Failed to start interview:', e)
        setBotSpeaking(false)
      } finally { startingInterviewRef.current = false }
    })()
  }, [coachingConfig, navigate, resume, setCurrentQuestion, setQuestions, setSessionId, speakAsBot, startInterview])

  useEffect(() => {
    if (!sessionId || !isInterviewActive) return
    visSaveTimer.current = setInterval(async () => {
      const vis = lastVisMetrics.current
      if (vis?.faceDetected) {
        try {
          await api.interview.saveVisualMetrics(sessionId, {
            eyeContactPct: vis.eyeContactPct,
            engagementScore: vis.engagementScore,
            attentionScore: vis.attentionScore,
            uprightPosturePct: vis.uprightPosturePct,
            stressLevel: vis.stressLevel,
            nervousnessIndicator: vis.nervousnessIndicator,
            smileConfidence: vis.smileConfidence,
          })
        } catch { /* best-effort */ }
      }
    }, 10000)
    return () => { if (visSaveTimer.current) clearInterval(visSaveTimer.current) }
  }, [sessionId, isInterviewActive])

  const handleVisualMetrics = useCallback((vis: VisualMetrics) => { lastVisMetrics.current = vis }, [])

  const startVoiceInput = useCallback(() => {
    audioIntel.startRecording()
    startSTT()
  }, [audioIntel, startSTT])

  const stopVoiceInput = useCallback(() => {
    stopSTT()
  }, [stopSTT])

  const handleSubmitAnswer = useCallback(async (answerText: string) => {
    const t = (answerText || textInput).trim()
    if (!t || !currentQuestion || isProcessing) return

    stopSTT()
    setIsProcessing(true)
    setSubmitError('')

    const msg: Message = {
      id: 'msg-' + Date.now(), role: 'user', text: t,
      timestamp: Date.now(), isVoice: !!answerText,
    }
    setMessages(prev => [...prev, msg])
    resetTranscript()
    setTextInput('')

    const b64 = await audioIntel.stopRecording()
    let audioData = b64
    const wasVoice = wasVoiceRef.current
    wasVoiceRef.current = false
    if (b64 && wasVoice) {
      audioIntel.analyzeAudio(b64, t)
    }

    try {
      if (!sessionId) throw new Error('No session ID')

      const result: any = await api.interview.analyzeResponse(sessionId, t, currentQuestion.id, audioData || undefined)
      updateMetrics(result.metrics)
      scoreHistory.current.push(scoreData(result.metrics))

      if (result.adaptation) setLastAdaptation(result.adaptation)
      if (result.encouragement) setLastEncouragement(result.encouragement)

      if (questionIndex < maxQuestions - 1) {
        const nextRes = await api.interview.nextQuestion(sessionId, t)
        const nextQ = nextRes.question
        if (nextQ.difficulty) setCurrentDifficulty(nextQ.difficulty)

        const transition = result.transition || ''
        const combined = transition
          ? `${transition} ${nextQ.text}`
          : `${result.feedback || 'Great answer.'} ${nextQ.text}`

        setMessages(prev => [...prev, {
          id: 'msg-' + Date.now(), role: 'ai', text: combined, timestamp: Date.now(),
        }])
        setCurrentQuestion(nextQ)
        setQuestions(prev => [...prev, nextQ])
        nextQuestion()
        await speakAsBot(combined)
      } else {
        setIsEnding(true)
        await api.interview.end(sessionId)
        const finalFeedback = await api.interview.feedback(sessionId)
        useInterviewStore.getState().setFeedback(finalFeedback)
        navigate(`/analytics?session_id=${sessionId}`)
      }
    } catch (e: any) {
      setSubmitError(e.message || 'Processing failed')
      setMessages(prev => [...prev, {
        id: 'msg-' + Date.now() + '-err', role: 'ai',
        text: 'Could not process that answer. Please try again.',
        timestamp: Date.now(),
      }])
      setBotSpeaking(false)
    } finally { setIsProcessing(false) }
  }, [currentQuestion, textInput, isProcessing, sessionId, questionIndex, maxQuestions, stopSTT, resetTranscript, speakAsBot, updateMetrics, setCurrentQuestion, setQuestions, nextQuestion, navigate])

  const latestScore = scoreHistory.current[scoreHistory.current.length - 1] || []
  const engScore = metrics.engagementScore || 0
  const vis = lastVisMetrics.current
  const totalCoveredTopics = topicCoverage.length

  const diffBadge = (level: string) => {
    const cls = DIFFICULTY_COLORS[level] || DIFFICULTY_COLORS.medium
    return (
      <span className={`${cls} text-[10px]`}>
        <Zap className="w-2.5 h-2.5" />
        {level.charAt(0).toUpperCase() + level.slice(1)}
      </span>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between animate-in">
        <div>
          <h1 className="font-heading text-2xl font-bold text-white tracking-tight">Interview Session</h1>
          <p className="text-on-surface-dim text-sm mt-0.5">
            {isInterviewActive ? `Question ${questionIndex + 1} of ${questions.length || maxQuestions}` : 'Preparing...'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {diffBadge(currentDifficulty)}
          <button onClick={() => setShowAiReasoning(!showAiReasoning)}
            className={`btn-ghost text-xs ${showAiReasoning ? 'bg-accent-amber/10 text-accent-amber' : ''}`}>
            <Brain className="w-3.5 h-3.5" /> {showAiReasoning ? 'Hide' : 'AI Insight'}
          </button>
          <button onClick={() => setShowMetrics(!showMetrics)}
            className={`btn-ghost text-xs ${showMetrics ? 'bg-accent-amber/10 text-accent-amber' : ''}`}>
            <Zap className="w-3.5 h-3.5" /> {showMetrics ? 'Hide' : 'Metrics'}
          </button>
          <button onClick={() => setCameraEnabled(!cameraEnabled)}
            className={`btn-ghost text-xs ${cameraEnabled ? 'text-accent-amber' : ''}`}>
            <Eye className="w-3.5 h-3.5" /> {cameraEnabled ? 'Cam On' : 'Cam Off'}
          </button>
        </div>
      </div>

      {/* Progress Tracker */}
      <div className="animate-in-fast" style={{ animationDelay: '0.05s' }}>
        <ProgressTracker current={Math.min(questionIndex + 1, maxQuestions)} total={maxQuestions}
          labels={['Start', ...Array(maxQuestions - 2).fill(''), 'Review']} />
      </div>

      {/* AI Reasoning Panel */}
      {showAiReasoning && (aiReasoning || lastAdaptation) && (
        <div className="card p-4 border-accent-amber/20 bg-accent-amber/[0.02] animate-in-fast">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-amber/10 flex items-center justify-center shrink-0 mt-0.5">
              <Brain className="w-4 h-4 text-accent-amber" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-accent-amber/80 mb-1">AI Reasoning</p>
              {aiReasoning && (
                <p className="text-sm text-on-surface-muted italic leading-relaxed mb-2">{aiReasoning}</p>
              )}
              {lastAdaptation && (
                <div className="flex items-center gap-2 text-[11px] text-on-surface-dim">
                  <TrendingUp className="w-3 h-3" />
                  <span>{lastAdaptation}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-6">

          {/* AI Interviewer + Camera */}
          <div className="grid md:grid-cols-2 gap-4 animate-in-fast" style={{ animationDelay: '0.1s' }}>
            <div className="card p-6 flex flex-col items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 opacity-30 pointer-events-none" />
              <AnimatedAI isSpeaking={botSpeaking} size="lg" />
              <h3 className="mt-4 text-lg font-semibold text-white">AI Interviewer</h3>
              <p className="text-xs text-on-surface-dim mt-0.5 uppercase tracking-widest font-medium">
                {botSpeaking ? 'Speaking...' : isProcessing ? 'Thinking...' : 'Listening'}
              </p>
              {botSpeaking && (
                <div className="mt-3">
                  <AudioVisualizer isActive height={24} barCount={32} color="#d97706" />
                </div>
              )}
              {lastEncouragement && (
                <div className="mt-4 px-4 py-2 rounded-xl bg-accent-amber/10 border border-accent-amber/20 text-xs text-accent-amber text-center max-w-[240px] animate-in-fast">
                  {lastEncouragement}
                </div>
              )}
            </div>

            <div className="relative rounded-2xl overflow-hidden bg-black/40 border border-surface-border aspect-video">
              {cameraEnabled ? (
                <CameraPreview autoStart className="w-full h-full" onMetricsUpdate={handleVisualMetrics} />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center p-6">
                  <div className="w-14 h-14 rounded-full bg-white/[0.04] flex items-center justify-center mb-3">
                    <Power className="w-6 h-6 text-on-surface-dim" />
                  </div>
                  <p className="text-sm text-on-surface-muted font-medium">Camera Disabled</p>
                  <button onClick={() => setCameraEnabled(true)} className="btn-secondary text-xs mt-4">
                    Enable Camera
                  </button>
                </div>
              )}
              {vis?.faceDetected && (
                <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-black/50 backdrop-blur-sm border border-white/10">
                  <div className="w-2 h-2 rounded-full bg-accent-amber animate-pulse" />
                  <span className="text-[10px] text-accent-amber font-medium">FACE</span>
                </div>
              )}
            </div>
          </div>

          {/* Audio Visualizer + Voice */}
          <div className={`card p-5 transition-all duration-500 ${isListening ? 'border-accent-amber/30' : ''}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all
                  ${isListening ? 'bg-accent-amber/20' : 'bg-white/[0.04]'}`}>
                  <Mic className={`w-4 h-4 ${isListening ? 'text-accent-amber' : 'text-on-surface-dim'}`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Voice Input</p>
                  <p className="text-[10px] text-on-surface-dim">{isListening ? 'Live transcription active' : 'Click Start to speak'}</p>
                </div>
              </div>
              <div className="flex gap-2">
                {!isListening && !isProcessing && !botSpeaking && (
                  <button onClick={startVoiceInput} className="btn-secondary text-xs">
                    <Mic className="w-3.5 h-3.5" /> Start
                  </button>
                )}
                {isListening && (
                  <button onClick={stopVoiceInput}
                    className="btn-danger text-xs">
                    <MicOff className="w-3.5 h-3.5" /> Stop
                  </button>
                )}
                {transcript && (
                  <button onClick={() => { wasVoiceRef.current = true; handleSubmitAnswer(transcript) }} className="btn-primary text-xs">
                    Submit <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            <AudioVisualizer isActive={isListening} height={40} barCount={48} color={isListening ? '#d97706' : '#d97706'} />

            <div className="mt-3 min-h-[40px]">
              {transcript ? (
                <p className="text-sm text-on-surface-muted italic leading-relaxed">
                  {transcript}
                  <span className="inline-block w-1 h-4 bg-accent-amber ml-1 animate-pulse" />
                </p>
              ) : (
                <p className="text-sm text-on-surface-dim/40 italic">
                  {isListening ? 'Listening... speak your answer' : 'Click Start to answer via voice'}
                </p>
              )}
            </div>
          </div>

          {/* Conversation */}
          <div className="card p-5 animate-in-fast" style={{ animationDelay: '0.15s' }}>
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="w-4 h-4 text-accent-amber" />
              <h3 className="font-semibold text-sm text-white">Conversation</h3>
              <span className="text-[10px] text-on-surface-dim ml-auto">{messages.length} messages</span>
            </div>
            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1 scrollbar-hide">
              {messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in-fast`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-accent-amber/10 border border-accent-amber/15'
                      : 'bg-white/[0.03] border border-white/[0.06]'
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      {msg.role === 'ai' ? (
                        <Sparkles className="w-3 h-3 text-accent-amber" />
                      ) : (
                        <User className="w-3 h-3 text-accent-amber" />
                      )}
                      <span className="text-[10px] text-on-surface-dim">
                        {msg.role === 'ai' ? 'AI Interviewer' : 'You'}
                        {msg.isVoice && ' (voice)'}
                      </span>
                    </div>
                    <p className="text-sm text-on-surface leading-relaxed">{msg.text}</p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Text Input */}
          {submitError && (
            <div className="card p-4 border-accent-rose/20 bg-accent-rose/5">
              <p className="text-sm text-accent-rose">{submitError}</p>
            </div>
          )}
          <form onSubmit={(e) => { e.preventDefault(); handleSubmitAnswer(textInput) }}
            className="card p-4 flex gap-3 items-center animate-in-fast" style={{ animationDelay: '0.2s' }}>
            <input
              type="text"
              value={textInput}
              onChange={e => setTextInput(e.target.value)}
              placeholder="Type your answer..."
              className="input flex-1 text-sm"
              disabled={isProcessing || botSpeaking}
            />
            <button type="button" onClick={isListening ? stopVoiceInput : startVoiceInput}
              className={`p-3 rounded-xl transition-all ${
                isListening
                  ? 'bg-accent-rose/15 text-accent-rose border border-accent-rose/20'
                  : 'bg-white/[0.04] text-on-surface-dim hover:text-white border border-white/[0.06]'
              }`}>
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button type="button" onClick={isSpeaking ? stopTTS : undefined}
              className={`p-3 rounded-xl transition-all ${
                isSpeaking
                  ? 'bg-accent-amber/15 text-accent-amber'
                  : 'bg-white/[0.04] text-on-surface-dim border border-white/[0.06]'
              }`}>
              {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <button type="submit" disabled={!textInput.trim() || isProcessing}
              className="btn-primary !p-3">
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>
        </div>

        {/* Sidebar */}
        <div className="space-y-4 animate-in" style={{ animationDelay: '0.2s' }}>
          {/* Score Gauges */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2">
                <Zap className="w-4 h-4 text-accent-amber" /> Live Scores
              </h3>
              <button onClick={() => setShowMetrics(!showMetrics)}
                className="text-on-surface-dim hover:text-on-surface">
                {showMetrics ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>
            {showMetrics && (
              <>
                <div className="grid grid-cols-3 gap-2 mb-4">
                  <ScoreGauge value={metrics.technicalScore} label="TECH" size="sm" gradient="amber" />
                  <ScoreGauge value={metrics.communicationScore} label="COMM" size="sm" gradient="amber" />
                  <ScoreGauge value={metrics.confidenceScore} label="CONF" size="sm" gradient="cyan" />
                </div>
                <div className="grid grid-cols-3 gap-2 mb-4">
                  <ScoreGauge value={metrics.depthOfKnowledge} label="DEPTH" size="sm" gradient="amber" />
                  <ScoreGauge value={100 - (metrics.stressLevel || 0)} label="CALM" size="sm" gradient="slate" />
                  <ScoreGauge value={metrics.engagementScore} label="ENGAGE" size="sm" gradient="amber" />
                </div>

                {scoreHistory.current.length >= 2 && (
                  <div className="mt-3">
                    <p className="text-[10px] text-on-surface-dim uppercase tracking-wider mb-2">Score Trend</p>
                    <ScoreGraph
                      data={scoreHistory.current.map((s, i) => ({
                        label: `Q${i + 1}`,
                        value: Math.round(s.reduce((a, b) => a + b.value, 0) / s.length),
                      }))}
                      height={80}
                    />
                  </div>
                )}
              </>
            )}
          </div>

          {/* Topic Coverage */}
          {topicCoverage.length > 0 && (
            <div className="card p-5">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-accent-amber" /> Topic Coverage
              </h3>
              <div className="space-y-1.5">
                {topicCoverage.map(tc => (
                  <div key={tc.topic} className="flex items-center justify-between text-xs">
                    <span className="text-on-surface-muted capitalize truncate mr-2">{tc.topic.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-on-surface-dim text-[10px]">
                        {tc.depth > 0 ? `depth ${tc.depth}` : `${tc.count}q`}
                      </span>
                      <div className="w-16 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                        <div className="h-full rounded-full bg-gradient-to-r from-accent-amber to-accent-amber-bright transition-all"
                          style={{ width: `${Math.min(tc.count * 20, 100)}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-on-surface-dim mt-2">
                {totalCoveredTopics} topic{totalCoveredTopics !== 1 ? 's' : ''} explored
              </p>
            </div>
          )}

          {/* Visual Analytics */}
          {vis?.faceDetected && (
            <div className="card p-5 animate-in-fast">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
                <Eye className="w-4 h-4 text-accent-amber" /> Visual Analytics
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Eye Contact', value: vis.eyeContactPct, color: 'from-accent-amber to-accent-amber-bright' },
                  { label: 'Attention', value: vis.attentionScore, color: 'from-accent-amber to-accent-rose' },
                  { label: 'Posture', value: vis.uprightPosturePct, color: 'from-accent-amber to-accent-cyan' },
                  { label: 'Smile', value: vis.smileConfidence, color: 'from-accent-amber to-orange-500' },
                ].map(item => (
                  <div key={item.label} className="space-y-1">
                    <p className="text-[10px] text-on-surface-dim uppercase tracking-wider">{item.label}</p>
                    <p className="text-lg font-bold text-white">{item.value}%</p>
                    <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                      <div className={`h-full rounded-full bg-gradient-to-r ${item.color} transition-all`}
                        style={{ width: `${item.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              {vis.blinkDetected && (
                <div className="mt-2 flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan animate-pulse" />
                  <span className="text-[10px] text-accent-cyan/70">{vis.blinkRate}/min blink rate</span>
                </div>
              )}
            </div>
          )}

          {/* Audio Analytics */}
          <div className="card p-5 animate-in-fast">
            <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
              <Volume2 className="w-4 h-4 text-accent-amber" /> Audio Intelligence
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Confidence', value: audioIntel.metrics.confidenceScore, color: 'from-accent-amber to-accent-amber-bright' },
                { label: 'Clarity', value: audioIntel.metrics.communicationClarityScore, color: 'from-accent-amber to-accent-cyan' },
                { label: 'Pitch Variation', value: Math.min(audioIntel.metrics.pitchVariation * 2, 99), color: 'from-accent-amber to-orange-500' },
                { label: 'Tone Stability', value: audioIntel.metrics.toneStability, color: 'from-accent-amber to-teal-500' },
              ].map(item => (
                <div key={item.label} className="space-y-1">
                  <p className="text-[10px] text-on-surface-dim uppercase tracking-wider">{item.label}</p>
                  <p className="text-lg font-bold text-white">{Math.round(item.value)}%</p>
                  <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className={`h-full rounded-full bg-gradient-to-r ${item.color} transition-all`}
                      style={{ width: `${Math.round(item.value)}%` }} />
                  </div>
                </div>
              ))}
            </div>
            {audioIntel.metrics.speechRateWpm > 0 && (
              <div className="mt-3 flex items-center justify-between text-[11px] text-on-surface-dim">
                <span>Speech Rate</span>
                <span className="text-white font-medium">{audioIntel.metrics.speechRateWpm} wpm</span>
              </div>
            )}
            {audioIntel.metrics.silenceRatio > 0 && (
              <div className="mt-1 flex items-center justify-between text-[11px] text-on-surface-dim">
                <span>Silence Ratio</span>
                <span className="text-white font-medium">{(audioIntel.metrics.silenceRatio * 100).toFixed(0)}%</span>
              </div>
            )}
            {audioIntel.metrics.hesitationScore > 0 && (
              <div className="mt-1 flex items-center justify-between text-[11px] text-on-surface-dim">
                <span>Hesitation</span>
                <span className="text-white font-medium">{audioIntel.metrics.hesitationScore}%</span>
              </div>
            )}
          </div>

          {/* Stress + Energy */}
          <div className="card p-5">
            <h3 className="font-semibold text-sm text-white flex items-center gap-2 mb-3">
              <Heart className="w-4 h-4 text-accent-rose" /> Stress & Energy
            </h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-dim">Stress Level</span>
                  <span className={`font-medium ${(metrics.stressLevel || 0) > 60 ? 'text-accent-rose' : 'text-accent-amber'}`}>
                    {metrics.stressLevel}%
                  </span>
                </div>
                <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${
                    (metrics.stressLevel || 0) > 60 ? 'bg-gradient-to-r from-accent-amber to-accent-rose'
                      : (metrics.stressLevel || 0) > 30 ? 'bg-gradient-to-r from-accent-amber to-accent-amber-bright'
                      : 'bg-gradient-to-r from-accent-amber to-accent-cyan'
                  }`} style={{ width: `${metrics.stressLevel || 0}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-dim">Nervousness</span>
                  <span className="font-medium text-on-surface-muted">{lastVisMetrics.current?.nervousnessIndicator || 0}%</span>
                </div>
                <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-orange-500 to-accent-rose transition-all"
                    style={{ width: `${lastVisMetrics.current?.nervousnessIndicator || 0}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Session Info */}
          <div className="card p-5 bg-white/[0.02]">
            <h3 className="font-semibold text-sm text-white mb-3">Session</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-on-surface-dim">Question</span>
                <span className="text-on-surface-muted">{questionIndex + 1} / {questions.length || maxQuestions}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-on-surface-dim">Difficulty</span>
                <span className="capitalize flex items-center gap-1">{diffBadge(currentDifficulty)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-on-surface-dim">Role</span>
                <span className="text-on-surface-muted truncate ml-2">{coachingConfig?.role || 'Engineer'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-on-surface-dim">Focus</span>
                <span className="text-on-surface-muted text-right text-[10px]">{(coachingConfig?.focusAreas || []).join(', ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-on-surface-dim">Topics</span>
                <span className="text-on-surface-muted">{totalCoveredTopics} covered</span>
              </div>
            </div>
          </div>

          {isEnding && (
            <div className="card p-5 border-accent-amber/20 bg-accent-amber/5">
              <p className="text-sm text-accent-amber flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Generating analytics...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
