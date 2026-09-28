/**
 * "Fill from text" (issue #466): turn what `POST models/extract-from-text`
 * read from a pasted docs / pricing page into a create / PATCH payload.
 *
 * Framework-free on purpose — the review step only decides *which* groups to
 * apply and *which* pricing option; the payload rules live here:
 *
 *   - description / configuration apply only the values the text stated
 *     (null = "the text didn't say", never "turn it off");
 *   - configuration is gated on the model type, so a flag the backend read for
 *     a chat model never lands on an embeddings row, and vice versa;
 *   - pricing replaces the **whole** price set from the picked option, so a
 *     stale cache or long-context price from an earlier setup can't survive.
 *     Long-context prices belong to the option (the drawer's Long context
 *     switch is on exactly when `price_long_context_threshold` is set).
 */
import { formatUnitCount } from './formatModelPrice'

export interface ExtractionTarget {
  key: string
  ai_model: string
  display_name?: string | null
  type?: string | null
}

export interface ExtractedPricingOption {
  label: string
  /** 1-based index of the request source the prices were read from. */
  source?: number | null
  price_scheme: string | null
  price_input: string | null
  price_output: string | null
  price_cached: string | null
  price_cache_write: string | null
  price_cache_write_1h: string | null
  price_standard_input_unit_count: number | null
  price_cached_input_unit_count: number | null
  price_standard_output_unit_count: number | null
  price_input_unit_name: string | null
  price_output_unit_name: string | null
  price_long_context_threshold: number | null
  price_long_context_input: string | null
  price_long_context_cached: string | null
  price_long_context_cache_write: string | null
  price_long_context_cache_write_1h: string | null
  price_long_context_output: string | null
}

export interface ExtractedModel {
  target_key: string
  matched_name: string | null
  description: string | null
  json_mode: boolean | null
  json_schema: boolean | null
  tool_calling: boolean | null
  reasoning: boolean | null
  reasoning_effort_options: string[] | null
  supports_temperature: boolean | null
  supports_top_p: boolean | null
  supports_max_tokens: boolean | null
  diarization: boolean | null
  keyterms: boolean | null
  vector_size: number | null
  pricing_options: ExtractedPricingOption[]
}

export interface ExtractionSource {
  text: string
  /** Inferred from the pasted HTML; helps the LLM tell pages apart. */
  site?: string | null
  title?: string | null
}

export interface ExtractFromTextRequest {
  /** A model card and a pricing page are often separate pages; one page may hold both. */
  sources: ExtractionSource[]
  /** Typed instructions ("use EU prices") — never a source of values. */
  notes?: string[]
  provider?: string | null
  targets: ExtractionTarget[]
}

export interface ExtractFromTextResponse {
  results: ExtractedModel[]
}

export type FillGroup = 'description' | 'configuration' | 'pricing'

export interface FillSelection {
  /** Apply anything at all to this model (bulk mode lets the user skip one). */
  apply: boolean
  groups: Record<FillGroup, boolean>
  pricingOptionIndex: number
}

export interface FillContext {
  type?: string | null
  /** The model's current `configs`, merged under an extracted `vector_size`. */
  configs?: Record<string, unknown> | null
}

export type ModelPatch = Record<string, unknown>

/** A model to fill, as the panel receives it; `configs` never goes to the server. */
export interface FillTarget extends ExtractionTarget {
  configs?: Record<string, unknown> | null
}

type ConfigurationField = Exclude<keyof ExtractedModel, 'target_key' | 'matched_name' | 'description' | 'pricing_options'>

const CONFIGURATION_FIELDS_BY_TYPE: Record<string, ConfigurationField[]> = {
  prompts: [
    'json_mode',
    'json_schema',
    'tool_calling',
    'reasoning',
    'reasoning_effort_options',
    'supports_temperature',
    'supports_top_p',
    'supports_max_tokens',
  ],
  stt: ['diarization', 'keyterms'],
  embeddings: ['vector_size'],
}

