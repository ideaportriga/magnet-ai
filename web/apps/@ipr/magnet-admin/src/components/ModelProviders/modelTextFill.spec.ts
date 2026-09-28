import { describe, expect, it } from 'vitest'

import {
  buildModelPatch,
  capabilityItems,
  defaultSelection,
  groupPricingOptions,
  hasGroup,
  isNameMatch,
  longContextLines,
  missingGroups,
  pricingOptionLines,
  pricingPatch,
  pricingTable,
  reviewGroups,
  type ExtractedModel,
  type ExtractedPricingOption,
} from './modelTextFill'

function option(overrides: Partial<ExtractedPricingOption> = {}): ExtractedPricingOption {
  return {
    label: 'Standard',
    price_scheme: null,
    price_input: null,
    price_output: null,
    price_cached: null,
    price_cache_write: null,
    price_cache_write_1h: null,
    price_standard_input_unit_count: null,
    price_cached_input_unit_count: null,
    price_standard_output_unit_count: null,
    price_input_unit_name: null,
    price_output_unit_name: null,
    price_long_context_threshold: null,
    price_long_context_input: null,
    price_long_context_cached: null,
    price_long_context_cache_write: null,
    price_long_context_cache_write_1h: null,
    price_long_context_output: null,
    ...overrides,
  }
}

function result(overrides: Partial<ExtractedModel> = {}): ExtractedModel {
  return {
    target_key: 'a',
    matched_name: 'GPT-4.1',
    description: null,
    json_mode: null,
    json_schema: null,
    tool_calling: null,
    reasoning: null,
    reasoning_effort_options: null,
    supports_temperature: null,
    supports_top_p: null,
    supports_max_tokens: null,
    diarization: null,
    keyterms: null,
    vector_size: null,
    pricing_options: [],
    ...overrides,
  }
}

const AZURE = result({
  description: 'Flagship GPT model.',
  tool_calling: true,
  supports_temperature: false,
  diarization: true,
  vector_size: 3072,
  pricing_options: [
    option({ label: 'Global', price_input: '2', price_output: '8', price_cached: '0.5' }),
    option({ label: 'Batch', price_input: '1', price_output: '4' }),
  ],
})

describe('defaultSelection', () => {
  it('picks every group the text filled and the first pricing option', () => {
    expect(defaultSelection(AZURE, 'prompts')).toEqual({
      apply: true,
      groups: { description: true, configuration: true, pricing: true },
      pricingOptionIndex: 0,
    })
  })

  it('skips a model the text does not describe', () => {
    const missing = result({ matched_name: null })
    expect(defaultSelection(missing, 'prompts').apply).toBe(false)
    expect(hasGroup(missing, 'description', 'prompts')).toBe(false)
  })
})

describe('buildModelPatch', () => {
  it('applies the chosen pricing option and only stated flags', () => {
    const selection = { ...defaultSelection(AZURE, 'prompts'), pricingOptionIndex: 1 }
    const patch = buildModelPatch(AZURE, selection, { type: 'prompts' })

    expect(patch).toMatchObject({
      description: 'Flagship GPT model.',
      tool_calling: true,
      supports_temperature: false,
      price_input: '1',
      price_output: '4',
      price_cached: null,
      price_scheme: 'basic',
      price_standard_input_unit_count: 1000000,
      price_cached_input_unit_count: 1000000,
      price_input_unit_name: 'tokens',
    })
    // Null in the extraction means "not stated" — never switched off.
    expect(patch).not.toHaveProperty('json_mode')
    // STT / embeddings fields don't belong on a chat model.
    expect(patch).not.toHaveProperty('diarization')
    expect(patch).not.toHaveProperty('configs')
  })

  it('gates configuration on the model type', () => {
    const selection = defaultSelection(AZURE, 'embeddings')
    const patch = buildModelPatch(AZURE, selection, { type: 'embeddings', configs: { dims_hint: 1 } })
    expect(patch.configs).toEqual({ dims_hint: 1, vector_size: 3072 })
    expect(patch).not.toHaveProperty('tool_calling')

    const stt = buildModelPatch(AZURE, defaultSelection(AZURE, 'stt'), { type: 'stt' })
    expect(stt).toMatchObject({ diarization: true })
    expect(stt).not.toHaveProperty('tool_calling')

    expect(hasGroup(AZURE, 'configuration', 'classifier')).toBe(false)
  })

  it('respects unchecked groups and skipped models', () => {
    const selection = defaultSelection(AZURE, 'prompts')
    selection.groups.pricing = false
    selection.groups.description = false
    expect(Object.keys(buildModelPatch(AZURE, selection, { type: 'prompts' })).sort()).toEqual(['supports_temperature', 'tool_calling'])

    selection.apply = false
    expect(buildModelPatch(AZURE, selection, { type: 'prompts' })).toEqual({})
  })
})

