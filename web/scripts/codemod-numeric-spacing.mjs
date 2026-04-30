#!/usr/bin/env node
/**
 * Codemod: numeric spacing utilities → semantic scale.
 *
 *   .p-16   → .p-lg
 *   .gap-8  → .gap-sm
 *   .m-24   → .m-2xl
 *
 * Also migrates legacy `var(--km-font-size-*)` aliases to `var(--ds-font-size-*)`.
 *
 * Scope: textual replacement across `.vue`, `.css`, `.scss` files. Word-boundary
 * regex ensures `16px`, `font-size: 16px`, etc. are not affected.
 *
 * Usage:
 *   node scripts/codemod-numeric-spacing.mjs --dry              # preview, default
 *   node scripts/codemod-numeric-spacing.mjs --apply            # write changes
 *   node scripts/codemod-numeric-spacing.mjs --apply --scope=apps/@ipr/magnet-admin
 *   node scripts/codemod-numeric-spacing.mjs --apply --scope=apps/@ipr/magnet-admin/src/components/Agents
 */

import { readFile, readdir, stat, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const webRoot = path.resolve(scriptDir, '..')

// Prefix → spacing-prefix map (kebab-friendly).
const PREFIXES = [
  'p', 'px', 'py', 'pt', 'pb', 'pl', 'pr',
  'm', 'mx', 'my', 'mt', 'mb', 'ml', 'mr',
  'gap', 'gap-x', 'gap-y',
]

// Numeric → semantic step. 6px is rounded up to `sm` (8px) per design review.
const NUMERIC_TO_SEMANTIC = {
  2: '2xs',
  4: 'xs',
  6: 'sm',
  8: 'sm',
  12: 'md',
  16: 'lg',
  20: 'xl',
  24: '2xl',
  32: '3xl',
  40: '4xl',
  48: '5xl',
  64: '6xl',
}

const KM_FONT_TO_DS = [
  // alias name → canonical
  ['xs', 'xs'],
  ['sm', 'sm'],
  ['caption', 'caption'],
  ['label', 'label'],
  ['body-lg', 'body-lg'],
  ['body', 'body'],
  ['h2', 'h2'],
  ['h1', 'h1'],
  ['display', 'display'],
]

const ignoredDirs = new Set(['.git', '.nx', '.yarn', 'coverage', 'dist', 'documentation', 'node_modules', '.venv', 'paraglide'])

const includedExts = new Set(['.vue', '.css', '.scss'])

function buildSpacingPattern() {
  // \b(p|px|...)-(2|4|...)\b
  const numericAlt = Object.keys(NUMERIC_TO_SEMANTIC).join('|')
  const prefixAlt = PREFIXES.map((p) => p.replace('-', '\\-')).join('|')
  return new RegExp(`\\b(${prefixAlt})-(${numericAlt})\\b`, 'g')
}

function buildKmFontPattern() {
  const aliasAlt = KM_FONT_TO_DS.map(([alias]) => alias.replace('-', '\\-')).join('|')
  return new RegExp(`var\\(\\s*--km-font-size-(${aliasAlt})\\b`, 'g')
}

// Other --km-* legacy alias families. Each maps `--km-<group>-<name>` → `--ds-<group>-<name>`
// 1:1 since the alias block in tokens/typography.css already pointed at the same canonical token.
const KM_LEGACY_VAR_PATTERNS = [
  /var\(\s*--km-font-(default|mono)\b/g,
  /var\(\s*--km-font-weight-([a-z]+)\b/g,
  /var\(\s*--km-line-height-([a-z]+)\b/g,
]

const SPACING_RE = buildSpacingPattern()
const KM_FONT_RE = buildKmFontPattern()

function applyReplacements(content) {
  let updated = content
  let spacingHits = 0
  let fontHits = 0

  updated = updated.replace(SPACING_RE, (match, prefix, num) => {
    spacingHits += 1
    return `${prefix}-${NUMERIC_TO_SEMANTIC[num]}`
  })

  updated = updated.replace(KM_FONT_RE, (_match, alias) => {
    fontHits += 1
    return `var(--ds-font-size-${alias}`
  })

  for (const re of KM_LEGACY_VAR_PATTERNS) {
    updated = updated.replace(re, (match) => {
      fontHits += 1
      return match.replace('--km-', '--ds-')
    })
  }

  return { updated, spacingHits, fontHits }
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
      if (includedExts.has(path.extname(dir))) out.push(dir)
      continue
    }
    if (!info.isDirectory()) continue
    const entries = await readdir(dir, { withFileTypes: true })
    for (const entry of entries) {
      if (entry.isDirectory() && ignoredDirs.has(entry.name)) continue
      const child = path.join(dir, entry.name)
      stack.push(child)
    }
  }
  return out.sort()
}

function parseArgs(argv) {
  const opts = { apply: false, scope: 'apps' }
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i]
    if (a === '--apply') opts.apply = true
    else if (a === '--dry') opts.apply = false
    else if (a.startsWith('--scope=')) opts.scope = a.split('=')[1]
    else if (a === '--help' || a === '-h') {
      console.log(`Usage: node scripts/codemod-numeric-spacing.mjs [--dry|--apply] [--scope=<rel-path>]\n`)
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
  let totalSpacing = 0
  let totalFont = 0
  let touched = 0

  for (const file of files) {
    const content = await readFile(file, 'utf8')
    const { updated, spacingHits, fontHits } = applyReplacements(content)
    if (spacingHits === 0 && fontHits === 0) continue
    totalSpacing += spacingHits
    totalFont += fontHits
    touched += 1

    const rel = path.relative(webRoot, file).split(path.sep).join('/')
    if (opts.apply) {
      if (updated !== content) {
        await writeFile(file, updated)
        console.log(`✔ ${rel}  (spacing: ${spacingHits}, km-font: ${fontHits})`)
      }
    } else {
      console.log(`  ${rel}  (spacing: ${spacingHits}, km-font: ${fontHits})`)
    }
  }

  const tag = opts.apply ? 'applied' : 'dry-run'
  console.log(`\nCodemod ${tag}: ${touched} files, ${totalSpacing} spacing replacements, ${totalFont} km-font replacements.`)
  if (!opts.apply) console.log(`Re-run with --apply to write changes.`)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
