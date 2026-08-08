import React from 'react'

export interface ProviderIconProps {
  id: string
  isActive?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const ProviderIcon: React.FC<ProviderIconProps> = ({
  id,
  isActive = false,
  size = 'sm',
  className = ''
}) => {
  const config = {
    sm: { container: 'w-5 h-5 rounded-md p-0.5', img: 'w-3.5 h-3.5', text: 'text-xs' },
    md: { container: 'w-6 h-6 rounded-lg p-1', img: 'w-4 h-4', text: 'text-sm' },
    lg: { container: 'w-8 h-8 rounded-xl p-1.5', img: 'w-5 h-5', text: 'text-base' },
  }[size]

  if (id === 'custom') {
    return (
      <span
        className={`inline-flex items-center justify-center shrink-0 transition-all ${
          config.container
        } ${
          isActive
            ? 'bg-white text-gray-900 shadow-sm ring-1 ring-black/10'
            : 'bg-gray-100 text-gray-700 border border-gray-200'
        } ${className}`}
      >
        <span className={config.text}>🔧</span>
      </span>
    )
  }

  const srcMap: Record<string, string> = {
    ollama: '/ollama.png',
    opencode: '/opencode.png',
    openai_compat: '/openai.png',
    groq: '/groq.png',
    openrouter: '/openrouter.png',
  }

  const src = srcMap[id] || '/ollama.png'

  return (
    <span
      className={`inline-flex items-center justify-center shrink-0 transition-all ${
        config.container
      } ${
        isActive
          ? 'bg-white shadow-sm ring-1 ring-black/10'
          : 'bg-gray-100 hover:bg-gray-200 border border-gray-200'
      } ${className}`}
    >
      <img
        src={src}
        alt={id}
        className={`${config.img} object-contain transition-transform duration-200`}
      />
    </span>
  )
}

export default ProviderIcon
