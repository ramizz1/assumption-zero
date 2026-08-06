import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { AnalysisListItem } from '../types'
import { recommendationColor, recommendationBg, formatDate } from '../lib/utils'

interface Props {
  isOpen: boolean
  onClose: () => void
  onCountUpdate?: (count: number) => void
}

export const SavedAnalysesModal: React.FC<Props> = ({ isOpen, onClose, onCountUpdate }) => {
  const navigate = useNavigate()
  const [items, setItems] = useState<AnalysisListItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [filterRec, setFilterRec] = useState<string>('all')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.listAnalyses()
      setItems(data || [])
      if (onCountUpdate) {
        onCountUpdate((data || []).length)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load saved analyses')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchItems()
    }
  }, [isOpen])

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!window.confirm('Delete this analysis? This action cannot be undone.')) return
    setDeletingId(id)
    try {
      await api.deleteAnalysis(id)
      const updated = items.filter((item) => item.analysis_id !== id)
      setItems(updated)
      if (onCountUpdate) {
        onCountUpdate(updated.length)
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete analysis')
    } finally {
      setDeletingId(null)
    }
  }

  if (!isOpen) return null

  const filteredItems = items.filter((item) => {
    const matchesSearch =
      !search.trim() ||
      item.idea_name.toLowerCase().includes(search.toLowerCase()) ||
      item.analysis_id.toLowerCase().includes(search.toLowerCase())

    const matchesFilter =
      filterRec === 'all' ||
      (filterRec === 'complete' && item.status === 'complete') ||
      (filterRec === 'failed' && item.status === 'failed') ||
      (filterRec === 'pending' && item.status === 'pending') ||
      (item.recommendation && item.recommendation.toLowerCase() === filterRec.toLowerCase())

    return matchesSearch && matchesFilter
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col bg-[#10121a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10 bg-[#141622]/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 font-bold text-lg">
              📜
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Saved Analyses History</h2>
              <p className="text-xs text-gray-400">View, search, or delete previously generated MVP reports</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-lg border border-white/10 hover:border-white/20 text-gray-400 hover:text-white flex items-center justify-center transition-colors"
            title="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Filter and Search Bar */}
        <div className="px-6 py-4 border-b border-white/5 bg-[#0e0f17] flex flex-col sm:flex-row gap-3 items-center justify-between">
          {/* Search Input */}
          <div className="relative w-full sm:w-72">
            <input
              type="text"
              placeholder="Search by name or ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#151724] border border-white/10 rounded-xl px-3.5 py-2 pl-9 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-amber-500/50 transition-colors"
            />
            <span className="absolute left-3 top-2.5 text-gray-500 text-sm">🔍</span>
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-2.5 text-xs text-gray-500 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-1.5 w-full sm:w-auto text-xs">
            {['all', 'Build', 'Test First', 'Pivot', 'Avoid', 'failed'].map((rec) => (
              <button
                key={rec}
                onClick={() => setFilterRec(rec)}
                className={`px-3 py-1.5 rounded-lg border transition-all font-medium ${
                  filterRec === rec
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm'
                    : 'bg-[#151724] text-gray-400 border-white/5 hover:border-white/20 hover:text-white'
                }`}
              >
                {rec === 'all' ? 'All Items' : rec}
              </button>
            ))}
          </div>
        </div>

        {/* Modal Body - List of items */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {loading ? (
            <div className="py-16 text-center text-gray-400 space-y-3">
              <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-sm">Loading saved analyses...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm text-center">
              {error}
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="py-16 text-center text-gray-500 space-y-3 border border-dashed border-white/10 rounded-2xl">
              <div className="text-3xl">💡</div>
              <p className="text-base font-medium text-gray-300">No matching analyses found</p>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                {items.length === 0
                  ? "You haven't run any MVP analyses yet. Create your first analysis from the home page!"
                  : 'Try clearing your search filters to view saved analyses.'}
              </p>
            </div>
          ) : (
            filteredItems.map((item) => (
              <div
                key={item.analysis_id}
                onClick={() => {
                  onClose()
                  navigate(`/analysis/${item.analysis_id}`)
                }}
                className="group relative p-4 rounded-xl bg-[#141622]/80 border border-white/10 hover:border-amber-500/40 hover:bg-[#181a28] transition-all duration-200 cursor-pointer flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-white group-hover:text-amber-300 transition-colors text-base truncate">
                      {item.idea_name}
                    </span>
                    <span className="font-mono text-xs text-gray-500 bg-white/5 px-2 py-0.5 rounded border border-white/5">
                      #{item.analysis_id.slice(0, 8)}
                    </span>
                    {item.is_demo && (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        Demo
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-gray-400 flex-wrap">
                    <span>Created: {formatDate(item.created_at)}</span>
                    {item.status === 'complete' ? (
                      <span className="text-emerald-400 font-medium">✓ Completed</span>
                    ) : item.status === 'failed' ? (
                      <span className="text-red-400 font-medium">✕ Failed</span>
                    ) : (
                      <span className="text-amber-400 font-medium animate-pulse">⏳ {item.status}...</span>
                    )}
                  </div>
                </div>

                {/* Score & Verdict badges */}
                <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end border-t sm:border-t-0 pt-3 sm:pt-0 border-white/5">
                  {item.opportunity_score !== undefined && item.opportunity_score !== null && (
                    <div className="flex items-center gap-2 bg-black/40 px-3 py-1.5 rounded-xl border border-white/5">
                      <span className="text-xs text-gray-400">Score:</span>
                      <span className="font-bold text-base text-white">{Math.round(item.opportunity_score)}/100</span>
                    </div>
                  )}

                  {item.recommendation && (
                    <span
                      className={`badge px-3 py-1 text-xs font-semibold rounded-lg ${recommendationBg(
                        item.recommendation
                      )}`}
                    >
                      <span className={recommendationColor(item.recommendation)}>{item.recommendation}</span>
                    </span>
                  )}

                  <button
                    onClick={(e) => handleDelete(item.analysis_id, e)}
                    disabled={deletingId === item.analysis_id}
                    className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all opacity-80 hover:opacity-100"
                    title="Delete analysis"
                  >
                    {deletingId === item.analysis_id ? '...' : '🗑️'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-white/10 bg-[#141622]/60 flex items-center justify-between text-xs text-gray-400">
          <span>Total saved: {items.length} analyses</span>
          <button
            onClick={fetchItems}
            className="hover:text-amber-400 flex items-center gap-1 transition-colors"
          >
            🔄 Refresh List
          </button>
        </div>
      </div>
    </div>
  )
}

export default SavedAnalysesModal