const PRICE_FIELDS = [
  'price_input',
  'price_output',
  'price_cached',
  'price_cache_write',
  'price_cache_write_1h',
  'price_long_context_input',
  'price_long_context_cached',
  'price_long_context_cache_write',
  'price_long_context_cache_write_1h',
  'price_long_context_output',
] as const

const DEFAULT_UNIT_COUNT = 1000000
const DEFAULT_UNIT_NAME = 'tokens'

export function isFound(result: ExtractedModel | null | undefined): boolean {
  return Boolean(result?.matched_name)
}

/** Configuration fields the text stated, for a model of `type`. */
export function configurationValues(result: ExtractedModel, type?: string | null): Partial<Record<ConfigurationField, unknown>> {
  const fields = CONFIGURATION_FIELDS_BY_TYPE[type ?? ''] ?? []
  const values: Partial<Record<ConfigurationField, unknown>> = {}
  for (const field of fields) {
    const value = result[field]
    if (value == null) continue
    if (Array.isArray(value) && value.length === 0) continue
    values[field] = value
  }
  return values
}

export function configurationPatch(result: ExtractedModel, context: FillContext = {}): ModelPatch {
  const { vector_size, ...flags } = configurationValues(result, context.type)
  const patch: ModelPatch = { ...flags }
  if (vector_size != null) {
    patch.configs = { ...(context.configs ?? {}), vector_size }
  }
  return patch
}

/** Price scheme the option implies when the text didn't name one. */
function inferPriceScheme(option: ExtractedPricingOption): string {
  if (option.price_cache_write_1h || option.price_long_context_cache_write_1h) return 'anthropic'
  if (option.price_cache_write || option.price_long_context_cache_write) return 'openai'
  return 'basic'
}

export function pricingPatch(option: ExtractedPricingOption): ModelPatch {
  const patch: ModelPatch = {}
  for (const field of PRICE_FIELDS) {
    patch[field] = option[field] ?? null
  }
  const scheme = option.price_scheme ?? inferPriceScheme(option)
  patch.price_scheme = scheme
  // The drawer hides cache-write prices the scheme doesn't bill — keep the
  // stored row consistent with what the Pricing tab would show.
  if (scheme === 'basic') {
    patch.price_cache_write = null
    patch.price_long_context_cache_write = null
  }
  if (scheme !== 'anthropic') {
    patch.price_cache_write_1h = null
    patch.price_long_context_cache_write_1h = null
  }
  const inputCount = option.price_standard_input_unit_count ?? DEFAULT_UNIT_COUNT
  patch.price_standard_input_unit_count = inputCount
  patch.price_cached_input_unit_count = option.price_cached_input_unit_count ?? inputCount
  patch.price_standard_output_unit_count = option.price_standard_output_unit_count ?? DEFAULT_UNIT_COUNT
  patch.price_input_unit_name = option.price_input_unit_name ?? DEFAULT_UNIT_NAME
  patch.price_output_unit_name = option.price_output_unit_name ?? DEFAULT_UNIT_NAME
  patch.price_long_context_threshold = option.price_long_context_threshold ?? null
  return patch
}

export function hasGroup(result: ExtractedModel, group: FillGroup, type?: string | null): boolean {
  if (!isFound(result)) return false
  if (group === 'description') return Boolean(result.description)
  if (group === 'configuration') return Object.keys(configurationValues(result, type)).length > 0
  return result.pricing_options.length > 0
}

export function defaultSelection(result: ExtractedModel, type?: string | null): FillSelection {
  return {
    apply: isFound(result),
    groups: {
      description: hasGroup(result, 'description', type),
      configuration: hasGroup(result, 'configuration', type),
      pricing: hasGroup(result, 'pricing', type),
    },
    pricingOptionIndex: 0,
  }
}

