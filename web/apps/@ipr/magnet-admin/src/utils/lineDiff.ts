/**
 * Tiny line-diff utility — no external dependency.
 *
 * Computes a unified diff between two multi-line strings via LCS
 * (Longest Common Subsequence). Returns a flat list of hunks where each
 * line is tagged `'equal'` (context), `'del'` (left only), or `'add'`
 * (right only) — same shape as a git-style unified diff, simple to render.
 *
 * Complexity O(N·M); use only on snapshots that fit comfortably in memory
 * (audit-log payloads are JSON of a single entity, so this is fine).
 */

export type LineKind = 'equal' | 'del' | 'add'

export interface DiffLine {
  kind: LineKind
  /** Line number in the BEFORE side (1-based), null for `add`. */
  before: number | null
  /** Line number in the AFTER side (1-based), null for `del`. */
  after: number | null
  text: string
}

/**
 * Build a unified diff of two strings split by `\n`. Trailing newlines are
 * preserved as empty lines so the output round-trips through `.join('\n')`.
 */
export function unifiedLineDiff(before: string, after: string): DiffLine[] {
  const a = before.split('\n')
  const b = after.split('\n')

  // ── LCS table ──────────────────────────────────────────────────────
  const n = a.length
  const m = b.length
  // dp[i][j] = LCS length of a[i:] vs b[j:]
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }

  // ── Walk the table to emit lines in order ──────────────────────────
  const out: DiffLine[] = []
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({ kind: 'equal', before: i + 1, after: j + 1, text: a[i] })
      i++
      j++
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.push({ kind: 'del', before: i + 1, after: null, text: a[i] })
      i++
    } else {
      out.push({ kind: 'add', before: null, after: j + 1, text: b[j] })
      j++
    }
  }
  while (i < n) {
    out.push({ kind: 'del', before: i + 1, after: null, text: a[i] })
    i++
  }
  while (j < m) {
    out.push({ kind: 'add', before: null, after: j + 1, text: b[j] })
    j++
  }
  return out
}

/**
 * Collapse long runs of context lines into "… N unchanged lines …" markers.
 * Returns the diff with synthetic separator entries (kind=`equal`, marker
 * text starts with `@@`) so the renderer can style them differently.
 */
export interface DiffHunkSeparator {
  kind: 'separator'
  collapsed: number
}

export type DiffEntry = DiffLine | DiffHunkSeparator

export function collapseContext(
  diff: DiffLine[],
  contextRadius = 3,
): DiffEntry[] {
  // Mark every line that's within `contextRadius` of a change as "kept".
  const keep: boolean[] = diff.map((l) => l.kind !== 'equal')
  for (let i = 0; i < diff.length; i++) {
    if (diff[i].kind === 'equal') continue
    for (
      let k = Math.max(0, i - contextRadius);
      k <= Math.min(diff.length - 1, i + contextRadius);
      k++
    ) {
      keep[k] = true
    }
  }

  const result: DiffEntry[] = []
  let collapsed = 0
  for (let i = 0; i < diff.length; i++) {
    if (keep[i]) {
      if (collapsed > 0) {
        result.push({ kind: 'separator', collapsed })
        collapsed = 0
      }
      result.push(diff[i])
    } else {
      collapsed++
    }
  }
  if (collapsed > 0) {
    result.push({ kind: 'separator', collapsed })
  }
  return result
}

/**
 * Convert an arbitrary value into the canonical text form used for diffing.
 * Strings pass through as-is; everything else is pretty-printed JSON.
 */
export function toDiffText(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}
