import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ReviewChart from './ReviewChart'

const review = (period: string, score: number | null) => ({ record_id: `review:${period}`, title: period, fields: { review_period: period, rating_overall: score } })

describe('review history chart', () => {
  it('connects chronologically sorted points and displays hover scores immediately', () => {
    const reviews = [review('2025-Q1', 4.25), review('2024-Q3', 3.5), review('2024-Q4', 3.75)]
    render(<ReviewChart reviews={reviews} />)
    const line = screen.getByTestId('review-trend-line')
    expect(line.getAttribute('points')?.split(' ')).toHaveLength(3)
    expect(reviews[0].fields.review_period).toBe('2025-Q1')
    const point = screen.getByRole('img', { name: '2024-Q4: 3.75 out of 5' })
    fireEvent.mouseEnter(point)
    expect(screen.getByRole('tooltip')).toHaveTextContent('2024-Q4')
    expect(screen.getByRole('tooltip')).toHaveTextContent('Overall rating: 3.75 / 5')
    fireEvent.mouseLeave(point)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('shows keyboard-focus scores and keeps the scale fixed at one to five', () => {
    render(<ReviewChart reviews={[review('2025-Q1', 1), review('2025-Q2', 5)]} />)
    const point = screen.getByRole('img', { name: '2025-Q2: 5.00 out of 5' })
    fireEvent.focus(point)
    expect(screen.getByRole('tooltip')).toHaveTextContent('5.00 / 5')
    fireEvent.keyDown(point, { key: 'Escape' })
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    expect(screen.getByRole('group', { name: /fixed 1 to 5 scale/ })).toBeVisible()
  })

  it('does not invent scores or connect through a missing review value', () => {
    render(<ReviewChart reviews={[review('2024-Q3', 3), review('2024-Q4', null), review('2025-Q1', 4)]} />)
    expect(screen.getAllByRole('img')).toHaveLength(2)
    expect(screen.queryByTestId('review-trend-line')).not.toBeInTheDocument()
  })
})
