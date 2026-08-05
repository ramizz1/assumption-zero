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
        className="badge bg-red-400/10 text-red-400 border-red-500/20 font-mono text-xs"
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
