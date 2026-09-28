import { describe, expect, it } from 'vitest'

import { blockFromTransfer, detectContentKind, formatCharCount, htmlToText, noteBlock, siteMonogram, totalSourceChars } from './sourceBlocks'

const AZURE_PRICING = `
<meta charset="utf-8">
<!--StartFragment-->
<h2>Azure OpenAI Service pricing</h2>
<nav><a href="https://azure.microsoft.com/en-us/">Home</a></nav>
<table>
  <thead>
    <tr><th>Model</th><th colspan="2">Global</th></tr>
    <tr><th></th><th>Input</th><th>Output</th></tr>
  </thead>
  <tbody>
    <tr><td>GPT-4.1</td><td>$2 per 1M tokens</td><td>$8</td></tr>
    <tr><td>GPT-4.1 mini</td><td>$0.40</td><td>$1.60</td></tr>
  </tbody>
</table>
<p>See <a href="https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/">details</a>
and <a href="https://azure.microsoft.com/pricing/calculator/">calculator</a>.
<img src="https://cdn.example-assets.com/logo.png"><img src="https://static.azure.com/x.png"></p>
<script>alert(1)</script>
<!--EndFragment-->`

const OPENAI_DOCS = `
# GPT-4.1
Smartest non-reasoning model. Context window 1,047,576 tokens, max output tokens 32,768.
Supports function calling, structured outputs and streaming.
Docs: https://platform.openai.com/docs/models/gpt-4.1 and https://platform.openai.com/docs/pricing`

describe('htmlToText', () => {
  it('keeps tables as rows, headings as markdown and drops scripts and nav', () => {
    const text = htmlToText(AZURE_PRICING)
    expect(text).toContain('## Azure OpenAI Service pricing')
    expect(text).toContain('| Model | Global | Global |')
    expect(text).toContain('| GPT-4.1 | $2 per 1M tokens | $8 |')
    expect(text).not.toContain('alert')
    expect(text).not.toContain('Home')
  })

  it('writes list items and line breaks', () => {
    expect(htmlToText('<ul><li>Batch</li><li>Priority</li></ul>line<br>two')).toBe('- Batch\n\n- Priority\n\nline\ntwo')
  })
})

describe('blockFromTransfer', () => {
  it('reads the site from the links, not from asset hosts', () => {
    const block = blockFromTransfer({ html: AZURE_PRICING, text: 'ignored' })
    expect(block?.site).toBe('azure.microsoft.com')
    expect(block?.title).toBe('Azure OpenAI Service pricing')
    expect(block?.contentKind).toBe('pricing')
    expect(block?.stats.tables).toBe(1)
    expect(block?.stats.prices).toBeGreaterThanOrEqual(4)
  })

  it('falls back to plain text and its URLs', () => {
    const block = blockFromTransfer({ text: OPENAI_DOCS })
    expect(block?.kind).toBe('source')
    expect(block?.site).toBe('platform.openai.com')
    expect(block?.title).toBe('GPT-4.1')
    expect(block?.contentKind).toBe('docs')
  })

  it('has no site when nothing links anywhere', () => {
    const block = blockFromTransfer({ html: '<p>Input $3 / 1M tokens, output $15</p>' })
    expect(block?.site).toBeNull()
    expect(block?.title).toBeNull()
  })

  it('ignores relative links', () => {
    const block = blockFromTransfer({ html: '<a href="/pricing">Pricing</a> <a href="#x">x</a> text' })
    expect(block?.site).toBeNull()
  })

  it('returns null for an empty transfer', () => {
    expect(blockFromTransfer({ html: '<p> </p>', text: '  ' })).toBeNull()
    expect(blockFromTransfer({})).toBeNull()
  })
})

describe('detectContentKind', () => {
  it.each([
    ['Claude Opus 4: Input $15 / MTok, Output $75 / MTok', 'pricing'],
    ['Input: $1.25 per 1M tokens', 'pricing'],
    [OPENAI_DOCS, 'docs'],
    [`${OPENAI_DOCS}\nPricing: input $2.00, output $8.00 per 1M tokens`, 'mixed'],
    ['Release notes for the new console', 'unknown'],
  ])('%s → %s', (text, kind) => {
    expect(detectContentKind(text)).toBe(kind)
  })
})

describe('notes and totals', () => {
  it('builds trimmed notes and skips blank ones', () => {
    expect(noteBlock('  use EU prices ')).toMatchObject({ kind: 'note', text: 'use EU prices' })
    expect(noteBlock('   ')).toBeNull()
  })

  it('counts only source characters', () => {
    const blocks = [blockFromTransfer({ text: 'abcd' }), noteBlock('a long note that does not count')]
    expect(totalSourceChars(blocks.filter((block) => block !== null))).toBe(4)
  })

  it('takes the monogram from the brand part of the host', () => {
    expect(siteMonogram('learn.microsoft.com')).toBe('M')
    expect(siteMonogram('localhost')).toBe('L')
    expect(siteMonogram(null)).toBe('')
  })

  it('formats character counts', () => {
    expect(formatCharCount(950)).toBe('950')
    expect(formatCharCount(12_400)).toBe('12.4k')
    expect(formatCharCount(12_000)).toBe('12k')
    expect(formatCharCount(123_456)).toBe('123k')
  })
})
