import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import type { AnalysisResult, AnalysisListItem } from '../types'
import { recommendationBg, recommendationColor } from '../lib/utils'

interface Props {
  isOpen: boolean
  onClose: () => void
  onCountUpdate?: (count: number) => void
}

export const SavedAnalysesModal: React.FC<Props> = ({ isOpen, onClose, onCountUpdate }) => {
  const [items, setItems] = useState<AnalysisListItem[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')

  const loadData = async () => {
    setLoading(true)
    try {
      const data = await api.listAnalyses({ search, status: statusFilter || undefined })
      setItems(data)
      if (onCountUpdate) {
        // Send true count back to parent
        onCountUpdate(data.length)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen, search, statusFilter])

  if (!isOpen) return null

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!window.confirm('Delete this analysis permanently?')) return
    try {
      await api.deleteAnalysis(id)
      loadData()
    } catch (err) {
      alert('Failed to delete')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/40 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden verseo-card">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-700 font-bold text-lg shadow-sm">
              📜
            </div>
            <div>
              <h2 className="text-xl font-display font-bold text-gray-900 tracking-tight">Saved Analyses</h2>
              <p className="text-xs text-gray-500 font-mono">View past validation reports</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-gray-500 hover:text-gray-900 flex items-center justify-center transition-colors shadow-sm"
          >
            ✕
          </button>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 border-b border-gray-200 bg-white flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            placeholder="Search ideas..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 input-field shadow-inner"
          />
          <div className="flex gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-hide">
            {['', 'build', 'test_first', 'pivot', 'avoid'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 rounded-xl border text-xs font-mono font-semibold whitespace-nowrap transition-all ${
                  statusFilter === status
                    ? 'bg-gray-900 text-white border-gray-900 shadow-md'
                    : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50 hover:text-gray-900 shadow-sm'
                }`}
              >
                {status === '' ? 'ALL' : status.replace('_', ' ').toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-gray-50">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-sm">No analyses found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {items.map((item) => (
                <Link
                  key={item.analysis_id}
                  to={`/analysis/${item.analysis_id}`}
                  onClick={onClose}
                  className="group relative bg-white p-5 rounded-2xl border border-gray-200 hover:border-gray-400 hover:shadow-lg transition-all verseo-card-hover"
                >
                  <button
                    onClick={(e) => handleDelete(item.analysis_id, e)}
                    className="absolute top-4 right-4 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete"
                  >
                    🗑️
                  </button>
                  <div className="pr-6">
                    <h3 className="text-base font-display font-bold text-gray-900 truncate mb-1">
                      {item.idea_name}
                    </h3>
                    <p className="text-xs text-gray-500 line-clamp-2 mb-4 leading-relaxed">
                      {item.stage.replace(/_/g, ' ')}
                    </p>
                  </div>

                  <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                    <div className="flex items-center gap-2">
                      {item.recommendation ? (
                        <span className={`text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider ${recommendationBg(item.recommendation)}`}>
                          <span className={recommendationColor(item.recommendation)}>
                            {item.recommendation}
                          </span>
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-1 rounded-md bg-amber-50 text-amber-600 uppercase tracking-wider border border-amber-200">
                          {item.status}
                        </span>
                      )}
                      {item.opportunity_score !== undefined && (
                        <span className="text-xs font-mono font-bold text-gray-900 bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">
                          {item.opportunity_score}/100
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] font-mono text-gray-400">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SavedAnalysesModal
