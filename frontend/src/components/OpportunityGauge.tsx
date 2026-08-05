/** Circular opportunity score gauge */
import { scoreColor, scoreBgColor } from '../lib/utils'

interface Props {
  score: number
  size?: number
}

export default function OpportunityGauge({ score, size = 140 }: Props) {
  const radius = 52
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(100, Math.max(0, score)) / 100
  const strokeDashoffset = circumference * (1 - progress)
  const colorClass = scoreColor(score)
  const bgColorClass = scoreBgColor(score)

  return (
    <div
      id="opportunity-gauge"
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
      aria-label={`Opportunity Score: ${score.toFixed(0)} out of 100`}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 120 120"
        className="-rotate-90"
      >
        {/* Background track */}
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="#1f1f26"
          strokeWidth="10"
        />
        {/* Score arc */}
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          className={
            score >= 65
              ? 'stroke-green-400'
              : score >= 45
              ? 'stroke-amber-400'
              : 'stroke-red-400'
          }
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-bold tabular-nums ${colorClass}`}>
          {score.toFixed(0)}
        </span>
        <span className="text-xs text-gray-500 mt-0.5">/ 100</span>
      </div>
    </div>
  )
}
