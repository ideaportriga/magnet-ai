#!/usr/bin/env node

import { existsSync } from 'node:fs'
import { readFile, readdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const webRoot = path.resolve(scriptDir, '..')

const args = new Set(process.argv.slice(2))
const shouldWrite = args.has('--write')

const scanEntries = ['apps', 'packages']
const sourceExtensions = new Set(['.js', '.jsx', '.mjs', '.ts', '.tsx', '.vue'])
const ignoredDirs = new Set(['.git', '.nx', 'coverage', 'dist', 'node_modules'])
const ignoredPathFragments = ['/src/paraglide/']
const ignoredFiles = new Set([
  'packages/ds/src/components/domain/KmGlyph.vue',
  'packages/ds/src/components/domain/phosphorIcons.ts',
])

const iconNameMap = new Map(Object.entries({
  'fa fa-arrow-right-arrow-left': 'swap',
  'fa fa-check': 'check',
  'fa fa-comment-dots': 'chat',
  'fa fa-copy': 'copy',
  'fa fa-external-link': 'external-link',
  'fa fa-pen': 'edit',
  'fa fa-robot': 'robot',
  'fa fa-times': 'close',
  'fa fa-xmark': 'close',
  'far fa-circle-check': 'check',
  'far fa-copy': 'copy',
  'far fa-file-alt': 'file-text',
  'far fa-plus-square': 'add-square',
  'far fa-save': 'save',
  'far fa-trash-can': 'delete',
  'fas fa-angle-left': 'chevron-left',
  'fas fa-angle-right': 'chevron-right',
  'fas fa-arrow-left': 'arrow-left',
  'fas fa-arrow-right': 'arrow-right',
  'fas fa-arrow-right-arrow-left': 'swap',
  'fas fa-bars': 'menu',
  'fas fa-bolt': 'bolt',
  'fas fa-book': 'book',
  'fas fa-chart-column': 'chart',
  'fas fa-check': 'check',
  'fas fa-check-circle': 'check',
  'fas fa-chevron-down': 'chevron-down',
  'fas fa-chevron-left': 'chevron-left',
  'fas fa-chevron-right': 'chevron-right',
  'fas fa-chevron-up': 'chevron-up',
  'fas fa-circle-exclamation': 'error',
  'fas fa-circle-info': 'info',
  'fas fa-circle-nodes': 'graph',
  'fas fa-clipboard-check': 'clipboard-check',
  'fas fa-clipboard-list': 'clipboard-list',
  'fas fa-clock-rotate-left': 'history',
  'fas fa-cloud-arrow-down': 'cloud-download',
  'fas fa-cloud-arrow-up': 'cloud-upload',
  'fas fa-cloud-upload-alt': 'cloud-upload',
  'fas fa-code': 'code',
  'fas fa-compress': 'collapse',
  'fas fa-compress-alt': 'collapse',
  'fas fa-cog': 'settings',
  'fas fa-cogs': 'settings',
  'fas fa-comment-dots': 'chat',
  'fas fa-comments': 'chats',
  'fas fa-copy': 'copy',
  'fas fa-database': 'database',
  'fas fa-diagram-project': 'graph',
  'fas fa-download': 'download',
  'fas fa-ellipsis-v': 'more-vertical',
  'fas fa-eraser': 'eraser',
  'fas fa-external-link-alt': 'external-link',
  'fas fa-expand': 'expand',
  'fas fa-expand-alt': 'expand',
  'fas fa-eye': 'eye',
  'fas fa-eye-slash': 'eye-off',
  'fas fa-file': 'file',
  'fas fa-file-circle-check': 'file-check',
  'fas fa-file-circle-question': 'file-question',
  'fas fa-file-export': 'export',
  'fas fa-file-lines': 'file-text',
  'fas fa-file-pdf': 'file-pdf',
  'fas fa-flask': 'flask',
  'fas fa-folder': 'folder',
  'fas fa-gear': 'settings',
  'fas fa-globe': 'globe',
  'fas fa-hard-drive': 'storage',
  'fas fa-info-circle': 'info',
  'fas fa-layer-group': 'stack',
  'fas fa-link': 'link',
  'fas fa-list-ul': 'list',
  'fas fa-lock': 'lock',
  'fas fa-magnifying-glass-chart': 'search-chart',
  'fas fa-microchip': 'cpu',
  'fas fa-microphone': 'microphone',
  'fas fa-paper-plane': 'send',
  'fas fa-paperclip': 'attach',
  'fas fa-pen': 'edit',
  'fas fa-pencil': 'edit',
  'fas fa-play': 'play',
  'fas fa-plug': 'plug',
  'fas fa-plus': 'add',
  'fas fa-project-diagram': 'graph',
  'fas fa-puzzle-piece': 'puzzle',
  'fas fa-redo': 'redo',
  'fas fa-rotate-right': 'redo',
  'fas fa-save': 'save',
  'fas fa-search': 'search',
  'fas fa-server': 'server',
  'fas fa-shield-alt': 'shield-check',
  'fas fa-shoe-prints': 'steps',
  'fas fa-sign-out-alt': 'sign-out',
  'fas fa-sliders': 'settings',
  'fas fa-stamp': 'stamp',
  'fas fa-stop': 'stop',
  'fas fa-sync': 'sync',
  'fas fa-table-columns': 'columns',
  'fas fa-table-list': 'table-list',
  'fas fa-tag': 'tag',
  'fas fa-tags': 'tags',
  'fas fa-thumbtack': 'pin',
  'fas fa-thumbs-down': 'thumbs-down',
  'fas fa-thumbs-up': 'thumbs-up',
  'fas fa-times': 'close',
  'fas fa-times-circle': 'error',
  'fas fa-trash': 'delete',
  'fas fa-triangle-exclamation': 'warning',
  'fas fa-undo': 'undo',
  'fas fa-upload': 'upload',
  'fas fa-user': 'user',
  'fas fa-user-circle': 'user',
  'fas fa-video': 'video',
  'fas fa-wand-magic-sparkles': 'magic',
  'fas fa-wrench': 'wrench',
  'fas fa-xmark': 'close',

  arrow_drop_down: 'chevron-down',
  arrow_drop_up: 'chevron-up',
  article: 'file-text',
  attach_file: 'attach',
  auto_awesome: 'magic',
  calendar_month: 'calendar',
  calendar_today: 'calendar',
  check_circle: 'check',
  content_copy: 'copy',
  content_cut: 'cut',
  delete_outline: 'delete',
  description: 'file-text',
  drag_indicator: 'drag',
  error_outline: 'error',
  expand_less: 'chevron-up',
  expand_more: 'chevron-down',
  fact_check: 'clipboard-check',
  file_copy: 'copy',
  filter_list: 'filter',
  first_page: 'first-page',
  folder_open: 'folder-open',
  format_list_numbered: 'list-numbered',
  hourglass_top: 'hourglass',
  hub: 'graph',
  insert_drive_file: 'file',
  last_page: 'last-page',
  logout: 'sign-out',
  more_vert: 'more-vertical',
  o_add: 'add',
  o_add_circle: 'add-circle',
  o_category: 'category',
  o_delete: 'delete',
  o_edit: 'edit',
  o_hub: 'graph',
  o_info: 'info',
  o_view_column: 'columns',
  o_warning: 'warning',
  open_in_new: 'external-link',
  play_arrow: 'play',
  psychology: 'brain',
  radio_button_unchecked: 'circle',
  schedule: 'clock',
  smart_toy: 'robot',
  sync: 'refresh',
  text_fields: 'text',
  toggle_on: 'toggle-on',
  verified: 'check',
  visibility: 'eye',
  visibility_off: 'eye-off',
}))

const functionalSvgMap = new Map(Object.entries({
  ai: 'robot',
  arrow: 'arrow-right',
  attach: 'attach',
  attach_file: 'attach',
  book: 'book',
  calendar: 'calendar',
  cloud: 'cloud-upload',
  copy: 'copy',
  dislike: 'thumbs-down',
  edit: 'edit',
  email: 'email',
  exchange_h: 'swap',
  file: 'file',
  like: 'thumbs-up',
  pdf: 'file-pdf',
  reload: 'refresh',
  robot: 'robot',
  send: 'send',
  settings: 'settings',
  user: 'user',
  'video-file': 'video',
}))

const attrNamePattern = '(?:icon|icon-before|icon-after|notification-icon|name)'
const boundAttrNamePattern = `:${attrNamePattern}`
const objectKeyPattern = '(?:icon|notificationIcon|iconBefore|iconAfter)'

function printHelp() {
  console.log(`Usage: node scripts/migrate-phosphor-icons.mjs [--write]\n\nDefault mode is dry-run. Pass --write to update files.`)
}

if (args.has('--help') || args.has('-h')) {
  printHelp()
  process.exit(0)
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function replaceStringLiterals(expression) {
  let next = expression
  for (const [legacy, canonical] of iconNameMap) {
    const escaped = escapeRegExp(legacy)
    next = next
      .replace(new RegExp(`'${escaped}'`, 'g'), `'${canonical}'`)
      .replace(new RegExp(`"${escaped}"`, 'g'), `"${canonical}"`)
      .replace(new RegExp(`&quot;${escaped}&quot;`, 'g'), `&quot;${canonical}&quot;`)
  }
  return next
}

function replaceStaticAttributes(content) {
  const staticAttribute = new RegExp(`\\b(${attrNamePattern})=(['"])([^'"]+)\\2`, 'g')
  return content.replace(staticAttribute, (match, name, quote, value) => {
    const canonical = iconNameMap.get(value)
    return canonical ? `${name}=${quote}${canonical}${quote}` : match
  })
}

function replaceBoundAttributes(content) {
  const boundAttribute = new RegExp(`(${boundAttrNamePattern})=(['"])(.*?)\\2`, 'gs')
  return content.replace(boundAttribute, (match, name, quote, expression) => {
    const nextExpression = replaceStringLiterals(expression)
    return nextExpression === expression ? match : `${name}=${quote}${nextExpression}${quote}`
  })
}

function replaceObjectProperties(content) {
  const directProperty = new RegExp(`\\b(${objectKeyPattern})\\s*:\\s*(['"])([^'"]+)\\2`, 'g')
  return content.replace(directProperty, (match, key, quote, value) => {
    const canonical = iconNameMap.get(value)
    return canonical ? `${key}: ${quote}${canonical}${quote}` : match
  })
}

function replaceKnownFontAwesomeStrings(content) {
  let next = content
  for (const [legacy, canonical] of iconNameMap) {
    if (!/^(?:fa|far|fas|fab|fal|fass|fad) fa-/.test(legacy)) continue
    const escaped = escapeRegExp(legacy)
    next = next
      .replace(new RegExp(`'${escaped}'`, 'g'), `'${canonical}'`)
      .replace(new RegExp(`"${escaped}"`, 'g'), `"${canonical}"`)
      .replace(new RegExp(`&quot;${escaped}&quot;`, 'g'), `&quot;${canonical}&quot;`)
  }
  return next
}

function replaceSvgIconAttributes(content) {
  const staticSvgIcon = /\bsvg-icon=(['"])([^'"]+)\1/g
  return content.replace(staticSvgIcon, (match, quote, value) => {
    const canonical = functionalSvgMap.get(value)
    return canonical ? `icon=${quote}${canonical}${quote}` : match
  })
}

function replaceSvgIconProperties(content) {
  const staticSvgIconProperty = /\bsvgIcon\s*:\s*(['"])([^'"]+)\1/g
  return content.replace(staticSvgIconProperty, (match, quote, value) => {
    const canonical = functionalSvgMap.get(value)
    return canonical ? `icon: ${quote}${canonical}${quote}` : match
  })
}

function replaceFunctionalKmIconTags(content) {
  const simpleTag = /<(KmIcon|km-icon)(\s+[^>]*\bname=(['"])([^'"]+)\3[^>]*)\/>/g
  return content.replace(simpleTag, (match, tag, attrs, quote, value) => {
    const canonical = functionalSvgMap.get(value)
    if (!canonical) return match

    const width = attrs.match(/\bwidth=(['"])(\d+)\1/)
    const height = attrs.match(/\bheight=(['"])(\d+)\1/)
    const size = width?.[2] ?? height?.[2] ?? '16'
    const nextAttrs = attrs
      .replace(/\s\bname=(['"])([^'"]+)\1/, ` name=${quote}${canonical}${quote}`)
      .replace(/\s\bwidth=(['"])(\d+)\1/g, '')
      .replace(/\s\bheight=(['"])(\d+)\1/g, '')
    const glyphTag = tag === 'KmIcon' ? 'KmGlyph' : 'km-glyph'
    return `<${glyphTag}${nextAttrs} size=${quote}${size}px${quote} />`
  })
}

function migrateContent(content) {
  return [
    replaceStaticAttributes,
    replaceBoundAttributes,
    replaceObjectProperties,
    replaceKnownFontAwesomeStrings,
    replaceSvgIconAttributes,
    replaceSvgIconProperties,
    replaceFunctionalKmIconTags,
  ].reduce((next, transform) => transform(next), content)
}

async function listFiles(entryPath) {
  if (!existsSync(entryPath)) return []

  const entries = await readdir(entryPath, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const fullPath = path.join(entryPath, entry.name)
    const relativePath = path.relative(webRoot, fullPath).split(path.sep).join('/')

    if (entry.isDirectory()) {
      if (ignoredDirs.has(entry.name)) continue
      if (ignoredPathFragments.some((fragment) => `/${relativePath}/`.includes(fragment))) continue
      files.push(...await listFiles(fullPath))
    } else if (sourceExtensions.has(path.extname(entry.name)) && !ignoredFiles.has(relativePath)) {
      files.push(fullPath)
    }
  }

  return files
}

const files = (await Promise.all(scanEntries.map((entry) => listFiles(path.join(webRoot, entry))))).flat()
const changed = []

for (const filePath of files) {
  const before = await readFile(filePath, 'utf8')
  const after = migrateContent(before)
  if (after === before) continue

  const relativePath = path.relative(webRoot, filePath).split(path.sep).join('/')
  changed.push(relativePath)

  if (shouldWrite) await writeFile(filePath, after)
}

const mode = shouldWrite ? 'updated' : 'would update'
console.log(`${mode} ${changed.length} file(s)`)
for (const file of changed) console.log(`- ${file}`)
