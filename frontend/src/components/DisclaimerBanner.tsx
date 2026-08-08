/** Permanent disclaimer banner — always visible */
import { DISCLAIMER } from '../lib/utils'

export default function DisclaimerBanner() {
  return (
    <div
      id="disclaimer-banner"
      className="w-full bg-zinc-50 border-t border-zinc-200 py-3 px-4"
      role="note"
      aria-label="Important disclaimer"
    >
      <p className="text-center text-xs text-zinc-500 max-w-4xl mx-auto">
        ⚠&ensp;{DISCLAIMER}
      </p>
    </div>
  )
}
