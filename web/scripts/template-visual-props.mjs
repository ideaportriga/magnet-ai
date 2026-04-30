#!/usr/bin/env node

import { readFile, readdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  applyTemplateVisualPropAllowlist,
  countTemplateVisualPropAllowlist,
} from './template-visual-prop-allowlist.mjs'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const webRoot = path.resolve(scriptDir, '..')

const scanEntries = ['apps', 'packages']

const ignoredDirs = new Set([
  '.git',
  '.nx',
  '.yarn',
  'coverage',
  'dist',
  'documentation',
  'node_modules',
])

const visualPropNames = [
  'color',
  'text-color',
  'bg',
  'bg-color',
  'hover-color',
  'hover-bg',
  'active-color',
  'active-bg',
  'active-bg-color',
  'indicator-color',
  'icon-color',
  'toggle-color',
  'toggle-text-color',
  'border-color',
]

const visualPropPattern = new RegExp(`\\s(:?(?:${visualPropNames.join('|')}))=(["'])([\\s\\S]*?)\\2`, 'g')

const rules = {
  'phase3-safe-defaults': {
    description: [
      'Remove default/ignored visual props and convert the common brand chip recipe.',
      'Matches only component-aware static values that do not require a new DS API.',
    ].join(' '),
    apply: applyPhase3SafeDefaults,
  },
  'phase3-glyph-tones': {
    description: [
      'Convert static KmGlyph colour tokens to the semantic tone API.',
      'Leaves dynamic and unusual product-specific colours untouched.',
    ].join(' '),
    apply: applyPhase3GlyphTones,
  },
  'phase3-button-tones': {
    description: [
      'Convert high-confidence KmBtn colour, icon-colour, and hover recipes to semantic tone APIs.',
      'Leaves solid custom fills, dynamic bindings, and unusual product-specific colours untouched.',
    ].join(' '),
    apply: applyPhase3ButtonTones,
  },
  'phase3-icon-btn-tones': {
    description: [
      'Convert high-confidence KmIconBtn selected/default colour recipes to semantic tone APIs.',
      'Leaves product-specific icon button colours untouched.',
    ].join(' '),
    apply: applyPhase3IconButtonTones,
  },
  'phase3-chip-tones': {
    description: [
      'Convert high-confidence KmChip colour and text-colour recipes to semantic tone APIs.',
      'Leaves dynamic status expressions and product-specific score colours untouched.',
    ].join(' '),
    apply: applyPhase3ChipTones,
  },
  'phase3-kg-dialog-tones': {
    description: [
      'Convert high-confidence KnowledgeGraph dialog section icon colours to semantic tone APIs.',
      'Leaves dynamic icon colours and exact product colours untouched.',
    ].join(' '),
    apply: applyPhase3KgDialogTones,
  },
  'phase3-badge-tones': {
    description: [
      'Convert high-confidence KmBadge colour and text-colour recipes to semantic tone APIs.',
      'Leaves dynamic status expressions and product-specific colours untouched.',
    ].join(' '),
    apply: applyPhase3BadgeTones,
  },
  'phase3-avatar-tones': {
    description: [
      'Convert high-confidence KmAvatar colour and text-colour recipes to semantic tone APIs.',
      'Leaves dynamic and text-only recipes untouched.',
    ].join(' '),
    apply: applyPhase3AvatarTones,
  },
  'phase3-control-defaults': {
    description: [
      'Remove ignored or default visual props from control wrappers.',
      'Matches only props that wrappers do not consume or that equal the DS default.',
    ].join(' '),
    apply: applyPhase3ControlDefaults,
  },
}

const glyphToneByColor = new Map(Object.entries({
  primary: 'brand',
  'semi-transparent-primary': 'brand-soft',
  'text-secondary': 'subtle',
  'secondary-text': 'subtle',
  'grey-4': 'muted',
  grey: 'muted',
  'grey-5': 'muted',
  'grey-6': 'muted',
  'text-grey': 'muted',
  'grey-7': 'weak',
  positive: 'success',
  green: 'success',
  'success-text': 'success',
  'teal-7': 'accent',
  'blue-7': 'info',
  'purple-7': 'context',
  negative: 'danger',
  error: 'danger',
  red: 'danger',
  'amber-8': 'warning',
  'yellow-8': 'warning',
  'orange-8': 'warning',
  white: 'inverse',
  seemless: 'seamless',
}))

