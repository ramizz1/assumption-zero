/** Inline citation badge that links to the evidence source */
import type { EvidenceItem } from '../types'

interface Props {
  evidenceId: string
  evidence: EvidenceItem[]
}

export default function CitationBadge({ evidenceId, evidence }: Props) {
  const item = evidence.find((e) => e.evidence_id === evidenceId)

  if (!item) {
    return (
      <span
        className="badge bg-red-50 text-red-700 border-red-200 font-mono text-xs"
        title="Invalid citation — evidence not found"
      >
        {evidenceId} ⚠
      </span>
    )
  }

  return (
    <a
      href={item.url.startsWith('demo://') ? '#sources' : item.url}
      target={item.url.startsWith('demo://') ? '_self' : '_blank'}
      rel="noopener noreferrer"
      className="citation-badge"
      title={`${item.title}\n${item.passage.slice(0, 150)}`}
      id={`cite-${evidenceId}`}
    >
      {evidenceId}
    </a>
  )
}