describe('pricingPatch', () => {
  it('infers the cache scheme from the listed cache-write prices', () => {
    expect(pricingPatch(option({ price_input: '3', price_cache_write: '3.75' })).price_scheme).toBe('openai')
    expect(pricingPatch(option({ price_input: '3', price_cache_write: '3.75', price_cache_write_1h: '6' })).price_scheme).toBe('anthropic')
  })

  it('drops cache-write prices the scheme does not bill', () => {
    const patch = pricingPatch(option({ price_scheme: 'basic', price_input: '1', price_cache_write: '2', price_cache_write_1h: '3' }))
    expect(patch.price_cache_write).toBeNull()
    expect(patch.price_cache_write_1h).toBeNull()
  })

  it('clears long-context prices the option does not have', () => {
    const patch = pricingPatch(option({ price_input: '1' }))
    expect(patch.price_long_context_threshold).toBeNull()
    expect(patch.price_long_context_input).toBeNull()
  })

  it('keeps non-token units', () => {
    const patch = pricingPatch(option({ price_input: '15', price_standard_input_unit_count: 1000, price_input_unit_name: 'queries' }))
    expect(patch.price_standard_input_unit_count).toBe(1000)
    expect(patch.price_cached_input_unit_count).toBe(1000)
    expect(patch.price_input_unit_name).toBe('queries')
    expect(patch.price_output_unit_name).toBe('tokens')
  })
})

describe('price lines', () => {
  it('lists the standard prices, input first and output last', () => {
    expect(pricingOptionLines(AZURE.pricing_options[0])).toEqual([
      { kind: 'input', amount: '$2', unit: '1M tokens' },
      { kind: 'cached', amount: '$0.5', unit: '1M tokens' },
      { kind: 'output', amount: '$8', unit: '1M tokens' },
    ])
  })

  it('keeps long context on the same option', () => {
    const tiered = option({
      price_input: '3',
      price_output: '15',
      price_long_context_threshold: 200000,
      price_long_context_input: '6',
      price_long_context_output: '22.5',
    })
    expect(longContextLines(tiered).map((line) => [line.kind, line.amount])).toEqual([
      ['input', '$6'],
      ['output', '$22.5'],
    ])
    expect(pricingPatch(tiered)).toMatchObject({
      price_long_context_threshold: 200000,
      price_long_context_input: '6',
      price_long_context_output: '22.5',
    })
    expect(longContextLines(option({ price_input: '1' }))).toEqual([])
  })
})

describe('missingGroups', () => {
  it('names what the text did not cover', () => {
    const pricesOnly = result({ pricing_options: [option({ price_input: '1' })] })
    expect(missingGroups(pricesOnly, 'prompts')).toEqual(['description', 'configuration'])
    // A classifier has no capabilities to miss.
    expect(missingGroups(pricesOnly, 'classifier')).toEqual(['description'])
    expect(missingGroups(result({ matched_name: null }), 'prompts')).toEqual([])
  })
})

describe('groupPricingOptions', () => {
  it('groups by source in source order with unattributed options last', () => {
    const groups = groupPricingOptions([
      option({ label: 'Standard', source: 2 }),
      option({ label: 'Loose', source: null }),
      option({ label: 'Global', source: 1 }),
      option({ label: 'Batch', source: 2 }),
    ])
    expect(groups.map((g) => [g.source, g.options.map((o) => [o.option.label, o.index])])).toEqual([
      [1, [['Global', 2]]],
      [
        2,
        [
          ['Standard', 0],
          ['Batch', 3],
        ],
      ],
      [null, [['Loose', 1]]],
    ])
  })

  it('is one group when nothing is attributed', () => {
    expect(groupPricingOptions([option(), option({ label: 'Batch' })])).toHaveLength(1)
  })
})