const glyphToneByBoundColor = new Map(Object.entries({
  'dragOver ? &quot;primary&quot; : &quot;grey-6&quot;': 'dragOver ? &quot;brand&quot; : &quot;muted&quot;',
  'item.type === &quot;file&quot; ? (item.uploaded ? &quot;positive&quot; : &quot;grey-7&quot;) : &quot;primary&quot;': 'item.type === &quot;file&quot; ? (item.uploaded ? &quot;success&quot; : &quot;weak&quot;) : &quot;brand&quot;',
  'modelValue === option.value ? \'primary\' : \'\'': 'modelValue === option.value ? \'brand\' : undefined',
  'parentRoute === \'/\' + item.path ? \'primary\' : \'icon\'': 'parentRoute === \'/\' + item.path ? \'brand\' : undefined',
  'secretExists(rec.key) ? &quot;positive&quot; : &quot;primary&quot;': 'secretExists(rec.key) ? &quot;success&quot; : &quot;brand&quot;',
  'testResult?.success ? &quot;positive&quot; : &quot;negative&quot;': 'testResult?.success ? &quot;success&quot; : &quot;danger&quot;',
  'webhookCall.success ? &quot;positive&quot; : &quot;negative&quot;': 'webhookCall.success ? &quot;success&quot; : &quot;danger&quot;',
}))

const defaultGlyphColors = new Set(['icon', 'secondary'])

const iconButtonToneByBoundColor = new Map(Object.entries({
  '`${liked ? &quot;primary&quot; : &quot;icon&quot;}`': 'liked ? &quot;brand&quot; : undefined',
  '`${disliked ? &quot;primary&quot; : &quot;icon&quot;}`': 'disliked ? &quot;brand&quot; : undefined',
  "liked ? 'primary' : 'icon'": "liked ? 'brand' : undefined",
  "disliked ? 'primary' : 'icon'": "disliked ? 'brand' : undefined",
}))

const buttonToneByColor = new Map(Object.entries({
  primary: 'brand',
  negative: 'danger',
  error: 'danger',
  'error-text': 'danger',
  'secondary-text': 'subtle',
  secondary: 'muted',
  'grey-7': 'weak',
  dark: 'neutral',
}))

const buttonIconToneByColor = new Map(Object.entries({
  primary: 'brand',
  negative: 'danger',
  error: 'danger',
  'error-text': 'danger',
  'secondary-text': 'subtle',
  secondary: 'muted',
  'grey-7': 'weak',
}))

const chipToneByColor = new Map(Object.entries({
  light: 'neutral',
  'in-progress': 'neutral',
  'primary-light': 'brand',
  'primary-transparent': 'brand',
  'chip-accent-bg': 'brand',
  'score-relevant': 'score',
  'grey-2': 'neutral',
  'grey-3': 'neutral',
  'green-2': 'success',
  'red-2': 'danger',
  'orange-2': 'warning',
}))

const chipToneByColorText = new Map(Object.entries({
  'light|grey-7': 'neutral',
  'light|grey-8': 'neutral',
  'in-progress|text-gray': 'neutral',
  'grey-2|grey-9': 'neutral',
  'grey-3|grey-8': 'neutral',
  'primary-light|primary': 'brand',
  'primary-transparent|primary': 'brand',
  'chip-accent-bg|primary': 'brand',
  'primary|white': 'brand',
  'score-relevant|score-relevant-text': 'score',
  'green-2|green-8': 'success',
  'green|white': 'success',
  'positive|white': 'success',
  'red-2|red-8': 'danger',
  'negative|white': 'danger',
  'orange-2|orange-8': 'warning',
}))

const chipNeutralTextOnly = new Set(['text-grey', 'text-gray'])

const chipToneByBoundColor = new Map(Object.entries({
  'runtimeStatus.runtime_loaded ? &quot;positive&quot; : &quot;grey-5&quot;': 'runtimeStatus.runtime_loaded ? &quot;success&quot; : &quot;neutral&quot;',
  'webhookCall.success ? &quot;positive&quot; : &quot;negative&quot;': 'webhookCall.success ? &quot;success&quot; : &quot;danger&quot;',
  'step.details.decided_action === &quot;search&quot; ? &quot;blue&quot; : &quot;green&quot;': 'step.details.decided_action === &quot;search&quot; ? &quot;info&quot; : &quot;success&quot;',
}))

