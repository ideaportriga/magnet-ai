/**
 * Source blocks for "fill from text" (#466): what a paste, a drop or a typed
 * line turns into before it goes to `POST models/extract-from-text`.
 *
 * Framework-free on purpose (only `DOMParser`):
 *
 *   - a pasted page becomes a `source` block. The copied HTML is converted to
 *     text that keeps table rows (`| Input | $2.00 |`) — pricing tables are
 *     the whole point, and plain-text copies flatten them into loose lines;
 *   - the block also carries what the UI shows instead of the text: the site
 *     (the most linked host in the fragment — browsers never expose the page
 *     URL of a copy), a heading, and whether it reads as pricing or docs;
 *   - a typed line becomes a `note`: an instruction for the extraction
 *     ("use EU Data Zone prices"), never a source of values.
 */

export type SourceContentKind = 'pricing' | 'docs' | 'mixed' | 'unknown'

export interface SourceStats {
  chars: number
  tables: number
  prices: number
}

export interface SourceBlock {
  id: string
  kind: 'source' | 'note'
  text: string
  site: string | null
  title: string | null
  contentKind: SourceContentKind
  stats: SourceStats
}

/** What a paste or a drop carries; either part may be missing. */
export interface TransferPayload {
  html?: string | null
  text?: string | null
}

/** Mirrors the backend's `MAX_TEXT_LENGTH` — the total over all sources. */
export const SOURCE_CHAR_LIMIT = 100_000
export const SOURCE_CHAR_WARNING = 80_000
/** Mirrors the backend's `MAX_SOURCES` / `MAX_NOTES`. */
export const MAX_SOURCES = 10
export const MAX_NOTES = 10
export const MAX_NOTE_LENGTH = 1_000

const TITLE_LENGTH = 120

let sequence = 0
function nextId(kind: SourceBlock['kind']): string {
  sequence += 1
  return `${kind}-${Date.now().toString(36)}-${sequence}`
}

// ── HTML → text ─────────────────────────────────────────────────────────

const DROPPED_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'SVG', 'IFRAME', 'OBJECT', 'BUTTON', 'NAV', 'SELECT'])

const BLOCK_TAGS = new Set([
  'ADDRESS',
  'ARTICLE',
  'ASIDE',
  'BLOCKQUOTE',
  'CAPTION',
  'DD',
  'DETAILS',
  'DIV',
  'DL',
  'DT',
  'FIELDSET',
  'FIGCAPTION',
  'FIGURE',
  'FOOTER',
  'FORM',
  'HEADER',
  'HR',
  'MAIN',
  'OL',
  'P',
  'PRE',
  'SECTION',
  'SUMMARY',
  'UL',
])

const TEXT_NODE = 3
const ELEMENT_NODE = 1

function parseHtml(html: string): Document {
  // A DOMParser document is inert: no scripts run and nothing is fetched.
  return new DOMParser().parseFromString(html, 'text/html')
}

function renderChildren(node: Node, out: string[]): void {
  node.childNodes.forEach((child) => renderNode(child, out))
}

function inlineText(node: Node): string {
  const out: string[] = []
  renderChildren(node, out)
  return out.join('').replace(/\s+/g, ' ').trim()
}

function tableRows(table: Element): Element[] {
  return Array.from(table.querySelectorAll(':scope > tr, :scope > thead > tr, :scope > tbody > tr, :scope > tfoot > tr'))
}

function tableToText(table: Element): string {
  const lines: string[] = []
  const caption = table.querySelector(':scope > caption')
  if (caption) lines.push(inlineText(caption))
  tableRows(table).forEach((row, index) => {
    const cells: string[] = []
    for (const cell of Array.from(row.children)) {
      if (cell.tagName !== 'TD' && cell.tagName !== 'TH') continue
      const text = inlineText(cell).replace(/\|/g, '/')
      // Repeat spanned header cells so the price columns still line up.
      const span = Math.min(Math.max(Number(cell.getAttribute('colspan')) || 1, 1), 10)
      for (let i = 0; i < span; i++) cells.push(text)
    }
    if (!cells.some(Boolean)) return
    lines.push(`| ${cells.join(' | ')} |`)
    if (index === 0 && row.querySelector('th')) lines.push(`|${' --- |'.repeat(cells.length)}`)
  })
  return lines.join('\n')
}

