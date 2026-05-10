import { Sparkles } from 'lucide-react'

interface AnimatedAIProps {
  isSpeaking: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function AnimatedAI({ isSpeaking, size = 'md' }: AnimatedAIProps) {
  const dims = { sm: 64, md: 96, lg: 128 }
  const d = dims[size]

  return (
    <div className="relative flex items-center justify-center" style={{ width: d, height: d }}>
      {isSpeaking && (
        <>
          <div className="absolute inset-0 rounded-full animate-ping opacity-20 bg-gradient-to-r from-accent-amber to-accent-amber-bright" />
          <div className="absolute inset-0 rounded-full animate-pulse-soft opacity-30 bg-gradient-to-r from-accent-amber to-accent-amber-bright" />
        </>
      )}

      <div className={`absolute inset-0 rounded-full blur-2xl transition-all duration-500
        ${isSpeaking ? 'bg-accent-amber/20 scale-110' : 'bg-accent-amber/10 scale-90'}`}
      />

      <div className={`relative z-10 w-full h-full rounded-full flex items-center justify-center
        bg-white/[0.06] border border-white/[0.10] backdrop-blur-sm
        transition-all duration-300 ${isSpeaking ? 'scale-105' : 'scale-100'}`}
      >
        <div className="absolute inset-2 rounded-full bg-gradient-to-br from-accent-amber/20 to-accent-amber/10 blur-sm" />

        <Sparkles className={`relative z-10 transition-all duration-300
          ${size === 'sm' ? 'w-5 h-5' : size === 'md' ? 'w-8 h-8' : 'w-10 h-10'}
          ${isSpeaking ? 'text-white scale-110' : 'text-white/60'}`}
        />

        {isSpeaking && (
          <div className="absolute -bottom-1 flex gap-1">
            {[1, 2, 3].map(i => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-accent-amber animate-bounce"
                style={{ animationDelay: `${i * 150}ms`, animationDuration: '0.6s' }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
