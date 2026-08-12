import React from 'react'

export interface ProviderIconProps {
  id: string
  isActive?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const providerAssets: Record<string, { src: string; label: string }> = {
  ollama: { src: '/ollama.png', label: 'Ollama' },
  opencode: { src: '/opencode.png', label: 'OpenCode' },
  openai_compat: { src: '/openai.png', label: 'OpenAI' },
  groq: { src: '/groq.png', label: 'Groq' },
  openrouter: { src: '/openrouter.png', label: 'OpenRouter' },
}

export const ProviderIcon: React.FC<ProviderIconProps> = ({
  id,
  isActive = false,
  size = 'sm',
  className = '',
}) => {
  const config = {
    sm: { container: 'h-5 w-5 rounded-md p-0.5', image: 'h-3.5 w-3.5', text: 'text-[9px]' },
    md: { container: 'h-6 w-6 rounded-lg p-1', image: 'h-4 w-4', text: 'text-[10px]' },
    lg: { container: 'h-8 w-8 rounded-xl p-1.5', image: 'h-5 w-5', text: 'text-xs' },
  }[size]

  const sharedClasses = `inline-flex shrink-0 items-center justify-center transition-all ${config.container} ${
    isActive
      ? 'bg-white text-zinc-950 shadow-sm ring-1 ring-black/10'
      : 'border border-zinc-200 bg-zinc-100 text-zinc-700'
  } ${className}`

  if (id === 'auto' || id === 'beta') {
    return (
      <span className={`${sharedClasses} font-black`} aria-hidden="true">
        <span className={config.text}>A0</span>
      </span>
    )
  }

  if (id === 'custom') {
    return (
      <span className={sharedClasses} aria-hidden="true">
        <svg className={config.image} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1-2.9 2.9-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21h-4v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1-2.9-2.9.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3v-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1 2.9-2.9.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V3h4v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1 2.9 2.9-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1h.1v4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
        </svg>
      </span>
    )
  }

  const asset = providerAssets[id] ?? providerAssets.ollama
  return (
    <span className={sharedClasses}>
      <img src={asset.src} alt="" title={asset.label} className={`${config.image} object-contain`} />
    </span>
  )
}

export default ProviderIcon
