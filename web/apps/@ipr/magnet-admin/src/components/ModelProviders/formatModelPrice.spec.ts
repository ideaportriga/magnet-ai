import { describe, expect, it } from 'vitest'
import { formatModelPrice, formatUnitCount } from './formatModelPrice'

describe('formatUnitCount', () => {
  it('abbreviates round millions and thousands', () => {
    expect(formatUnitCount(1000000)).toBe('1M')
    expect(formatUnitCount(2000000)).toBe('2M')
    expect(formatUnitCount(1000)).toBe('1K')
  })

  it('keeps counts that are not round as plain numbers', () => {
    expect(formatUnitCount(1)).toBe('1')
    expect(formatUnitCount(1500)).toBe('1500')
  })
})

describe('formatModelPrice', () => {
  it('returns null when no price is set', () => {
    expect(formatModelPrice(null)).toBeNull()
    expect(formatModelPrice(undefined)).toBeNull()
    expect(formatModelPrice('')).toBeNull()
    expect(formatModelPrice('  ')).toBeNull()
  })

  it('defaults to per 1M tokens', () => {
    expect(formatModelPrice('2.5')).toBe('$2.5 / 1M tokens')
    expect(formatModelPrice('2.5', null, null)).toBe('$2.5 / 1M tokens')
  })

  it('shows the stored price without rounding', () => {
    expect(formatModelPrice('0.000125', 1000, 'characters')).toBe('$0.000125 / 1K characters')
  })

  it('keeps a zero price', () => {
    expect(formatModelPrice('0')).toBe('$0 / 1M tokens')
    expect(formatModelPrice(0)).toBe('$0 / 1M tokens')
  })

  it('uses the stored unit count and name', () => {
    expect(formatModelPrice('0.01', 1, 'queries')).toBe('$0.01 / 1 queries')
  })
})
