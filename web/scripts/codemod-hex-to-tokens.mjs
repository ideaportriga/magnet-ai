#!/usr/bin/env node
/**
 * Codemod: hardcoded hex colors → DS color tokens.
 *
 * Two passes:
 *   1. Exact / near-match hex → semantic token replacement.
 *   2. The remaining hex stay as-is (mostly domain-specific palettes for
 *      deep research / agent visualizations that need their own DS tokens
 *      before mass-migration).
 *
 * Word-boundary regex ensures we replace only standalone hex literals in
 * Vue scoped CSS / .css files. Token-definition files (`tokens/`,
 * `themes/`, `utilities/`, `composition/`, `reset/`) are skipped — they
 * legitimately contain hex literals.
 *
 * Usage:
 *   node scripts/codemod-hex-to-tokens.mjs --dry            # preview, default
 *   node scripts/codemod-hex-to-tokens.mjs --apply
 *   node scripts/codemod-hex-to-tokens.mjs --apply --scope=apps/@ipr/magnet-admin
 */

import { readFile, readdir, stat, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const webRoot = path.resolve(scriptDir, '..')

/**
 * Hex (lowercase, normalised to 6 digits) → token expression.
 * Each entry maps a literal that's directly equivalent to a DS semantic role.
 * Entries are prioritised by frequency and clarity of intent.
 */
const HEX_TO_TOKEN = {
  // ─── Pure white / black ──────────────────────────────────────────────
  '#fff':     'var(--ds-color-static-white)',
  '#ffffff':  'var(--ds-color-static-white)',
  '#000':     'var(--ds-color-static-black)',
  '#000000':  'var(--ds-color-static-black)',

  // ─── Greyscale family — maps to --ds-color-gray-{50..950} ────────────
  '#171717':  'var(--ds-color-gray-950)',
  '#1a1a1a':  'var(--ds-color-gray-900)',
  '#212121':  'var(--ds-color-gray-900)',
  '#2a2a2a':  'var(--ds-color-gray-800)',
  '#2d3436':  'var(--ds-color-gray-800)',
  '#424242':  'var(--ds-color-gray-700)',
  '#5c5c5c':  'var(--ds-color-gray-600)',
  '#616161':  'var(--ds-color-gray-600)',
  '#757575':  'var(--ds-color-gray-500)',
  '#7a7a86':  'var(--ds-color-gray-500)',
  '#808080':  'var(--ds-color-gray-500)',
  '#959ea4':  'var(--ds-color-gray-400)',
  '#9e9e9e':  'var(--ds-color-gray-400)',
  '#bdbdbd':  'var(--ds-color-gray-300)',
  '#c4c7cf':  'var(--ds-color-gray-300)',
  '#d3d3d3':  'var(--ds-color-gray-200)',
  '#d6d6e1':  'var(--ds-color-gray-200)',
  '#e0e0e0':  'var(--ds-color-gray-200)',
  '#e8e8e8':  'var(--ds-color-gray-100)',
  '#eaeaf6':  'var(--ds-color-gray-100)',
  '#f0f0f0':  'var(--ds-color-gray-100)',
  '#f0f1f3':  'var(--ds-color-gray-100)',
  '#f5f5f5':  'var(--ds-color-gray-50)',
  '#f5f6f7':  'var(--ds-color-gray-50)',
  '#f7f7fc':  'var(--ds-color-gray-50)',
  '#f8f9fa':  'var(--ds-color-gray-50)',
  '#fafafa':  'var(--ds-color-gray-50)',

  // ─── Brand primary anchor ────────────────────────────────────────────
  '#6840c2':  'var(--ds-color-primary)',

  // ─── Status — danger / success / warning / info ──────────────────────
  '#c11c1c':  'var(--ds-color-danger-700)',
  '#cc1d1d':  'var(--ds-color-danger-600)',
  '#e62222':  'var(--ds-color-danger-solid)',
  '#a3171d':  'var(--ds-color-danger-700)',
  '#ffecec':  'var(--ds-color-danger-soft)',

  '#2e7d42':  'var(--ds-color-success-on-soft)',
  '#00a876':  'var(--ds-color-success-solid)',
  '#00714f':  'var(--ds-color-success-on-soft)',
  '#bdf2d5':  'var(--ds-color-success-200)',
  '#e9fce9':  'var(--ds-color-success-100)',

  '#d99500':  'var(--ds-color-warning-solid)',
  '#fcec87':  'var(--ds-color-warning-200)',
  '#fff9d4':  'var(--ds-color-warning-100)',
  '#6b4a00':  'var(--ds-color-warning-on-soft)',

  '#1aa7c4':  'var(--ds-color-info-solid)',
  '#0b6c80':  'var(--ds-color-info-on-soft)',
  '#e3f7fb':  'var(--ds-color-info-soft)',
}

const ignoredDirs = new Set([
  '.git', '.nx', '.yarn', 'coverage', 'dist', 'documentation', 'node_modules', '.venv', 'paraglide',
])

// Token / theme files are sources of truth for hex literals — skip.
const SKIPPED_PATH_FRAGMENTS = [
  '/packages/ds/src/tokens/',
  '/packages/ds/src/utilities/',
  '/packages/ds/src/composition/',
  '/packages/ds/src/reset/',
  '/packages/themes/',
]

const includedExts = new Set(['.vue', '.css', '.scss'])

/**
 * Build a single regex of `#XXX` literals (with word boundaries).
 * Maps the matched hex (lower-cased + 3-digit-expanded) back to its token.
 */
function buildPattern(map) {
  const escaped = Object.keys(map).map((k) => k.replace(/^#/, '#')).join('|')
  return new RegExp(`(?<!\\w)(${escaped})(?!\\w)`, 'gi')
}

const PATTERN = buildPattern(HEX_TO_TOKEN)

function applyReplacements(content) {
  let updated = content
  let hits = 0
  updated = updated.replace(PATTERN, (match) => {
    const lower = match.toLowerCase()
    // Try the literal as-is, then expand 3-digit shorthand.
    const token = HEX_TO_TOKEN[lower] || HEX_TO_TOKEN[expandShort(lower)]
    if (!token) return match
    hits += 1
    return token
  })
  return { updated, hits }
}

function expandShort(hex) {
  if (hex.length !== 4) return hex // already #xxxxxx
  const [, a, b, c] = hex
  return `#${a}${a}${b}${b}${c}${c}`
}

async function listFiles(root) {
  const out = []
  if (!existsSync(root)) return out
  const stack = [root]
  while (stack.length) {
    const dir = stack.pop()
    const info = await stat(dir).catch(() => null)
    if (!info) continue
    if (info.isFile()) {
      if (includedExts.has(path.extname(dir)) && !shouldSkip(dir)) out.push(dir)
      continue
    }
    if (!info.isDirectory()) continue
    const entries = await readdir(dir, { withFileTypes: true })
    for (const entry of entries) {
      if (entry.isDirectory() && ignoredDirs.has(entry.name)) continue
      stack.push(path.join(dir, entry.name))
    }
  }
  return out.sort()
}

function shouldSkip(file) {
  const normalised = file.replaceAll(path.sep, '/')
  return SKIPPED_PATH_FRAGMENTS.some((fragment) => normalised.includes(fragment))
}

function parseArgs(argv) {
  const opts = { apply: false, scope: 'apps' }
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i]
    if (a === '--apply') opts.apply = true
    else if (a === '--dry') opts.apply = false
    else if (a.startsWith('--scope=')) opts.scope = a.split('=')[1]
    else if (a === '--help' || a === '-h') {
      console.log('Usage: node scripts/codemod-hex-to-tokens.mjs [--dry|--apply] [--scope=<rel-path>]\n')
      process.exit(0)
    }
  }
  return opts
}

async function main() {
  const opts = parseArgs(process.argv.slice(2))
  const root = path.resolve(webRoot, opts.scope)
  if (!existsSync(root)) {
    console.error(`scope path not found: ${opts.scope}`)
    process.exit(1)
  }

  const files = await listFiles(root)
  let totalHits = 0
  let touched = 0

  for (const file of files) {
    const content = await readFile(file, 'utf8')
    const { updated, hits } = applyReplacements(content)
    if (hits === 0) continue
    totalHits += hits
    touched += 1
    const rel = path.relative(webRoot, file).split(path.sep).join('/')
    if (opts.apply) {
      await writeFile(file, updated)
      console.log(`✔ ${rel}  (hex→token: ${hits})`)
    } else {
      console.log(`  ${rel}  (hex→token: ${hits})`)
    }
  }

  const tag = opts.apply ? 'applied' : 'dry-run'
  console.log(`\nCodemod ${tag}: ${touched} files, ${totalHits} replacements (across ${Object.keys(HEX_TO_TOKEN).length} known mappings).`)
  if (!opts.apply) console.log('Re-run with --apply to write changes.')
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
