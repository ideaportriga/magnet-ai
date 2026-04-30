#!/usr/bin/env node

import { existsSync } from 'node:fs'
import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  applyTemplateVisualPropAllowlist,
  countTemplateVisualPropAllowlist,
} from './template-visual-prop-allowlist.mjs'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const webRoot = path.resolve(scriptDir, '..')
const repoRoot = path.resolve(webRoot, '..')

const scanEntries = [
  'apps',
  'packages',
  'package.json',
]

const ignoredDirs = new Set([
  '.git',
  '.nx',
  '.yarn',
  'coverage',
  'dist',
  'documentation',
  'node_modules',
])

const ignoredPathFragments = [
  '/src/paraglide/',
]

const sourceExtensions = new Set([
  '.cjs',
  '.css',
  '.js',
  '.json',
  '.jsx',
  '.mjs',
  '.sass',
  '.scss',
  '.styl',
  '.ts',
  '.tsx',
  '.vue',
])

const metrics = [
  {
    key: 'directQuasarImports',
    label: 'Direct quasar imports',
    description: "Imports from 'quasar' or 'quasar/*'. Must stay at zero.",
    pattern: /(?:from\s+['"]quasar['"]|import\s+[^'"\n]*['"]quasar['"]|from\s+['"]quasar\/[^'"]+['"]|import\s+[^'"\n]*['"]quasar\/[^'"]+['"])/g,
    content: 'raw',
  },
  {
    key: 'quasarExtrasRefs',
    label: '@quasar/extras references',
    description: 'Remaining icon/font package references to remove.',
    pattern: /@quasar\/extras/g,
    content: 'raw',
  },
  {
    key: 'vClosePopup',
    label: 'v-close-popup directives',
    description: 'Legacy popup-close directive usages.',
    pattern: /\bv-close-popup\b/g,
    content: 'raw',
  },
  {
    key: 'vRipple',
    label: 'v-ripple directives',
    description: 'Legacy ripple directive usages.',
    pattern: /\bv-ripple\b/g,
    content: 'raw',
  },
  {
    key: 'qComponentTags',
    label: 'Live <q-*> template tags',
    description: 'Quasar component tags inside Vue template blocks after comment stripping.',
    pattern: /<\/?q-[a-z0-9-]+/gi,
    content: 'vueTemplate',
    extensions: new Set(['.vue']),
  },
  {
    key: 'qCssSelectors',
    label: '.q-* CSS selectors',
    description: 'Quasar internal class selectors in CSS/style blocks.',
    pattern: /\.q-[A-Za-z0-9_-]+/g,
    content: 'styles',
  },
  {
    key: 'qCssVariables',
    label: '--q-* CSS variables',
    description: 'Legacy Quasar CSS custom property names.',
    pattern: /--q-[A-Za-z0-9_-]+/g,
    content: 'stylesAndCode',
  },
  {
    key: 'qCssVarRefs',
    label: 'var(--q-*) references',
    description: 'Static references to legacy Quasar CSS custom properties.',
    pattern: /var\(--q-[A-Za-z0-9_-]+/g,
    content: 'stylesAndCode',
  },
  {
    key: 'dynamicQCssVarFallbacks',
    label: 'dynamic var(--q-${...}) fallbacks',
    description: 'Template-string fallbacks that keep Quasar color vocabulary alive.',
    pattern: /var\(--q-\$\{/g,
    content: 'raw',
  },
  {
    key: 'dsCompatImports',
    label: '@ds/compat imports',
    description: 'Transitional compatibility imports.',
    pattern: /(?:from\s+['"]@ds\/compat(?:\/[^'"]*)?['"]|import\s+[^'"\n]*['"]@ds\/compat(?:\/[^'"]*)?['"]|@ds\/compat\/)/g,
    content: 'raw',
  },
  {
    key: 'stylusFiles',
    label: 'Standalone .styl files',
    description: 'Legacy Stylus source files. Must stay at zero.',
    kind: 'fileExtension',
    extension: '.styl',
  },
  {
    key: 'vueStylusBlocks',
    label: 'Vue <style lang="stylus"> blocks',
    description: 'Vue SFC style blocks still compiled through Stylus.',
    pattern: /<style\b[^>]*\blang=['"]stylus['"][^>]*>/gi,
    content: 'raw',
    extensions: new Set(['.vue']),
  },
  {
    key: 'stylusPackageDeps',
    label: 'Stylus package dependencies',
    description: 'package.json dependencies on stylus or @types/stylus.',
    pattern: /"(?:@types\/)?stylus"\s*:/g,
    content: 'raw',
    pathIncludes: 'package.json',
  },
  {
    key: 'deepQSelectors',
    label: ':deep(.q-*) selectors',
    description: 'Scoped style selectors reaching into Quasar internals.',
    pattern: /:deep\([^)]*\.q-[A-Za-z0-9_-]+/g,
    content: 'styles',
  },
  {
    key: 'deepDsSelectors',
    label: ':deep() DS/internal selectors',
    description: 'Scoped styles reaching into DS/domain/headless internals. Should move to stable DS parts or product wrappers.',
    pattern: /:deep\([^)]*(?:\.(?:ds|km)-|\[data-(?:state|side|align|highlighted|disabled)|\[data-reka)/g,
    content: 'styles',
  },
  {
    key: 'cypressQSelectors',
    label: 'Cypress .q-* selectors',
    description: 'Tests coupled to Quasar class names.',
    pattern: /\.q-[A-Za-z0-9_-]+/g,
    content: 'raw',
    pathIncludes: '/cypress/',
  },
  {
    key: 'transitionAll',
    label: 'transition: all declarations',
    description: 'Broad transitions that should move to DS motion presets or explicit properties.',
    pattern: /transition\s*:\s*all\b/g,
    content: 'styles',
  },
  {
    key: 'templateVisualProps',
    label: 'Template visual props',
    description: 'Color/background visual props in templates that should move toward semantic variant/display/tone APIs.',
    pattern: /\s:?(?:color|text-color|bg|bg-color|hover-color|hover-bg|active-color|active-bg|active-bg-color|indicator-color|icon-color|toggle-color|toggle-text-color|border-color)=/g,
    content: 'vueTemplate',
    extensions: new Set(['.vue']),
  },
  {
    key: 'sanctionedTemplateVisualFallbacks',
    label: 'Sanctioned template visual fallbacks',
    description: 'Explicit DS wrapper compatibility visual bindings. Must not grow; deprecate over time.',
    kind: 'templateVisualAllowlist',
    content: 'vueTemplate',
    extensions: new Set(['.vue']),
  },
  {
    key: 'legacyLayoutClasses',
    label: 'Legacy layout class attributes',
    description: 'Vue template class attributes containing row/column/col-* compatibility layout utilities.',
    pattern: /\s:?class\s*=\s*['"](?=(?:(?:col-(?:xs|sm|md|lg|xl)-(?:auto|[1-9]|1[0-2])|col-auto|col-(?:[1-9]|1[0-2])|column|row|col)(?=\s|['"])|[^'"]*\s(?:col-(?:xs|sm|md|lg|xl)-(?:auto|[1-9]|1[0-2])|col-auto|col-(?:[1-9]|1[0-2])|column|row|col)(?=\s|['"])))[^'"]*['"]/g,
    content: 'vueTemplate',
    extensions: new Set(['.vue']),
  },
  {
    key: 'kmZIndexTokens',
    label: '--km-z-* tokens',
    description: 'Legacy app z-index scale. Prefer the public --ds-z-* token scale.',
    pattern: /--km-z-[A-Za-z0-9_-]+/g,
    content: 'raw',
  },
  {
    key: 'unprefixedRadiusTokens',
    label: 'var(--radius-*) without --ds- prefix',
    description: 'Undefined token name (silently resolves to 0). Use var(--ds-radius-*) instead.',
    pattern: /var\(--radius-(?:xs|sm|md|lg|xl|2xl|full)\b/g,
    content: 'stylesAndCode',
  },
  {
    key: 'inlineStatusHexes',
    label: 'Inline status hex literals',
    description: 'Hardcoded hex colors for status (red/orange/yellow/green/blue) bypass DS status tokens. Use var(--ds-color-{success,warning,danger,info}-*) instead. Token definitions in @ds tokens/utilities are exempt.',
    pattern: /#(?:1976d2|c10015|f2c037|21ba45|ff0000|dd7e89|fcec87|bdf2d5|dcfce7|dbeafe)\b/gi,
    content: 'stylesAndCode',
    extensions: new Set(['.vue']),
  },
  {
    key: 'varFallbacks',
    label: 'var() with fallback in feature code',
    description: 'Second-arg var(--ds-..., <fallback>) hides typos like the historical var(--radius-*). New feature code should reference tokens without fallbacks; raise the canonical token instead.',
    pattern: /var\(\s*--ds-[A-Za-z0-9_-]+\s*,/g,
    content: 'stylesAndCode',
    pathIncludes: '/apps/',
  },
  {
    key: 'legacyNumericSpacing',
    label: 'Legacy numeric spacing utilities (p-16, gap-8, m-24, …)',
    description: 'Numeric pixel-based spacing classes from the codemod bridge. Phase 5 migrates them to the semantic scale (p-md, gap-sm, m-2xl, …). The 6px step has no semantic equivalent and is excluded.',
    pattern: /\b(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|gap-x|gap-y)-(?:2|4|8|12|16|20|24|32|40|48|64)\b/g,
    content: 'stylesAndCode',
    pathIncludes: '/apps/',
  },
  {
    key: 'legacyKmFontSize',
    label: 'var(--km-font-size-*) references',
    description: 'Legacy typography aliases. Phase 5 migrates them to var(--ds-font-size-*) and removes the alias block.',
    pattern: /var\(\s*--km-font-size-[A-Za-z0-9_-]+/g,
    content: 'stylesAndCode',
    pathIncludes: '/apps/',
  },
  {
    key: 'dsImports',
    label: '@ds imports',
    description: 'Positive adoption metric for the new design system.',
    pattern: /(?:from\s+['"]@ds(?:\/[^'"]*)?['"]|import\s+['"]@ds(?:\/[^'"]*)?['"]|import\s+[^'"\n]*['"]@ds(?:\/[^'"]*)?['"])/g,
    content: 'raw',
  },
]

function parseArgs(argv) {
  const args = {
    json: false,
    check: undefined,
    writeBaseline: undefined,
    writeReport: undefined,
  }

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--json') args.json = true
    else if (arg === '--check') args.check = argv[++index]
    else if (arg === '--write-baseline') args.writeBaseline = argv[++index]
    else if (arg === '--write-report') args.writeReport = argv[++index]
    else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown argument: ${arg}`)
    }
  }

  return args
}

function printHelp() {
  console.log(`Usage: node scripts/audit-ds-migration.mjs [options]

Options:
  --json                       Print JSON instead of Markdown.
  --write-report <path>        Write Markdown report to a path relative to web/ or absolute.
  --write-baseline <path>      Write baseline JSON to a path relative to web/ or absolute.
  --check <baseline-path>      Fail if any debt metric exceeds the baseline count.
`)
}

async function listFiles(entryPath) {
  if (!existsSync(entryPath)) return []

  const info = await stat(entryPath)
  if (info.isFile()) return shouldScanFile(entryPath) ? [entryPath] : []
  if (!info.isDirectory()) return []

  const entries = await readdir(entryPath, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    if (entry.isDirectory() && ignoredDirs.has(entry.name)) continue
    const childPath = path.join(entryPath, entry.name)
    if (shouldIgnorePath(childPath)) continue
    files.push(...await listFiles(childPath))
  }

  return files
}

function shouldIgnorePath(filePath) {
  const relativePath = `/${path.relative(webRoot, filePath).split(path.sep).join('/')}/`
  return ignoredPathFragments.some((fragment) => relativePath.includes(fragment))
}

function shouldScanFile(filePath) {
  return sourceExtensions.has(path.extname(filePath))
}

function stripHtmlComments(content) {
  return content.replace(/<!--[\s\S]*?-->/g, '')
}

function stripCssComments(content) {
  return content.replace(/\/\*[\s\S]*?\*\//g, '')
}

function vueTemplateContent(filePath, content) {
  if (path.extname(filePath) !== '.vue') return ''
  const blocks = [...content.matchAll(/<template\b[^>]*>([\s\S]*?)<\/template>/gi)]
  return blocks.map((match) => stripHtmlComments(match[1])).join('\n')
}

function styleContent(filePath, content) {
  const ext = path.extname(filePath)
  if (ext === '.vue') {
    const blocks = [...content.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)]
    return blocks.map((match) => stripCssComments(match[1])).join('\n')
  }
  if (['.css', '.scss', '.sass', '.styl'].includes(ext)) return stripCssComments(content)
  return ''
}

function metricContent(metric, filePath, content) {
  if (metric.content === 'vueTemplate') return vueTemplateContent(filePath, content)
  if (metric.content === 'styles') return styleContent(filePath, content)
  if (metric.content === 'stylesAndCode') return `${styleContent(filePath, content)}\n${content}`
  return content
}

function applyMetricAllowlist(metric, normalizedPath, content) {
  if (metric.key !== 'templateVisualProps') return content
  return applyTemplateVisualPropAllowlist(normalizedPath, content)
}

function countMatches(pattern, content) {
  pattern.lastIndex = 0
  return [...content.matchAll(pattern)].length
}

function resolveOutputPath(outputPath) {
  if (path.isAbsolute(outputPath)) return outputPath
  return path.resolve(webRoot, outputPath)
}

function formatRelative(filePath) {
  return path.relative(repoRoot, filePath).split(path.sep).join('/')
}

async function audit() {
  const files = (await Promise.all(
    scanEntries.map((entry) => listFiles(path.resolve(webRoot, entry))),
  )).flat().sort()

  const result = {
    generatedAt: new Date().toISOString(),
    webRoot: path.relative(repoRoot, webRoot) || '.',
    scannedFiles: files.length,
    metrics: {},
  }

  for (const metric of metrics) {
    result.metrics[metric.key] = {
      key: metric.key,
      label: metric.label,
      description: metric.description,
      count: 0,
      files: [],
    }
  }

  for (const filePath of files) {
    const relativePath = formatRelative(filePath)
    const normalizedPath = relativePath.replaceAll('\\', '/')
    const ext = path.extname(filePath)
    const content = await readFile(filePath, 'utf8')

    for (const metric of metrics) {
      if (metric.extensions && !metric.extensions.has(ext)) continue
      if (metric.pathIncludes && !normalizedPath.includes(metric.pathIncludes)) continue

      if (metric.kind === 'fileExtension') {
        if (ext !== metric.extension) continue

        const entry = result.metrics[metric.key]
        entry.count += 1
        entry.files.push({ path: normalizedPath, count: 1 })
        continue
      }

      if (metric.kind === 'templateVisualAllowlist') {
        const contentToScan = metricContent(metric, filePath, content)
        const count = countTemplateVisualPropAllowlist(normalizedPath, contentToScan)
        if (count === 0) continue

        const entry = result.metrics[metric.key]
        entry.count += count
        entry.files.push({ path: normalizedPath, count })
        continue
      }

      const contentToScan = applyMetricAllowlist(metric, normalizedPath, metricContent(metric, filePath, content))
      if (!contentToScan) continue

      const count = countMatches(metric.pattern, contentToScan)
      if (count === 0) continue


      const entry = result.metrics[metric.key]
      entry.count += count
      entry.files.push({ path: normalizedPath, count })
    }
  }

  for (const metric of Object.values(result.metrics)) {
    metric.files.sort((a, b) => b.count - a.count || a.path.localeCompare(b.path))
  }

  return result
}

function baselineFromResult(result) {
  return {
    generatedAt: result.generatedAt,
    scannedFiles: result.scannedFiles,
    counts: Object.fromEntries(
      Object.entries(result.metrics).map(([key, metric]) => [key, metric.count]),
    ),
  }
}

function renderMarkdown(result) {
  const lines = [
    '# Frontend DS Migration Audit',
    '',
    `Generated at: ${result.generatedAt}`,
    `Scanned files: ${result.scannedFiles}`,
    '',
    '## Summary',
    '',
    '| Metric | Count | Notes |',
    '|---|---:|---|',
  ]

  for (const metric of Object.values(result.metrics)) {
    lines.push(`| ${metric.label} | ${metric.count} | ${metric.description} |`)
  }

  lines.push('', '## Top Files', '')

  for (const metric of Object.values(result.metrics)) {
    lines.push(`### ${metric.label}`, '')
    if (metric.files.length === 0) {
      lines.push('No matches.', '')
      continue
    }

    lines.push('| File | Count |', '|---|---:|')
    for (const file of metric.files.slice(0, 20)) {
      lines.push(`| ${file.path} | ${file.count} |`)
    }
    if (metric.files.length > 20) lines.push(`| ... ${metric.files.length - 20} more files | |`)
    lines.push('')
  }

  return `${lines.join('\n')}\n`
}

async function checkBaseline(result, baselinePath) {
  const resolvedPath = resolveOutputPath(baselinePath)
  const baseline = JSON.parse(await readFile(resolvedPath, 'utf8'))
  const failures = []

  for (const [key, metric] of Object.entries(result.metrics)) {
    if (key === 'dsImports') continue
    const baselineCount = baseline.counts?.[key]
    if (typeof baselineCount !== 'number') continue
    if (metric.count > baselineCount) failures.push({ key, label: metric.label, count: metric.count, baseline: baselineCount })
  }

  if (failures.length === 0) return failures

  console.error('DS migration audit failed: legacy debt increased beyond baseline.\n')
  for (const failure of failures) {
    console.error(`- ${failure.label}: ${failure.count} > ${failure.baseline}`)
  }
  process.exitCode = 1
  return failures
}

async function writeJson(outputPath, value) {
  const resolvedPath = resolveOutputPath(outputPath)
  await mkdir(path.dirname(resolvedPath), { recursive: true })
  await writeFile(resolvedPath, `${JSON.stringify(value, null, 2)}\n`)
}

async function writeText(outputPath, value) {
  const resolvedPath = resolveOutputPath(outputPath)
  await mkdir(path.dirname(resolvedPath), { recursive: true })
  await writeFile(resolvedPath, value)
}

const args = parseArgs(process.argv.slice(2))
const result = await audit()
let baselineFailures = []

if (args.writeBaseline) await writeJson(args.writeBaseline, baselineFromResult(result))
if (args.writeReport) await writeText(args.writeReport, renderMarkdown(result))
if (args.check) baselineFailures = await checkBaseline(result, args.check)

if (args.json) console.log(JSON.stringify(result, null, 2))
else if (args.check && !args.writeBaseline && !args.writeReport && baselineFailures.length === 0) {
  console.log('DS migration audit passed: legacy debt did not increase beyond baseline.')
}
else if (args.check && baselineFailures.length > 0) {
  // Failure details were already printed by checkBaseline.
}
else console.log(renderMarkdown(result))