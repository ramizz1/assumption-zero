import { useParams, Link } from 'react-router-dom'
import { useAnalysis } from '../hooks/useAnalysis'
import ProgressView from './ProgressView'
import ReportView from './ReportView'
import DisclaimerBanner from '../components/DisclaimerBanner'

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const { data, error } = useAnalysis(id ?? null)

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-[#1f1f26] px-6 py-4 sticky top-0 bg-[#0d0d0f]/95 backdrop-blur-sm z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <span className="text-xs font-mono font-bold text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">A0</span>
            <span className="font-bold text-white">Assumption Zero</span>
            <span className="text-[10px] font-semibold text-amber-400/80 bg-amber-400/10 border border-amber-400/20 px-1.5 py-0.5 rounded-full">BETA</span>
          </Link>
          <span className="text-xs text-gray-600 font-mono">{id?.slice(0, 8)}…</span>
        </div>
      </header>

      <main className="flex-1 px-4 py-8">
        {error ? (
          <div className="max-w-2xl mx-auto text-center mt-16">
            <div className="card p-8">
              <p className="text-red-400 text-lg mb-4">Analysis Error</p>
              <p className="text-gray-400 text-sm mb-6">{error}</p>
              <Link to="/" className="btn-primary">← Start New Analysis</Link>
            </div>
          </div>
        ) : !data ? (
          <div className="max-w-2xl mx-auto text-center mt-16">
            <div className="card p-8">
              <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-400">Loading analysis…</p>
            </div>
          </div>
        ) : data.status === 'failed' ? (
          <div className="max-w-2xl mx-auto text-center mt-16">
            <div className="card p-8">
              <p className="text-red-400 text-lg mb-4">Analysis Failed</p>
              <p className="text-gray-400 text-sm mb-6">{data.error_message}</p>
              <Link to="/" className="btn-primary">← Start New Analysis</Link>
            </div>
          </div>
        ) : data.status === 'complete' ? (
          <ReportView result={data} />
        ) : (
          <ProgressView result={data} />
        )}
      </main>

      <DisclaimerBanner />
    </div>
  )
}