describe('reviewGroups', () => {
  it('has capabilities only for types that have them', () => {
    expect(reviewGroups('prompts')).toEqual(['description', 'configuration', 'pricing'])
    expect(reviewGroups('classifier')).toEqual(['description', 'pricing'])
    expect(reviewGroups(null)).toEqual(['description', 'pricing'])
  })
})

describe('pricingTable', () => {
  it('has a column per stated price kind, input first and output last', () => {
    const table = pricingTable([
      option({ label: 'Standard', price_output: '8', price_input: '2' }),
      option({ label: 'Batch', price_input: '1', price_cached: '0.25', price_output: '4' }),
    ])
    expect(table.columns).toEqual([
      { kind: 'input', unit: '1M tokens' },
      { kind: 'cached', unit: '1M tokens' },
      { kind: 'output', unit: '1M tokens' },
    ])
    expect(table.unit).toBe('1M tokens')
    const [standard, batch] = table.groups[0].rows
    expect(standard.cells.cached).toBeUndefined()
    expect(batch.cells.cached?.amount).toBe('$0.25')
  })

  it('drops the header unit of a column whose rows disagree', () => {
    const table = pricingTable([
      option({ price_input: '2', price_output: '8' }),
      option({ label: 'Per 1K', price_input: '0.002', price_standard_input_unit_count: 1000, price_output: '0.008' }),
    ])
    expect(table.columns).toEqual([
      { kind: 'input', unit: null },
      { kind: 'output', unit: '1M tokens' },
    ])
    expect(table.unit).toBeNull()
    expect(table.groups[0].rows[1].cells.input?.unit).toBe('1K tokens')
  })

  it('puts long-context prices on their option, in the same columns', () => {
    const table = pricingTable([
      option({
        price_input: '3',
        price_output: '15',
        price_long_context_threshold: 200000,
        price_long_context_input: '6',
        price_long_context_cached: '0.6',
        price_long_context_output: '22.5',
      }),
    ])
    expect(table.columns.map((column) => column.kind)).toEqual(['input', 'cached', 'output'])
    const [row] = table.groups[0].rows
    expect(row.longContext?.threshold).toBe('200K')
    expect(row.longContext?.cells.cached?.amount).toBe('$0.6')
    expect(pricingTable([option({ price_input: '1' })]).groups[0].rows[0].longContext).toBeNull()
  })

  it('groups rows by source and keeps the global option index', () => {
    const table = pricingTable([option({ label: 'Standard', source: 2, price_input: '1' }), option({ label: 'Global', source: 1, price_input: '2' })])
    expect(table.groups.map((g) => [g.source, g.rows.map((r) => [r.label, r.index])])).toEqual([
      [1, [['Global', 1]]],
      [2, [['Standard', 0]]],
    ])
  })
})

describe('capabilityItems', () => {
  it('splits yes/no capabilities from valued ones', () => {
    const chat = result({ json_mode: true, tool_calling: false, reasoning_effort_options: ['low', 'high'], vector_size: 1536 })
    expect(capabilityItems(chat, 'prompts')).toEqual({
      flags: [
        { key: 'json_mode', on: true },
        { key: 'tool_calling', on: false },
      ],
      values: [{ key: 'reasoning_effort_options', items: ['low', 'high'] }],
    })
    expect(capabilityItems(chat, 'embeddings')).toEqual({ flags: [], values: [{ key: 'vector_size', items: ['1536'] }] })
  })
})

describe('isNameMatch', () => {
  it('ignores case and punctuation', () => {
    expect(isNameMatch({ ai_model: 'gpt-4.1-mini', display_name: null }, 'GPT-4.1 mini')).toBe(true)
    expect(isNameMatch({ ai_model: 'x-1', display_name: 'Claude Sonnet' }, 'claude sonnet')).toBe(true)
    expect(isNameMatch({ ai_model: 'gpt-4.1-mini', display_name: null }, 'GPT-4.1')).toBe(false)
  })
})