/** The fields to send for one model; `{}` when nothing is picked. */
export function buildModelPatch(result: ExtractedModel, selection: FillSelection, context: FillContext = {}): ModelPatch {
  if (!selection.apply || !isFound(result)) return {}
  let patch: ModelPatch = {}
  if (selection.groups.description && result.description) {
    patch.description = result.description
  }
  if (selection.groups.configuration) {
    patch = { ...patch, ...configurationPatch(result, context) }
  }
  const option = result.pricing_options[selection.pricingOptionIndex] ?? result.pricing_options[0]
  if (selection.groups.pricing && option) {
    patch = { ...patch, ...pricingPatch(option) }
  }
  return patch
}

export type PriceLineKind = 'input' | 'cached' | 'cacheWrite' | 'cacheWrite1h' | 'output'

export interface PriceLine {
  kind: PriceLineKind
  /** `$2.5` — the price as stored, never rounded (sub-cent tails matter). */
  amount: string
  /** `1M tokens` */
  unit: string
}

type PriceFieldMap = Record<PriceLineKind, keyof ExtractedPricingOption>

const STANDARD_PRICE_LINES: PriceFieldMap = {
  input: 'price_input',
  cached: 'price_cached',
  cacheWrite: 'price_cache_write',
  cacheWrite1h: 'price_cache_write_1h',
  output: 'price_output',
}

const LONG_CONTEXT_PRICE_LINES: PriceFieldMap = {
  input: 'price_long_context_input',
  cached: 'price_long_context_cached',
  cacheWrite: 'price_long_context_cache_write',
  cacheWrite1h: 'price_long_context_cache_write_1h',
  output: 'price_long_context_output',
}

function priceLines(option: ExtractedPricingOption, fields: PriceFieldMap): PriceLine[] {
  const inputCount = option.price_standard_input_unit_count ?? DEFAULT_UNIT_COUNT
  const inputUnit = option.price_input_unit_name ?? DEFAULT_UNIT_NAME
  const units: Record<PriceLineKind, string> = {
    input: `${formatUnitCount(inputCount)} ${inputUnit}`,
    cached: `${formatUnitCount(option.price_cached_input_unit_count ?? inputCount)} ${inputUnit}`,
    cacheWrite: `${formatUnitCount(option.price_cached_input_unit_count ?? inputCount)} ${inputUnit}`,
    cacheWrite1h: `${formatUnitCount(option.price_cached_input_unit_count ?? inputCount)} ${inputUnit}`,
    output: `${formatUnitCount(option.price_standard_output_unit_count ?? DEFAULT_UNIT_COUNT)} ${option.price_output_unit_name ?? DEFAULT_UNIT_NAME}`,
  }
  return (Object.keys(fields) as PriceLineKind[]).flatMap((kind) => {
    const price = option[fields[kind]]
    if (price == null || String(price).trim() === '') return []
    return [{ kind, amount: `$${String(price).trim()}`, unit: units[kind] }]
  })
}

/** Standard (short-context) prices of a pricing option, input first, output last. */
export function pricingOptionLines(option: ExtractedPricingOption): PriceLine[] {
  return priceLines(option, STANDARD_PRICE_LINES)
}

/** Prices above `price_long_context_threshold`; empty when the option has one tier. */
export function longContextLines(option: ExtractedPricingOption): PriceLine[] {
  if (!option.price_long_context_threshold) return []
  return priceLines(option, LONG_CONTEXT_PRICE_LINES)
}

export interface PricingOptionGroup {
  /** 1-based source index; `null` for options the LLM didn't attribute. */
  source: number | null
  /** `index` is the option's position in `pricing_options` (the selection value). */
  options: { option: ExtractedPricingOption; index: number }[]
}

/**
 * Pricing options by the source they came from, in source order, with
 * unattributed ones last. Indices stay global, so a pick in any group is
 * still one `pricingOptionIndex`.
 */
export function groupPricingOptions(options: ExtractedPricingOption[]): PricingOptionGroup[] {
  const groups = new Map<number | null, PricingOptionGroup>()
  options.forEach((option, index) => {
    const source = option.source ?? null
    const group = groups.get(source) ?? { source, options: [] }
    group.options.push({ option, index })
    groups.set(source, group)
  })
  return [...groups.values()].sort((a, b) => (a.source ?? Infinity) - (b.source ?? Infinity))
}