function renderNode(node: Node, out: string[]): void {
  if (node.nodeType === TEXT_NODE) {
    out.push((node.textContent ?? '').replace(/\s+/g, ' '))
    return
  }
  if (node.nodeType !== ELEMENT_NODE) return
  const element = node as Element
  const tag = element.tagName.toUpperCase()
  if (DROPPED_TAGS.has(tag) || element.getAttribute('aria-hidden') === 'true' || element.hasAttribute('hidden')) return
  if (tag === 'BR') {
    out.push('\n')
    return
  }
  if (tag === 'TABLE') {
    out.push(`\n${tableToText(element)}\n`)
    return
  }
  const heading = /^H([1-6])$/.exec(tag)
  if (heading) {
    const text = inlineText(element)
    if (text) out.push(`\n${'#'.repeat(Number(heading[1]))} ${text}\n`)
    return
  }
  if (tag === 'LI') {
    out.push('\n- ')
    renderChildren(element, out)
    out.push('\n')
    return
  }
  if (tag === 'TD' || tag === 'TH') {
    // A cell outside a table (a partial copy of one row).
    out.push(' | ')
    renderChildren(element, out)
    return
  }
  const block = BLOCK_TAGS.has(tag)
  if (block) out.push('\n')
  renderChildren(element, out)
  if (block) out.push('\n')
}

