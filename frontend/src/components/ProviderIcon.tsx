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
  className = '',
}) => {
  const config = {
    sm: { container: 'w-5 h-5 rounded-md p-0.5', text: 'text-[9px]' },
    md: { container: 'w-6 h-6 rounded-lg p-1', text: 'text-[10px]' },
    lg: { container: 'w-8 h-8 rounded-xl p-1.5', text: 'text-xs' },
  }[size]

  const labelMap: Record<string, string> = {
    auto: 'A0',
    beta: 'A0',
    custom: 'API',
    ollama: 'OL',
    opencode: 'OC',
    openai_compat: 'AI',
    groq: 'GQ',
    openrouter: 'OR',
  }
  const label = labelMap[id] || id.slice(0, 2).toUpperCase()

  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center font-black tracking-tight transition-all ${
        config.container
      } ${
        isActive
          ? 'bg-white text-gray-900 shadow-sm ring-1 ring-black/10'
          : 'border border-gray-200 bg-gray-100 text-gray-700 hover:bg-gray-200'
      } ${className}`}
      aria-label={id}
    >
      <span className={config.text}>{label}</span>
    </span>
  )
}

export default ProviderIcon