const chipToneByBoundColorText = new Map(Object.entries({
  'isManuallyAddedParam(param) ? &quot;primary&quot; : &quot;grey-4&quot;|isManuallyAddedParam(param) ? &quot;white&quot; : &quot;grey-9&quot;': 'isManuallyAddedParam(param) ? &quot;brand&quot; : &quot;neutral&quot;',
  'row.exists ? &quot;orange-2&quot; : &quot;green-2&quot;|row.exists ? &quot;orange-8&quot; : &quot;green-8&quot;': 'row.exists ? &quot;warning&quot; : &quot;success&quot;',
  'userInfo?.is_two_factor_enabled ? &quot;positive&quot; : &quot;grey-4&quot;|userInfo?.is_two_factor_enabled ? &quot;white&quot; : &quot;dark&quot;': 'userInfo?.is_two_factor_enabled ? &quot;success&quot; : &quot;neutral&quot;',
  "availableModelsSource === 'api' ? 'positive' : 'primary-light'|availableModelsSource === 'api' ? 'white' : 'primary'": "availableModelsSource === 'api' ? 'success' : 'brand'",
  "model.model_type === 'embeddings' ? 'in-progress' : 'primary-light'|model.model_type === 'embeddings' ? 'grey-7' : 'primary'": "model.model_type === 'embeddings' ? 'neutral' : 'brand'",
}))

const badgeToneByColorText = new Map(Object.entries({
  'orange-1|orange-9': 'warning',
  'orange-2|orange-9': 'warning',
  'amber-8|white': 'warning',
  'blue-7|white': 'info',
  'grey-4|grey-8': 'neutral',
  'positive|white': 'success',
  'negative|white': 'danger',
  'error|white': 'danger',
}))

const badgeToneByBoundColor = new Map(Object.entries({
  "item.value === 'Yes' ? 'teal-5' : 'grey-5'": "item.value === 'Yes' ? 'success' : 'neutral'",
  "testResult.via_router ? &quot;positive&quot; : &quot;grey-6&quot;": "testResult.via_router ? &quot;success&quot; : &quot;neutral&quot;",
  "isExpiringSoon(row.expires_at) ? 'orange-7' : 'grey-6'": "isExpiringSoon(row.expires_at) ? 'warning' : 'neutral'",
}))

const avatarToneByColorText = new Map(Object.entries({
  'primary-bg|white': 'brand',
  'primary-light|primary': 'brand-soft',
}))

const kgDialogToneByIconColor = new Map(Object.entries({
  primary: 'brand',
  'blue-7': 'info',
  teal: 'accent',
  'teal-7': 'accent',
  'deep-purple-6': 'assistant',
  'purple-7': 'context',
  'green-7': 'success',
  'deep-orange-7': 'warning',
}))