function tidy(text: string): string {
  return text
    .split('\n')
    .map((line) => line.replace(/[ \t\u00a0]+/g, ' ').trim())
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function documentText(doc: Document): string {
  const out: string[] = []
  renderChildren(doc.body ?? doc, out)
  return tidy(out.join(''))
}

/** Readable text of copied HTML, with tables as `| a | b |` rows. */
export function htmlToText(html: string): string {
  return documentText(parseHtml(html))
}

// ── Metadata ────────────────────────────────────────────────────────────

/** Asset hosts that say nothing about which page the copy came from. */
const ASSET_HOST_RE =
  /(?:^|\.)(?:cdn|static|assets?|img|images|media|fonts?)[\d-]*\.|(?:cloudfront\.net|akamaized\.net|akamaihd\.net|gstatic\.com|googleapis\.com|jsdelivr\.net|cloudflare\.com|cdnjs\.com|gravatar\.com|twimg\.com|fbcdn\.net)$/

function hostOf(value: string | null | undefined): string | null {
  if (!value) return null
  try {
    const url = new URL(value.trim())
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
    const host = url.hostname.toLowerCase().replace(/^www\./, '')
    return host && !ASSET_HOST_RE.test(host) ? host : null
  } catch {
    return null
  }
}

/** The most frequent host; ties go to the one seen first. */
function dominantHost(hosts: (string | null)[]): string | null {
  const counts = new Map<string, number>()
  for (const host of hosts) {
    if (host) counts.set(host, (counts.get(host) ?? 0) + 1)
  }
  let best: string | null = null
  let bestCount = 0
  for (const [host, count] of counts) {
    if (count > bestCount) {
      best = host
      bestCount = count
    }
  }
  return best
}

/** Where the copy most likely came from, judged by the links inside it. */
export function inferSite(doc: Document): string | null {
  const values = Array.from(doc.querySelectorAll('a[href], link[href], img[src], source[src]')).map(
    (element) => element.getAttribute('href') ?? element.getAttribute('src')
  )
  return dominantHost(values.map(hostOf))
}

function inferSiteFromText(text: string): string | null {
  return dominantHost(Array.from(text.matchAll(/https?:\/\/[^\s)<>"']+/g), (match) => hostOf(match[0])))
}

function clip(text: string, length: number): string {
  const single = text.replace(/\s+/g, ' ').trim()
  return single.length > length ? `${single.slice(0, length - 1).trimEnd()}…` : single
}

/** The first heading of the fragment, for the block's title line. */
export function inferTitle(doc: Document): string | null {
  const heading = doc.querySelector('h1, h2, h3, caption, [role="heading"], h4')
  const text = heading ? inlineText(heading) : ''
  return text ? clip(text, TITLE_LENGTH) : null
}

function inferTitleFromText(text: string): string | null {
  const heading = /^#{1,3}\s+(.+)$/m.exec(text)
  return heading ? clip(heading[1], TITLE_LENGTH) : null
}

const PRICE_RE = /(?:[$€£]\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|EUR)\b)/g
const PER_UNIT_RE =
  /(?:\bper\s+|\/\s*)(?:1\s?[km]\b|1,000(?:,000)?\b|(?:one\s+)?(?:million|thousand)\b|\d+\s+)?\s*(?:input\s+|output\s+)?(?:tokens?|characters?|chars|requests?|queries|images?|minutes?|hours?)\b|\/\s*MTok\b/gi
const DOCS_TERMS = [
  /context (?:window|length)/i,
  /max(?:imum)? output tokens/i,
  /knowledge cut-?off/i,
  /function calling/i,
  /tool (?:use|calling)/i,
  /structured outputs?/i,
  /json mode/i,
  /modalit(?:y|ies)/i,
  /reasoning (?:effort|tokens?)/i,
  /\bstreaming\b/i,
  /fine-?tuning/i,
  /rate limits?/i,
  /\bsnapshots?\b/i,
  /\bcapabilities\b/i,
  /\btemperature\b/i,
  /\btop[_ ]p\b/i,
  /\bdimensions\b/i,
  /\bendpoints?\b/i,
]

function countMatches(text: string, pattern: RegExp): number {
  return Array.from(text.matchAll(pattern)).length
}

/** Pricing, docs, both, or neither — a cheap local read of the text. */
export function detectContentKind(text: string): SourceContentKind {
  const prices = countMatches(text, PRICE_RE)
  const perUnit = countMatches(text, PER_UNIT_RE)
  const pricing = prices >= 2 || (prices >= 1 && perUnit >= 1)
  const docs = DOCS_TERMS.filter((term) => term.test(text)).length >= 2
  if (pricing && docs) return 'mixed'
  if (pricing) return 'pricing'
  if (docs) return 'docs'
  return 'unknown'
}

function sourceBlock(text: string, site: string | null, title: string | null, tables: number): SourceBlock {
  return {
    id: nextId('source'),
    kind: 'source',
    text,
    site,
    title,
    contentKind: detectContentKind(text),
    stats: { chars: text.length, tables, prices: countMatches(text, PRICE_RE) },
  }
}

/** A pasted or dropped page as a block; `null` when there is nothing in it. */
export function blockFromTransfer(payload: TransferPayload): SourceBlock | null {
  const html = payload.html?.trim()
  if (html) {
    const doc = parseHtml(html)
    const text = documentText(doc)
    if (text) {
      return sourceBlock(text, inferSite(doc) ?? inferSiteFromText(text), inferTitle(doc), doc.querySelectorAll('table').length)
    }
  }
  const text = tidy(payload.text ?? '')
  if (!text) return null
  const tables = text.split('\n').some((line) => /^\|.*\|$/.test(line)) ? 1 : 0
  return sourceBlock(text, inferSiteFromText(text), inferTitleFromText(text), tables)
}

/** A typed instruction; `null` when blank. */
export function noteBlock(text: string): SourceBlock | null {
  const note = text.trim().slice(0, MAX_NOTE_LENGTH)
  if (!note) return null
  return {
    id: nextId('note'),
    kind: 'note',
    text: note,
    site: null,
    title: null,
    contentKind: 'unknown',
    stats: { chars: note.length, tables: 0, prices: 0 },
  }
}

export function sourceBlocksOf(blocks: SourceBlock[]): SourceBlock[] {
  return blocks.filter((block) => block.kind === 'source')
}

export function noteBlocksOf(blocks: SourceBlock[]): SourceBlock[] {
  return blocks.filter((block) => block.kind === 'note')
}

/** Characters the sources send; notes are small and capped on their own. */
export function totalSourceChars(blocks: SourceBlock[]): number {
  return sourceBlocksOf(blocks).reduce((sum, block) => sum + block.text.length, 0)
}

/** `learn.microsoft.com` → `M`: the brand part of the host, not the subdomain. */
export function siteMonogram(site: string | null | undefined): string {
  const parts = (site ?? '').split('.').filter(Boolean)
  const brand = parts.length >= 2 ? parts[parts.length - 2] : parts[0]
  return brand ? brand.charAt(0).toUpperCase() : ''
}

/** `12.4k` */
export function formatCharCount(count: number): string {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands >= 100 ? Math.round(thousands) : Number(thousands.toFixed(1))}k`
}
