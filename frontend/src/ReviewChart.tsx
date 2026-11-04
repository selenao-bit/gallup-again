import { useId, useState } from 'react'

interface ReviewRecord {
  record_id: string
  title: string
  fields: Record<string, unknown>
}

const LEFT = 44
const RIGHT = 736
const TOP = 24
const BOTTOM = 230

export default function ReviewChart({ reviews }: { reviews: readonly ReviewRecord[] }) {
  const descriptionId = useId()
  const [activeId, setActiveId] = useState<string | null>(null)
  const entries = [...reviews]
    .sort((a, b) => String(a.fields.review_period ?? a.title).localeCompare(String(b.fields.review_period ?? b.title)))
    .map((review, index) => {
      const raw = review.fields.rating_overall
      const score = typeof raw === 'number' && Number.isFinite(raw) && raw >= 1 && raw <= 5 ? raw : null
      return {
        id: review.record_id,
        period: String(review.fields.review_period ?? review.title),
        score,
        x: reviews.length === 1 ? (LEFT + RIGHT) / 2 : LEFT + index * (RIGHT - LEFT) / Math.max(reviews.length - 1, 1),
        y: score === null ? null : BOTTOM - (score - 1) * (BOTTOM - TOP) / 4,
      }
    })
  const points = entries.filter((point): point is typeof point & { score: number; y: number } => point.score !== null && point.y !== null)
  const segments: string[][] = []
  let segment: string[] = []
  for (const entry of entries) {
    if (entry.y === null) {
      if (segment.length > 1) segments.push(segment)
      segment = []
    } else {
      segment.push(`${entry.x},${entry.y}`)
    }
  }
  if (segment.length > 1) segments.push(segment)
  const active = points.find(point => point.id === activeId)
  const labelStep = Math.max(1, Math.ceil(entries.length / 14))
  const tooltipX = active ? Math.max(8, Math.min(active.x - 90, 572)) : 0
  const tooltipY = active ? (active.y > 90 ? active.y - 68 : active.y + 16) : 0

  if (!points.length) return <p className="muted">No overall review scores are recorded yet.</p>

  return <figure className="review-chart-figure">
    <svg className="review-chart" viewBox="0 0 760 278" role="group"
      aria-label="Recorded overall review ratings on a fixed 1 to 5 scale" aria-describedby={descriptionId}>
      <text className="review-axis-label" x={LEFT} y={12}>Overall rating (1–5)</text>
      {[1, 2, 3, 4, 5].map(score => {
        const y = BOTTOM - (score - 1) * (BOTTOM - TOP) / 4
        return <g key={score} aria-hidden="true">
          <line x1={LEFT} x2={RIGHT} y1={y} y2={y} className="review-grid-line" />
          <text className="review-axis-label" x={20} y={y + 4}>{score}</text>
        </g>
      })}
      {segments.map((values, index) => <polyline key={index} data-testid="review-trend-line"
        points={values.join(' ')} className="review-trend-line" aria-hidden="true" />)}
      {entries.map((entry, index) => (index % labelStep === 0 || index === entries.length - 1) &&
        <text key={entry.id} className="review-axis-label" x={entry.x} y={252} textAnchor="middle" aria-hidden="true">{entry.period}</text>)}
      {points.map(point => <g key={point.id} className="review-point" tabIndex={0} role="img"
        aria-label={`${point.period}: ${point.score.toFixed(2)} out of 5`}
        onMouseEnter={() => setActiveId(point.id)} onMouseLeave={() => setActiveId(null)}
        onFocus={() => setActiveId(point.id)} onBlur={() => setActiveId(null)}
        onClick={() => setActiveId(point.id)}
        onKeyDown={event => { if (event.key === 'Escape') setActiveId(null) }}>
        <circle className="review-hit" cx={point.x} cy={point.y} r={14} />
        <circle className="review-dot" cx={point.x} cy={point.y} r={point.id === activeId ? 6 : 4.5} />
      </g>)}
      {active && <g role="tooltip" className="review-tooltip" transform={`translate(${tooltipX} ${tooltipY})`}>
        <rect width={180} height={54} rx={7} />
        <text x={12} y={20} className="review-tooltip-period">{active.period}</text>
        <text x={12} y={40}>Overall rating: {active.score.toFixed(2)} / 5</text>
      </g>}
    </svg>
    <figcaption id={descriptionId}>Hover over a point, or focus it with the keyboard, to see the quarter and score.</figcaption>
  </figure>
}