function parseArgs(argv) {
  const args = {
    analyze: false,
    dryRun: false,
    json: false,
    rule: undefined,
  }

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--analyze') args.analyze = true
    else if (arg === '--dry-run') args.dryRun = true
    else if (arg === '--json') args.json = true
    else if (arg === '--rule') args.rule = argv[++index]
    else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown argument: ${arg}`)
    }
  }

  if (!args.analyze && !args.rule) args.analyze = true
  if (args.rule && !rules[args.rule]) throw new Error(`Unknown rule: ${args.rule}`)

  return args
}

function printHelp() {
  console.log(`Usage: node scripts/template-visual-props.mjs [options]

Options:
  --analyze                    Group current Vue template visual props.
  --rule <name>                Apply a component-aware rewrite rule.
  --dry-run                    Show rewrite results without writing files.
  --json                       Print JSON output.
  -h, --help                   Show this help.

Rules:
${Object.entries(rules).map(([name, rule]) => `  ${name.padEnd(24)} ${rule.description}`).join('\n')}`)
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const files = await collectVueFiles()

  if (args.analyze) {
    const analysis = await analyzeFiles(files)
    printAnalysis(analysis, args.json)
    return
  }

  const result = await rewriteFiles(files, args.rule, args.dryRun)
  printRewriteResult(result, args.json)
}

async function collectVueFiles() {
  const files = []

  for (const entry of scanEntries) {
    await walk(path.join(webRoot, entry), files)
  }

  return files.sort()
}

async function walk(dir, files) {
  const dirEntries = await readdir(dir, { withFileTypes: true })

  for (const entry of dirEntries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (!ignoredDirs.has(entry.name)) await walk(fullPath, files)
    } else if (entry.isFile() && entry.name.endsWith('.vue')) {
      files.push(fullPath)
    }
  }
}

async function analyzeFiles(files) {
  const byProp = new Map()
  const byComponentProp = new Map()
  const byComponentPropValue = new Map()
  const sanctionedFallbacksByFile = new Map()

  for (const file of files) {
    const content = await readFile(file, 'utf8')
    const relativeFile = path.relative(webRoot, file).split(path.sep).join('/')
    for (const tag of getTemplateTags(content)) {
      const allowedCount = countTemplateVisualPropAllowlist(relativeFile, tag.raw)
      if (allowedCount > 0) addCount(sanctionedFallbacksByFile, relativeFile, file, allowedCount)

      const raw = applyTemplateVisualPropAllowlist(relativeFile, tag.raw)
      visualPropPattern.lastIndex = 0
      let match
      while ((match = visualPropPattern.exec(raw))) {
        const prop = match[1]
        const value = match[3]
        addCount(byProp, prop, file)
        addCount(byComponentProp, `${tag.name} ${prop}`, file)
        addCount(byComponentPropValue, `${tag.name} ${prop}=${JSON.stringify(value)}`, file)
      }
    }
  }

  return {
    byProp: toSortedRows(byProp),
    byComponentProp: toSortedRows(byComponentProp),
    byComponentPropValue: toSortedRows(byComponentPropValue),
    sanctionedFallbacksByFile: toSortedRows(sanctionedFallbacksByFile),
  }
}

async function rewriteFiles(files, ruleName, dryRun) {
  const rule = rules[ruleName]
  const changedFiles = []
  let totalChanges = 0

  for (const file of files) {
    const original = await readFile(file, 'utf8')
    const rewritten = rewriteTemplateTags(original, rule.apply)
    if (rewritten.content === original) continue

    totalChanges += rewritten.changes.length
    changedFiles.push({
      file: path.relative(webRoot, file),
      changes: rewritten.changes.length,
      labels: summarizeLabels(rewritten.changes),
    })

    if (!dryRun) await writeFile(file, rewritten.content)
  }

  return {
    rule: ruleName,
    dryRun,
    changedFiles: changedFiles.length,
    totalChanges,
    files: changedFiles,
  }
}

function getTemplateTags(content) {
  const tags = []
  for (const block of getTemplateBlocks(content)) {
    for (const tag of scanStartTags(block.content)) {
      tags.push(tag)
    }
  }

  return tags
}

function getTemplateBlocks(content) {
  const blocks = []
  const pattern = /<\/?template\b[^>]*>/gi
  let match

  while ((match = pattern.exec(content))) {
    if (match[0].startsWith('</')) continue

    const start = match.index + match[0].length
    let end = -1
    let depth = 1

    while ((match = pattern.exec(content))) {
      if (match[0].startsWith('</')) depth -= 1
      else depth += 1

      if (depth === 0) {
        end = match.index
        break
      }
    }

    if (end === -1) break
    blocks.push({ start, end, content: content.slice(start, end) })
  }

  return blocks
}

function scanStartTags(content) {
  const tags = []
  let index = 0

  while (index < content.length) {
    const start = content.indexOf('<', index)
    if (start === -1) break

    if (content.startsWith('<!--', start)) {
      const endComment = content.indexOf('-->', start + 4)
      index = endComment === -1 ? content.length : endComment + 3
      continue
    }

    const next = content[start + 1]
    if (!next || next === '/' || next === '!' || next === '?') {
      index = start + 1
      continue
    }

    const end = findTagEnd(content, start)
    if (end === -1) break

    const raw = content.slice(start, end + 1)
    const name = /^<\s*([A-Za-z][\w.-]*)/.exec(raw)?.[1]
    if (name) tags.push({ start, end: end + 1, name, raw })
    index = end + 1
  }

  return tags
}

function findTagEnd(content, start) {
  let quote = ''

  for (let index = start + 1; index < content.length; index += 1) {
    const char = content[index]
    if (quote) {
      if (char === quote) quote = ''
    } else if (char === '"' || char === "'") {
      quote = char
    } else if (char === '>') {
      return index
    }
  }

  return -1
}

function rewriteTemplateTags(content, applyRule) {
  const blocks = getTemplateBlocks(content)
  let output = ''
  let cursor = 0
  const changes = []

  for (const block of blocks) {
    output += content.slice(cursor, block.start)
    const rewrittenBlock = rewriteTagsInBlock(block.content, applyRule)
    output += rewrittenBlock.content
    changes.push(...rewrittenBlock.changes)
    cursor = block.end
  }

  output += content.slice(cursor)

  return { content: output, changes }
}

function rewriteTagsInBlock(content, applyRule) {
  let output = ''
  let cursor = 0
  const changes = []

  for (const tag of scanStartTags(content)) {
    const result = applyRule(tag.raw, tag.name)
    output += content.slice(cursor, tag.start)
    output += result.tag
    changes.push(...result.changes)
    cursor = tag.end
  }

  output += content.slice(cursor)

  return { content: output, changes }
}

function applyPhase3SafeDefaults(tag, name) {
  let next = tag
  const changes = []

  if ((name === 'km-loader' || name === 'KmLoader') && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove default km-loader color')
  }

  if ((name === 'km-timeline' || name === 'KmTimeline') && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove default km-timeline color')
  }

  if (name === 'km-toggle' && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove default km-toggle color')
  }

  if (name === 'km-tabs') {
    for (const attrName of ['active-color', 'active-bg-color', 'indicator-color']) {
      if (getStaticAttr(next, attrName) != null) {
        next = removeAttr(next, attrName)
        changes.push(`remove ignored km-tabs ${attrName}`)
      }
    }
  }

  if (name === 'km-chip' && !hasAttr(next, 'tone') && getStaticAttr(next, 'color') === 'primary-light' && getStaticAttr(next, 'text-color') === 'primary') {
    next = replaceStaticAttr(next, 'color', 'primary-light', 'tone', 'brand')
    next = removeStaticAttr(next, 'color', 'primary-light')
    next = removeStaticAttr(next, 'text-color', 'primary')
    changes.push('convert brand km-chip recipe')
  }

  if ((name === 'km-btn' || name === 'KmBtn') && canRemoveDefaultPrimaryButtonColor(next)) {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove default primary km-btn color')
  }

  return { tag: changes.length ? cleanupTag(next) : next, changes }
}

function applyPhase3GlyphTones(tag, name) {
  if (name !== 'km-glyph' && name !== 'KmGlyph') return { tag, changes: [] }

  const boundColor = getStaticAttr(tag, ':color')
  if (boundColor && !hasAttr(tag, ':tone') && !hasAttr(tag, 'tone')) {
    const toneExpression = glyphToneByBoundColor.get(boundColor)
    if (toneExpression) {
      return {
        tag: cleanupTag(replaceStaticAttr(tag, ':color', boundColor, ':tone', toneExpression)),
        changes: ['convert dynamic glyph color to tone'],
      }
    }
  }

  const color = getStaticAttr(tag, 'color')
  if (!color || hasAttr(tag, 'tone')) return { tag, changes: [] }

  if (defaultGlyphColors.has(color)) {
    return {
      tag: cleanupTag(removeStaticAttr(tag, 'color', color)),
      changes: ['remove default glyph color'],
    }
  }

  const tone = glyphToneByColor.get(color)
  if (!tone) return { tag, changes: [] }

  return {
    tag: cleanupTag(replaceStaticAttr(tag, 'color', color, 'tone', tone)),
    changes: [`convert glyph ${color} to ${tone}`],
  }
}

function applyPhase3ButtonTones(tag, name) {
  if (name !== 'km-btn' && name !== 'KmBtn') return { tag, changes: [] }

  let next = tag
  const changes = []

  const interactionTone = getButtonInteractionTone(next)
  if (interactionTone && isNonSolidButton(next) && !hasAttr(next, 'interaction-tone')) {
    const hoverColor = getStaticAttr(next, 'hover-color')
    const hoverBg = getStaticAttr(next, 'hover-bg')
    next = replaceStaticAttr(next, 'hover-color', hoverColor, 'interaction-tone', interactionTone)
    next = removeStaticAttr(next, 'hover-bg', hoverBg)
    changes.push(`convert ${interactionTone} km-btn interaction tone`)
  }

  const iconColor = getStaticAttr(next, 'icon-color')
  if (iconColor && hasAttr(next, 'svg-icon') && !hasAttr(next, 'icon')) {
    next = removeStaticAttr(next, 'icon-color', iconColor)
    changes.push('remove ignored km-btn svg icon color')
  } else if (iconColor === 'icon') {
    next = removeStaticAttr(next, 'icon-color', 'icon')
    changes.push('remove default km-btn icon color')
  } else if (iconColor && !hasAttr(next, 'icon-tone') && !hasAttr(next, 'svg-icon')) {
    const iconTone = buttonIconToneByColor.get(iconColor)
    if (iconTone) {
      next = replaceStaticAttr(next, 'icon-color', iconColor, 'icon-tone', iconTone)
      changes.push(`convert km-btn icon ${iconColor} to ${iconTone}`)
    }
  }

  const color = getStaticAttr(next, 'color')
  if (color && canConvertStaticButtonColorTone(next, color)) {
    const tone = buttonToneByColor.get(color)
    next = replaceStaticAttr(next, 'color', color, 'tone', tone)
    changes.push(`convert km-btn ${color} to ${tone}`)
  }

  return { tag: changes.length ? cleanupTag(next) : next, changes }
}

function applyPhase3IconButtonTones(tag, name) {
  if (name !== 'km-icon-btn' && name !== 'KmIconBtn') return { tag, changes: [] }
  if (hasAttr(tag, 'tone') || hasAttr(tag, ':tone')) return { tag, changes: [] }

  const boundColor = getStaticAttr(tag, ':color')
  if (!boundColor) return { tag, changes: [] }

  const toneExpression = iconButtonToneByBoundColor.get(boundColor)
  if (!toneExpression) return { tag, changes: [] }

  return {
    tag: cleanupTag(replaceStaticAttr(tag, ':color', boundColor, ':tone', toneExpression)),
    changes: ['convert km-icon-btn selected color to tone'],
  }
}

function applyPhase3ChipTones(tag, name) {
  if (name !== 'km-chip' && name !== 'KmChip') return { tag, changes: [] }

  let next = tag
  const changes = []

  if (getStaticAttr(next, 'icon-color') === 'icon') {
    next = removeStaticAttr(next, 'icon-color', 'icon')
    changes.push('remove default km-chip icon color')
  }

  if (hasAttr(next, 'tone')) return { tag: changes.length ? cleanupTag(next) : next, changes }

  const boundColor = getStaticAttr(next, ':color')
  const boundTextColor = getStaticAttr(next, ':text-color')

  if (boundColor && boundTextColor) {
    const tone = chipToneByBoundColorText.get(`${boundColor}|${boundTextColor}`)
    if (tone) {
      next = replaceStaticAttr(next, ':color', boundColor, ':tone', tone)
      next = removeStaticAttr(next, ':text-color', boundTextColor)
      changes.push('convert dynamic km-chip status color/text-color to tone')
    }
  } else if (boundColor) {
    const tone = chipToneByBoundColor.get(boundColor)
    if (tone) {
      next = replaceStaticAttr(next, ':color', boundColor, ':tone', tone)
      const textColor = getStaticAttr(next, 'text-color')
      if (textColor === 'white') next = removeStaticAttr(next, 'text-color', textColor)
      changes.push('convert dynamic km-chip status color to tone')
    }
  }

  if (changes.length) return { tag: cleanupTag(next), changes }

  const color = getStaticAttr(next, 'color')
  const textColor = getStaticAttr(next, 'text-color')

  if (color && textColor) {
    const tone = chipToneByColorText.get(`${color}|${textColor}`)
    if (tone) {
      next = replaceStaticAttr(next, 'color', color, 'tone', tone)
      next = removeStaticAttr(next, 'text-color', textColor)
      if (tone === 'score') next = removeStaticClassToken(next, 'text-score-relevant-text')
      changes.push(`convert km-chip ${color}/${textColor} to ${tone}`)
    }
  } else if (color) {
    const tone = chipToneByColor.get(color)
    if (tone) {
      next = replaceStaticAttr(next, 'color', color, 'tone', tone)
      if (tone === 'score') next = removeStaticClassToken(next, 'text-score-relevant-text')
      changes.push(`convert km-chip ${color} to ${tone}`)
    }
  } else if (textColor && chipNeutralTextOnly.has(textColor)) {
    next = replaceStaticAttr(next, 'text-color', textColor, 'tone', 'neutral')
    changes.push(`convert km-chip ${textColor} to neutral`)
  }

  return { tag: changes.length ? cleanupTag(next) : next, changes }
}

function applyPhase3KgDialogTones(tag, name) {
  if (name !== 'kg-dialog-section' && name !== 'KgDialogSection') return { tag, changes: [] }
  if (hasAttr(tag, 'tone')) return { tag, changes: [] }

  const iconColor = getStaticAttr(tag, 'icon-color')
  if (!iconColor) return { tag, changes: [] }

  const tone = kgDialogToneByIconColor.get(iconColor)
  if (!tone) return { tag, changes: [] }

  return {
    tag: cleanupTag(replaceStaticAttr(tag, 'icon-color', iconColor, 'tone', tone)),
    changes: [`convert kg-dialog-section ${iconColor} to ${tone}`],
  }
}

function applyPhase3BadgeTones(tag, name) {
  if (name !== 'km-badge' && name !== 'KmBadge') return { tag, changes: [] }
  if (hasAttr(tag, 'tone')) return { tag, changes: [] }

  const boundColor = getStaticAttr(tag, ':color')
  const boundTone = boundColor ? badgeToneByBoundColor.get(boundColor) : undefined
  if (boundColor && boundTone) {
    let next = replaceStaticAttr(tag, ':color', boundColor, ':tone', boundTone)
    const textColor = getStaticAttr(next, 'text-color')
    if (textColor === 'white') next = removeStaticAttr(next, 'text-color', textColor)

    return {
      tag: cleanupTag(next),
      changes: ['convert dynamic km-badge status color to tone'],
    }
  }

  const color = getStaticAttr(tag, 'color')
  const textColor = getStaticAttr(tag, 'text-color')
  if (!color || !textColor) return { tag, changes: [] }

  const tone = badgeToneByColorText.get(`${color}|${textColor}`)
  if (!tone) return { tag, changes: [] }

  let next = replaceStaticAttr(tag, 'color', color, 'tone', tone)
  next = removeStaticAttr(next, 'text-color', textColor)

  return {
    tag: cleanupTag(next),
    changes: [`convert km-badge ${color}/${textColor} to ${tone}`],
  }
}

function applyPhase3AvatarTones(tag, name) {
  if (name !== 'km-avatar' && name !== 'KmAvatar') return { tag, changes: [] }
  if (hasAttr(tag, 'tone')) return { tag, changes: [] }

  const color = getStaticAttr(tag, 'color')
  const textColor = getStaticAttr(tag, 'text-color')
  if (!color || !textColor) return { tag, changes: [] }

  const tone = avatarToneByColorText.get(`${color}|${textColor}`)
  if (!tone) return { tag, changes: [] }

  let next = replaceStaticAttr(tag, 'color', color, 'tone', tone)
  next = removeStaticAttr(next, 'text-color', textColor)

  return {
    tag: cleanupTag(next),
    changes: [`convert km-avatar ${color}/${textColor} to ${tone}`],
  }
}

function applyPhase3ControlDefaults(tag, name) {
  let next = tag
  const changes = []

  if (name === 'km-btn-toggle' || name === 'KmBtnToggle') {
    for (const attrName of ['color', 'text-color', 'toggle-color', 'toggle-text-color']) {
      const value = getStaticAttr(next, attrName)
      if (value != null) {
        next = removeStaticAttr(next, attrName, value)
        changes.push(`remove ignored km-btn-toggle ${attrName}`)
      }
    }
  }

  if (name === 'km-btn' || name === 'KmBtn') {
    const textColor = getStaticAttr(next, 'text-color')
    if (textColor != null) {
      next = removeStaticAttr(next, 'text-color', textColor)
      changes.push('remove ignored km-btn text-color')
    }
  }

  if (name === 'km-icon' || name === 'KmIcon') {
    const color = getStaticAttr(next, 'color')
    if (color === 'secondary') {
      next = removeStaticAttr(next, 'color', color)
      changes.push('remove ignored km-icon color')
    }
  }

  if ((name === 'km-toggle' || name === 'KmToggle') && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove default km-toggle color')
  }

  if ((name === 'km-linear-progress' || name === 'KmLinearProgress') && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove default km-linear-progress color')
  }

  if ((name === 'km-inner-loading' || name === 'KmInnerLoading') && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove default km-inner-loading color')
  }

  if ((name === 'km-slider' || name === 'KmSlider') && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove ignored km-slider color')
  }

  if ((name === 'km-option-group' || name === 'KmOptionGroup') && getStaticAttr(next, 'color') === 'primary') {
    next = removeStaticAttr(next, 'color', 'primary')
    changes.push('remove ignored km-option-group color')
  }

  if (name === 'km-radio' || name === 'KmRadio') {
    const color = getStaticAttr(next, 'color')
    if (color === 'primary' || color === 'grey-6') {
      next = removeStaticAttr(next, 'color', color)
      changes.push('remove ignored km-radio color')
    }
  }

  if (name === 'km-select' || name === 'KmSelect') {
    if (getStaticAttr(next, 'color') === 'primary') {
      next = removeStaticAttr(next, 'color', 'primary')
      changes.push('remove ignored km-select color')
    }
    if (getStaticAttr(next, 'bg-color') === 'background') {
      next = removeStaticAttr(next, 'bg-color', 'background')
      changes.push('remove ignored km-select bg-color')
    }
  }

  if ((name === 'km-select-flat' || name === 'KmSelectFlat') && getStaticAttr(next, 'bg-color') === 'background') {
    next = removeStaticAttr(next, 'bg-color', 'background')
    changes.push('remove ignored km-select-flat bg-color')
  }

  if ((name === 'km-input' || name === 'KmInput') && getStaticAttr(next, 'bg-color') === 'background') {
    next = removeStaticAttr(next, 'bg-color', 'background')
    changes.push('remove ignored km-input bg-color')
  }

  if (name === 'km-chip' || name === 'KmChip') {
    for (const attrName of ['hover-color', 'hover-bg']) {
      const value = getStaticAttr(next, attrName)
      if (value != null) {
        next = removeStaticAttr(next, attrName, value)
        changes.push(`remove ignored km-chip ${attrName}`)
      }
    }
  }

  return { tag: changes.length ? cleanupTag(next) : next, changes }
}

function getButtonInteractionTone(tag) {
  const hoverColor = getStaticAttr(tag, 'hover-color')
  const hoverBg = getStaticAttr(tag, 'hover-bg')

  if (hoverColor === 'primary' && hoverBg === 'primary-bg') return 'brand'
  if ((hoverColor === 'negative' || hoverColor === 'error') && (hoverBg === 'negative-bg' || hoverBg === 'error-bg')) return 'danger'

  return undefined
}

function canConvertStaticButtonColorTone(tag, color) {
  if (!buttonToneByColor.has(color)) return false
  if (hasAttr(tag, 'tone')) return false
  if (hasAttr(tag, 'bg') || hasAttr(tag, 'text-color')) return false
  return isNonSolidButton(tag)
}

function isNonSolidButton(tag) {
  if (['flat', 'simple', 'link', 'outline', 'secondary'].some((attrName) => hasAttr(tag, attrName))) {
    return true
  }

  const variant = getStaticAttr(tag, 'variant')
  return Boolean(variant && variant !== 'primary' && variant !== 'danger')
}

function canRemoveDefaultPrimaryButtonColor(tag) {
  if (getStaticAttr(tag, 'color') !== 'primary') return false

  return ![
    'flat',
    'simple',
    'link',
    'outline',
    'secondary',
    'variant',
    'bg',
    'hover-bg',
    'hover-color',
    'icon-color',
  ].some((attrName) => hasAttr(tag, attrName))
}

function getStaticAttr(tag, name) {
  const match = attrPattern(name).exec(tag)
  return match?.[2]
}

function hasAttr(tag, name) {
  return new RegExp(`\\s${escapeRegExp(name)}(?=\\s|=|/?>)`).test(tag)
}

function removeStaticAttr(tag, name, value) {
  const pattern = new RegExp(`\\s${escapeRegExp(name)}=(['"])${escapeRegExp(value)}\\1`, 'g')
  return tag.replace(pattern, '')
}

function replaceStaticAttr(tag, oldName, oldValue, newName, newValue) {
  const pattern = new RegExp(`(\\s)${escapeRegExp(oldName)}=(['"])${escapeRegExp(oldValue)}\\2`, 'g')
  return tag.replace(pattern, (_match, whitespace, quote) => `${whitespace}${newName}=${quote}${newValue}${quote}`)
}

function removeAttr(tag, name) {
  const pattern = new RegExp(`\\s${escapeRegExp(name)}=(['"])[\\s\\S]*?\\1`, 'g')
  return tag.replace(pattern, '')
}

function removeStaticClassToken(tag, token) {
  const classValue = getStaticAttr(tag, 'class')
  if (!classValue) return tag

  const tokens = classValue.split(/\s+/).filter(Boolean)
  if (!tokens.includes(token)) return tag

  const nextValue = tokens.filter((className) => className !== token).join(' ')
  if (!nextValue) return removeStaticAttr(tag, 'class', classValue)
  return replaceStaticAttr(tag, 'class', classValue, 'class', nextValue)
}

function cleanupTag(tag) {
  let next = tag.replace(/[ \t]+$/gm, '')
  while (/\n[ \t]*\n/.test(next)) next = next.replace(/\n[ \t]*\n/g, '\n')
  return next
}

function attrPattern(name) {
  return new RegExp(`\\s${escapeRegExp(name)}=(['"])([\\s\\S]*?)\\1`)
}

function addCount(map, key, file, count = 1) {
  const entry = map.get(key) ?? { count: 0, files: new Set() }
  entry.count += count
  entry.files.add(file)
  map.set(key, entry)
}

function toSortedRows(map) {
  return [...map.entries()]
    .map(([key, value]) => ({ key, count: value.count, files: value.files.size }))
    .sort((left, right) => right.count - left.count || left.key.localeCompare(right.key))
}

function summarizeLabels(changes) {
  const labels = new Map()
  for (const change of changes) labels.set(change, (labels.get(change) ?? 0) + 1)
  return Object.fromEntries([...labels.entries()].sort(([left], [right]) => left.localeCompare(right)))
}

function printAnalysis(analysis, json) {
  if (json) {
    console.log(JSON.stringify(analysis, null, 2))
    return
  }

  for (const [title, rows] of Object.entries(analysis)) {
    console.log(`\n## ${title}`)
    for (const row of rows.slice(0, 40)) {
      console.log(`${String(row.count).padStart(4)}  ${String(row.files).padStart(4)} files  ${row.key}`)
    }
  }
}

function printRewriteResult(result, json) {
  if (json) {
    console.log(JSON.stringify(result, null, 2))
    return
  }

  console.log(`${result.dryRun ? 'Dry run' : 'Applied'} ${result.rule}: ${result.totalChanges} changes in ${result.changedFiles} files`)
  for (const file of result.files) {
    console.log(`- ${file.file}: ${file.changes}`)
  }
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

try {
  await main()
} catch (error) {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
}
