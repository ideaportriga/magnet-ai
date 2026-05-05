/**
 * Filter transforms for `<km-filter-bar>` consumers.
 *
 * The bar emits a flat map of raw user selections keyed by `config[key]`.
 * Backends accept different shapes:
 *  - `/observability/monitoring/{rag,llm,agent}` POST endpoints expect a
 *    MongoDB-style `FilterObject` with `$eq` / `$in` / `$gte` operators.
 *  - `/traces` and other GET endpoints expect flat camelCase query params
 *    like `statusIn`, `startTimeAfter`.
 *
 * `timePeriod` filters carry an ISO 8601 duration (`P1D`, `PT15M`, …) —
 * the transforms convert those to a `now() - duration` timestamp.
 */

import { DateTime, Duration } from 'luxon'

export interface FilterConf {
  key: string
  type?: string
  field?: string
  multiple?: boolean
  customLogic?: (value: unknown) => unknown
  // Other config fields are ignored by the transforms.
  [k: string]: unknown
}

function unwrapValue(v: unknown): unknown {
  if (v && typeof v === 'object' && !Array.isArray(v) && 'value' in (v as Record<string, unknown>)) {
    return (v as { value: unknown }).value
  }
  return v
}

function toCamelCase(str: string): string {
  return str.replace(/[-_](.)/g, (_, c: string) => c.toUpperCase())
}

function isEmpty(val: unknown): boolean {
  if (val == null) return true
  if (Array.isArray(val) && val.length === 0) return true
  return false
}

/**
 * Convert raw filter selections to a MongoDB-style FilterObject for POST
 * bodies (e.g. observability monitoring endpoints).
 */
export function toMongoFilter(
  active: Record<string, unknown>,
  config: Record<string, FilterConf>,
): Record<string, unknown> {
  const conditions: Record<string, unknown>[] = []
  let searchString: string | null = null

  for (const key in config) {
    const c = config[key]
    const val = active[key]
    if (isEmpty(val)) continue

    if (c.customLogic) {
      const res = c.customLogic(val)
      if (Array.isArray(res)) {
        for (const cond of res) conditions.push(cond as Record<string, unknown>)
      } else if (res != null) {
        conditions.push(res as Record<string, unknown>)
      }
      continue
    }

    if (c.type === 'timePeriod') {
      const isoDur = String(unwrapValue(val))
      const duration = Duration.fromISO(isoDur)
      if (!duration.isValid) continue
      const dateThreshold = DateTime.now().minus(duration).toISO()
      const fieldName = c.field || key
      if (dateThreshold) conditions.push({ [fieldName]: { $gte: dateThreshold } })
      continue
    }

    if (c.type === 'search') {
      const v = unwrapValue(val)
      if (v != null && v !== '') searchString = String(v)
      continue
    }

    if (c.multiple) {
      const arr = Array.isArray(val) ? val : [val]
      const values = arr.map((item) => unwrapValue(item)).filter((v) => v !== undefined)
      if (values.length) conditions.push({ [c.key]: { $in: values } })
      continue
    }

    const v = unwrapValue(val)
    if (Array.isArray(v)) {
      if (v.length) conditions.push({ [c.key]: { $in: v } })
    } else if (v !== undefined) {
      conditions.push({ [c.key]: { $eq: v } })
    }
  }

  const result: Record<string, unknown> = {}
  if (conditions.length === 1) Object.assign(result, conditions[0])
  else if (conditions.length > 1) result.$and = conditions
  if (searchString) result.searchString = searchString
  return result
}

/**
 * Convert raw filter selections to flat camelCase query params for GET
 * endpoints (e.g. `/traces?statusIn=…&startTimeAfter=…`).
 */
export function toSqlFilter(
  active: Record<string, unknown>,
  config: Record<string, FilterConf>,
): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  let searchString: string | null = null

  for (const key in config) {
    const c = config[key]
    const val = active[key]
    if (isEmpty(val)) continue

    if (c.type === 'timePeriod') {
      const isoDur = String(unwrapValue(val))
      const duration = Duration.fromISO(isoDur)
      if (!duration.isValid) continue
      const dateThreshold = DateTime.now().minus(duration).toISO()
      const fieldName = c.field || key
      if (dateThreshold) result[`${toCamelCase(fieldName)}After`] = dateThreshold
      continue
    }

    if (c.type === 'search') {
      const v = unwrapValue(val)
      if (v != null && v !== '') searchString = String(v)
      continue
    }

    if (c.multiple) {
      const arr = Array.isArray(val) ? val : [val]
      const values = arr.map((item) => unwrapValue(item)).filter((v) => v !== undefined)
      if (values.length) result[`${toCamelCase(c.key)}In`] = values
      continue
    }

    const v = unwrapValue(val)
    if (v !== undefined) result[c.key] = v
  }

  if (searchString) result.searchString = searchString
  return result
}
