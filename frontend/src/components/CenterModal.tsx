import { useEffect } from 'react'
import { X } from 'lucide-react'

interface CenterModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
}

export default function CenterModal({ open, onClose, title, children }: CenterModalProps) {
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto card-glass p-6 animate-scale-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          {title && <h2 className="font-heading font-bold text-lg text-white">{title}</h2>}
          <button
            onClick={onClose}
            className="ml-auto p-1.5 rounded-lg text-on-surface-dim hover:text-on-surface hover:bg-white/[0.04] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
