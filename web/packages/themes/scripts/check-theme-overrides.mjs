#!/usr/bin/env node
/**
 * Validates brand theme files in `packages/themes/src/themes/<theme>/theme.css`
 * against the contract in `packages/themes/THEME_CONTRACT.md`.
 *
 * Allowed: --ds-color-*, --ds-brand-*, --ds-font-default, --ds-font-mono.
 * Forbidden: --ds-space-*, --ds-radius-*, --ds-z-*, --ds-shadow-*,
 *           --ds-duration-*, --ds-ease-*, --ds-transition-*, --ds-font-size-*,
 *           --ds-line-height-*, --ds-font-weight-*, --ds-tracking-*, --ds-text-*,
 *           --ds-field-*, --ds-btn-height-*, --ds-dialog-*, --ds-table-row-*,
 *           --ds-loader-*.
 * Warned (legacy non-namespaced): everything outside the --ds-* namespace.
 *
 * Usage:
 *   node packages/themes/scripts/check-theme-overrides.mjs           # validate, exit 1 on forbidden
 *   node packages/themes/scripts/check-theme-overrides.mjs --report  # full report (no exit code)
 */

import { readFile, readdir, stat } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const themesRoot = path.resolve(scriptDir, '..', 'src', 'themes')

const ALLOWED_PATTERNS = [
  /^--ds-color-/,
  /^--ds-brand-/,
  /^--ds-font-default$/,
  /^--ds-font-mono$/,
]

const FORBIDDEN_PATTERNS = [
  { pattern: /^--ds-space-/,        label: 'spacing scale' },
  { pattern: /^--ds-radius-/,       label: 'radius scale' },
  { pattern: /^--ds-z-/,            label: 'z-index scale' },
  { pattern: /^--ds-shadow-/,       label: 'elevation' },
  { pattern: /^--ds-duration-/,     label: 'motion duration' },
  { pattern: /^--ds-ease-/,         label: 'motion ease' },
  { pattern: /^--ds-transition-/,   label: 'transition preset' },
  { pattern: /^--ds-font-size-/,    label: 'typography size' },
  { pattern: /^--ds-line-height-/,  label: 'typography line-height' },
  { pattern: /^--ds-font-weight-/,  label: 'typography weight' },
  { pattern: /^--ds-tracking-/,     label: 'typography tracking' },
  { pattern: /^--ds-text-/,         label: 'typography role' },
  { pattern: /^--ds-field-/,        label: 'field dimension' },
  { pattern: /^--ds-btn-height/,    label: 'button height' },
  { pattern: /^--ds-dialog-/,       label: 'dialog dimension' },
  { pattern: /^--ds-table-row/,     label: 'table row dimension' },
  { pattern: /^--ds-loader-/,       label: 'loader dimension' },
]

function classify(name) {
  if (!name.startsWith('--ds-')) return { kind: 'legacy' }
  for (const f of FORBIDDEN_PATTERNS) {
    if (f.pattern.test(name)) return { kind: 'forbidden', label: f.label }
  }
  for (const a of ALLOWED_PATTERNS) {
    if (a.test(name)) return { kind: 'allowed' }
  }
  return { kind: 'unknown' }
}

function extractDeclarations(css) {
  // Match `--name: value;` declarations only at the start of trimmed lines.
  const decls = []
  const re = /^\s*(--[a-zA-Z][a-zA-Z0-9_-]*)\s*:/gm
  let m
  while ((m = re.exec(css)) !== null) {
    decls.push(m[1])
  }
  return decls
}

async function listThemes() {
  if (!existsSync(themesRoot)) return []
  const entries = await readdir(themesRoot, { withFileTypes: true })
  const themes = []
  for (const entry of entries) {
    if (!entry.isDirectory()) continue
    const themePath = path.join(themesRoot, entry.name, 'theme.css')
    if (existsSync(themePath)) themes.push({ name: entry.name, path: themePath })
  }
  return themes.sort((a, b) => a.name.localeCompare(b.name))
}

async function audit() {
  const themes = await listThemes()
  const results = []

  for (const theme of themes) {
    const content = await readFile(theme.path, 'utf8')
    const decls = extractDeclarations(content)
    const seen = new Set()

    const allowed = []
    const forbidden = []
    const legacy = []
    const unknown = []

    for (const name of decls) {
      if (seen.has(name)) continue
      seen.add(name)
      const c = classify(name)
      if (c.kind === 'allowed') allowed.push(name)
      else if (c.kind === 'forbidden') forbidden.push({ name, label: c.label })
      else if (c.kind === 'legacy') legacy.push(name)
      else unknown.push(name)
    }

    results.push({
      theme: theme.name,
      file: path.relative(path.resolve(scriptDir, '..', '..', '..'), theme.path).split(path.sep).join('/'),
      allowed,
      forbidden,
      legacy,
      unknown,
    })
  }

  return results
}

function renderReport(results) {
  const lines = ['# Theme Overrides Report', '']
  for (const r of results) {
    lines.push(`## ${r.theme}`, '', `Source: \`${r.file}\``, '')
    lines.push(`- Allowed overrides: ${r.allowed.length}`)
    lines.push(`- Forbidden overrides: ${r.forbidden.length}`)
    lines.push(`- Legacy non-namespaced: ${r.legacy.length}`)
    lines.push(`- Unknown --ds-* (not in contract): ${r.unknown.length}`)
    lines.push('')
    if (r.forbidden.length > 0) {
      lines.push('### Forbidden')
      for (const f of r.forbidden) lines.push(`- \`${f.name}\` (${f.label})`)
      lines.push('')
    }
    if (r.unknown.length > 0) {
      lines.push('### Unknown --ds-*')
      for (const n of r.unknown) lines.push(`- \`${n}\``)
      lines.push('')
    }
    if (r.legacy.length > 0) {
      lines.push('### Legacy non-namespaced (warn)')
      for (const n of r.legacy) lines.push(`- \`${n}\``)
      lines.push('')
    }
  }
  return lines.join('\n') + '\n'
}

function reportAndExit(results, opts) {
  const totalForbidden = results.reduce((s, r) => s + r.forbidden.length, 0)
  const totalUnknown = results.reduce((s, r) => s + r.unknown.length, 0)
  const totalLegacy = results.reduce((s, r) => s + r.legacy.length, 0)

  if (opts.report) {
    process.stdout.write(renderReport(results))
    return
  }

  if (totalForbidden === 0 && totalUnknown === 0) {
    console.log(
      `theme-overrides: OK (${results.length} themes, ${totalLegacy} legacy non-namespaced ` +
      `vars are warn-only).`,
    )
    return
  }

  console.error('theme-overrides: contract violations\n')
  for (const r of results) {
    if (r.forbidden.length === 0 && r.unknown.length === 0) continue
    console.error(`# ${r.theme} (${r.file})`)
    for (const f of r.forbidden) console.error(`  forbidden: ${f.name} (${f.label})`)
    for (const n of r.unknown) console.error(`  unknown:   ${n}`)
    console.error('')
  }
  process.exitCode = 1
}

const args = process.argv.slice(2)
const opts = { report: args.includes('--report') }

const results = await audit()
reportAndExit(results, opts)
