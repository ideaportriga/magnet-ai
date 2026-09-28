/**
 * Price cell text for the models list, e.g. `$2.5 / 1M tokens`.
 *
 * Prices are stored as decimal strings and shown as entered — rounding would
 * hide the tail of sub-cent prices like `0.000125`. Unit count and name fall
 * back to the same defaults the model drawer's Pricing tab uses.
 */
const DEFAULT_PRICE_UNIT_COUNT = 1000000
const DEFAULT_PRICE_UNIT_NAME = 'tokens'

export function formatUnitCount(count: number): string {
  if (count >= 1000000 && count % 1000000 === 0) return `${count / 1000000}M`
  if (count >= 1000 && count % 1000 === 0) return `${count / 1000}K`
  return String(count)
}

export function formatModelPrice(price: string | number | null | undefined, unitCount?: number | null, unitName?: string | null): string | null {
  if (price == null || String(price).trim() === '') return null
  const count = formatUnitCount(unitCount || DEFAULT_PRICE_UNIT_COUNT)
  return `$${String(price).trim()} / ${count} ${unitName || DEFAULT_PRICE_UNIT_NAME}`
}
