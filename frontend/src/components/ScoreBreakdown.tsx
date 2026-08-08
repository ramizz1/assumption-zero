/** Score breakdown table with all 7 dimensions */
import type { OpportunityScore } from '../types'
import { scoreColor, confidenceColor } from '../lib/utils'

interface Props {
  score: OpportunityScore
}

export default function ScoreBreakdown({ score }: Props) {
  return (
    <div id="score-breakdown" className="verseo-card p-5">
      <h2 className="section-title">Score Breakdown</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-zinc-500 border-b border-zinc-200">
              <th className="pb-3 font-medium">Dimension</th>
              <th className="pb-3 font-medium text-right">Raw</th>
              <th className="pb-3 font-medium text-right">Weight</th>
              <th className="pb-3 font-medium text-right">Weighted</th>
              <th className="pb-3 font-medium text-center">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {score.dimensions.map((dim) => (
              <tr key={dim.dimension} className="hover:bg-zinc-50">
                <td className="py-3 text-zinc-700 font-medium pr-4">
                  {dim.display_name}
                  {dim.missing_information.length > 0 && (
                    <span
                      className="ml-1.5 text-amber-500 text-xs"
                      title={dim.missing_information.join('; ')}
                    >
                      ⚠
                    </span>
                  )}
                </td>
                <td className={`py-3 text-right font-mono font-semibold ${scoreColor(dim.raw_score)}`}>
                  {dim.raw_score.toFixed(0)}
                </td>
                <td className="py-3 text-right text-gray-500">
                  {dim.weight}%
                </td>
                <td className={`py-3 text-right font-mono ${scoreColor(dim.raw_score)}`}>
                  {dim.weighted_score.toFixed(1)}
                </td>
                <td className="py-3 text-center">
                  <span className={`text-xs font-medium uppercase tracking-wide ${confidenceColor(dim.confidence)}`}>
                    {dim.confidence}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-zinc-200">
              <td className="pt-3 font-bold text-zinc-900">TOTAL</td>
              <td />
              <td />
              <td className={`pt-3 text-right font-bold text-lg font-mono ${scoreColor(score.total)}`}>
                {score.total.toFixed(1)}
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
