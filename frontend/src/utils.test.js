import {describe, expect, it} from 'vitest'
import {compare_dates, string_to_html} from './utils'

describe('utility helpers', () => {
  it('sorts dates from oldest to newest', () => {
    expect(compare_dates('31/12/2025', '01/01/2026')).toBeLessThan(0)
    expect(compare_dates('01/01/2026', '01/01/2026')).toBe(0)
  })

  it('formats links, line breaks, bold text, and strikethrough text', () => {
    expect(string_to_html('*bold*\n^done^ https://github.com/vuejs/core'))
      .toContain('<b>bold</b><br><s>done</s>')
    expect(string_to_html('https://github.com/vuejs/core')).toContain('gh-vuejs-core')
  })
})
