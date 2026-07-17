import {describe, expect, it} from 'vitest'
import {compareDates, formatDate, string_to_html} from '@/utils'

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
})
