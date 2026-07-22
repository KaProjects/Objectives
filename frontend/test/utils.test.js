import {describe, expect, it} from 'vitest'
import {compareDates, formatDate, isDeadlineClose, isDueOrOverdue, parseIsoDate, sortKeyResultsByDeadline, string_to_html} from '@/utils'

describe('utility helpers', () => {
  it('sorts dates from oldest to newest', () => {
    expect(compareDates('2025-12-31', '2026-01-01')).toBeLessThan(0)
    expect(compareDates('2026-01-01', '2026-01-01')).toBe(0)
    expect(formatDate('2026-01-01')).toBe('01/01/2026')
  })

  it('formats links, line breaks, bold text, and strikethrough text', () => {
    expect(string_to_html('*bold*\n^done^ https://github.com/vuejs/core'))
      .toContain('<b>bold</b><br><s>done</s>')
    expect(string_to_html('https://github.com/vuejs/core')).toContain('gh-vuejs-core')
  })

  it('formats each strikethrough pair independently', () => {
    expect(string_to_html('^first^ and ^second^')).toBe('<s>first</s> and <s>second</s>')
  })

  it('removes unsafe markup before it reaches v-html', () => {
    const html = string_to_html('Hello <img src=x onerror="alert(1)"><script>alert(1)</script>')

    expect(html).toBe('Hello ')
    expect(html).not.toContain('onerror')
    expect(html).not.toContain('<script')
  })

  it('accepts only valid ISO dates and sorts missing deadlines last', () => {
    expect(parseIsoDate('2026-02-29')).toBeNull()
    expect(parseIsoDate('2026-02-28')).toBe('2026-02-28')
    expect(parseIsoDate('28/02/2026')).toBeNull()

    expect(sortKeyResultsByDeadline([
      {id: 1, t: 'not a date'},
      {id: 2, t: '2026-10-01'},
      {id: 3, t: '2026-01-01'},
      {id: 4, t: ''},
    ]).map((keyResult) => keyResult.id)).toEqual([3, 2, 1, 4])
  })

  it('marks only valid deadlines that are today or in the past', () => {
    const today = new Date('2026-07-19T12:00:00+02:00')

    expect(isDueOrOverdue('2026-07-18', today)).toBe(true)
    expect(isDueOrOverdue('2026-07-19', today)).toBe(true)
    expect(isDueOrOverdue('2026-07-20', today)).toBe(false)
    expect(isDueOrOverdue('soon', today)).toBe(false)
  })

  it('marks deadlines in the next four weeks as close', () => {
    const januaryThirtyFirst = new Date('2026-01-31T12:00:00+01:00')

    expect(isDeadlineClose('2026-02-28', januaryThirtyFirst)).toBe(true)
    expect(isDeadlineClose('2026-03-01', januaryThirtyFirst)).toBe(false)
    expect(isDeadlineClose('2026-01-31', januaryThirtyFirst)).toBe(false)
  })
})
