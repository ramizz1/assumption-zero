/** Permanent disclaimer banner — always visible */
import { DISCLAIMER } from '../lib/utils'

export default function DisclaimerBanner() {
  return (
    <div
      id="disclaimer-banner"
      className="w-full bg-amber-400/5 border-t border-amber-500/20 py-3 px-4"
      role="note"
      aria-label="Important disclaimer"
    >
      <p className="text-center text-xs text-amber-400/80 max-w-4xl mx-auto">
        ⚠&ensp;{DISCLAIMER}
      </p>
    </div>
  )
}