/** The groups a model of `type` can be filled with, in review order. */
export function reviewGroups(type?: string | null): FillGroup[] {
  return type && CONFIGURATION_FIELDS_BY_TYPE[type] ? ['description', 'configuration', 'pricing'] : ['description', 'pricing']
}

/** Groups the text said nothing about, shown as "Not in the pasted text" rows. */
export function missingGroups(result: ExtractedModel, type?: string | null): FillGroup[] {
  if (!isFound(result)) return []
  return reviewGroups(type).filter((group) => !hasGroup(result, group, type))
}

export type PriceCells = Partial<Record<PriceLineKind, PriceLine>>

export interface PricingTableRow {
  /** Position in `pricing_options` — the selection value. */
  index: number
  label: string
  cells: PriceCells
  /** Prices above the threshold (`200K`); `null` for a single-tier option. */
  longContext: { threshold: string; cells: PriceCells } | null
}

export interface PricingTableColumn {
  kind: PriceLineKind
  /** Stated once in the header when every price in the column shares it. */
  unit: string | null
}

export interface PricingTable {
  /** Stated once for the whole table when every column shares it. */
  unit: string | null
  columns: PricingTableColumn[]
  groups: { source: number | null; rows: PricingTableRow[] }[]
}

const PRICE_LINE_ORDER = Object.keys(STANDARD_PRICE_LINES) as PriceLineKind[]

function cellsOf(lines: PriceLine[]): PriceCells {
  return Object.fromEntries(lines.map((line) => [line.kind, line]))
}

/**
 * Pricing options as a comparison table: one column per price kind any option
 * states (input first, output last), one row per option, grouped by source
 * like `groupPricingOptions`. Long-context prices share the option's columns.
 */
export function pricingTable(options: ExtractedPricingOption[]): PricingTable {
  const groups = groupPricingOptions(options).map(({ source, options: grouped }) => ({
    source,
    rows: grouped.map(({ option, index }): PricingTableRow => {
      const long = longContextLines(option)
      return {
        index,
        label: option.label,
        cells: cellsOf(pricingOptionLines(option)),
        longContext: long.length ? { threshold: formatUnitCount(option.price_long_context_threshold ?? 0), cells: cellsOf(long) } : null,
      }
    }),
  }))
  const rows = groups.flatMap((group) => group.rows)
  const columns = PRICE_LINE_ORDER.flatMap((kind) => {
    const lines = rows.flatMap((row) => [row.cells[kind], row.longContext?.cells[kind]]).filter((line): line is PriceLine => line != null)
    if (lines.length === 0) return []
    const units = new Set(lines.map((line) => line.unit))
    return [{ kind, unit: units.size === 1 ? [...units][0] : null }]
  })
  const units = new Set(columns.map((column) => column.unit))
  const unit = units.size === 1 ? [...units][0] : null
  return { unit, columns, groups }
}

export interface CapabilityItems {
  /** Yes/no capabilities the text stated, in form order. */
  flags: { key: string; on: boolean }[]
  /** Capabilities with values (`reasoning_effort_options`, `vector_size`). */
  values: { key: string; items: string[] }[]
}

export function capabilityItems(result: ExtractedModel, type?: string | null): CapabilityItems {
  const items: CapabilityItems = { flags: [], values: [] }
  for (const [key, value] of Object.entries(configurationValues(result, type))) {
    if (typeof value === 'boolean') items.flags.push({ key, on: value })
    else items.values.push({ key, items: Array.isArray(value) ? value.map(String) : [String(value)] })
  }
  return items
}

function comparableName(name: string | null | undefined): string {
  return (name ?? '').toLowerCase().replace(/[^a-z0-9]/g, '')
}

/** Whether the name the text used is just the model's own name, spelled differently. */
export function isNameMatch(target: Pick<ExtractionTarget, 'ai_model' | 'display_name'>, matchedName: string | null | undefined): boolean {
  const matched = comparableName(matchedName)
  if (!matched) return true
  return [target.ai_model, target.display_name].some((name) => comparableName(name) === matched)
}
