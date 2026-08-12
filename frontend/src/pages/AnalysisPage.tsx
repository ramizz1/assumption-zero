import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAnalysis } from '../hooks/useAnalysis'
import ProgressView from './ProgressView'
import ReportView from './ReportView'
import DisclaimerBanner from '../components/DisclaimerBanner'

function safeAnalysisMessage(value?: string | null): string {
  const message = (value || '').replace(/<[^>]+>/g, '').trim()
  if (!message || /unexpected error occurred/i.test(message)) {
    return 'The analysis could not be completed. Verify your AI provider setup and try again.'
  }
  return message.slice(0, 500)
}

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const { data, error } = useAnalysis(id ?? null)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('Link copied!')

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setToastMessage('Link copied!')
    } catch {
      setToastMessage('Clipboard access was blocked')
    }
    setShowToast(true)
    setTimeout(() => setShowToast(false), 3000)
  }

  return (
    <div className="min-h-screen flex flex-col relative bg-white">
      {/* Toast Notification */}
      {showToast && (
        <div role="status" className="fixed top-20 left-1/2 transform -translate-x-1/2 bg-zinc-900 text-white px-4 py-2 rounded-full shadow-lg text-sm font-bold z-50 animate-in slide-in-from-top-2 fade-in flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          {toastMessage}
        </div>
      )}

      {/* Header */}
      <header className="border-b border-zinc-200 px-6 py-4 sticky top-0 bg-white/95 backdrop-blur-sm z-30">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 hover:opacity-70 transition-opacity">
            <span className="text-xs font-mono font-bold text-zinc-500 bg-zinc-100 px-1.5 py-0.5 rounded border border-zinc-200">A0</span>
            <span className="font-bold text-zinc-900">Assumption Zero</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/docs" className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-950 px-3 py-1.5 text-xs font-bold text-white shadow-sm transition-colors hover:bg-zinc-800">
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></svg>
              Docs
            </Link>
            <button
              onClick={handleShare}
              className="px-3 py-1.5 bg-zinc-50 hover:bg-zinc-100 text-zinc-700 border border-zinc-200 rounded-lg text-xs font-bold font-mono transition-colors flex items-center gap-2"
            >
              <span aria-hidden="true">↗</span><span className="hidden sm:inline">Share Analysis</span><span className="sm:hidden">Share</span>
            </button>
            <span className="text-xs text-zinc-400 font-mono hidden sm:inline">{id?.slice(0, 8)}…</span>
          </div>
        </div>
      </header>

      <main className="flex-1 px-4 py-8 bg-white verseo-grid">
        {error ? (
          <div className="max-w-2xl mx-auto text-center mt-16">
            <div className="verseo-card p-8">
              <div className="text-3xl mb-3">⚠️</div>
              <p className="text-red-600 font-bold text-lg mb-2">
                {error.includes('402') || error.includes('429') || error.includes('quota') || error.includes('token') || error.includes('credit')
                  ? 'No AI Tokens Available (Quota / Rate Limit Exceeded)'
                  : 'Analysis Error'}
              </p>
              <p className="text-zinc-500 text-sm mb-6 max-w-lg mx-auto leading-relaxed">{safeAnalysisMessage(error)}</p>
              <Link to="/" className="btn-primary">← Start New Analysis</Link>
            </div>
          </div>
        ) : !data ? (
          <div className="max-w-2xl mx-auto text-center mt-16">
            <div className="verseo-card p-8">
              <div className="w-8 h-8 border-2 border-zinc-200 border-t-zinc-900 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-zinc-500">Loading analysis…</p>
            </div>
          </div>
        ) : data.status === 'failed' ? (
          <div className="max-w-2xl mx-auto text-center mt-16">
            <div className="verseo-card p-8">
              <div className="text-3xl mb-3">⚠️</div>
              <p className="text-red-600 font-bold text-lg mb-2">
                {data.error_message?.includes('402') || data.error_message?.includes('429') || data.error_message?.includes('quota') || data.error_message?.includes('token') || data.error_message?.includes('credit')
                  ? 'No AI Tokens Available (Quota Exceeded)'
                  : 'Analysis Failed'}
              </p>
              <p className="text-zinc-500 text-sm mb-6 max-w-lg mx-auto leading-relaxed">{safeAnalysisMessage(data.error_message)}</p>
              {(data.error_message?.includes('402') || data.error_message?.includes('429') || data.error_message?.includes('quota') || data.error_message?.includes('token')) && (
                <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-700 text-left max-w-lg mx-auto">
                  <strong>Tip:</strong> Return home, open Configure Keys, and validate a provider. Keys stay in session storage and are never included in the public site bundle.
                </div>
              )}
              <Link to="/" className="btn-primary">← Start New Analysis</Link>
            </div>
          </div>
        ) : data.status === 'complete' ? (
          <ReportView initialResult={data} />
        ) : (
          <ProgressView result={data} />
        )}
      </main>

      <DisclaimerBanner />
    </div>
  )
}
