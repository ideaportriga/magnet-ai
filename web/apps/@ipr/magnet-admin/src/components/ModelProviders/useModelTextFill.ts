import { computed, reactive, ref, type Ref } from 'vue'

import { buildModelPatch, defaultSelection, type ExtractedModel, type FillSelection, type FillTarget, type ModelPatch } from './modelTextFill'
import { noteBlocksOf, SOURCE_CHAR_LIMIT, sourceBlocksOf, totalSourceChars, type SourceBlock } from './sourceBlocks'
import { useExtractModelsFromText } from './useExtractModelsFromText'

/**
 * State behind "fill from text" (#466), shared by the New Model dialog and the
 * bulk Update From Docs dialog: the pasted source blocks, the extraction
 * result, the user's picks, and the payload those picks produce.
 *
 * Extraction runs when the dialog's primary action is pressed, not on a button
 * of its own. The result is cached against the blocks and targets it was read
 * for, so going Back to the form and pressing Create again doesn't call the
 * LLM a second time unless something changed.
 *
 * Notes alone are not something to read: without a pasted source the dialog
 * behaves as if the field were empty.
 */
export function useModelTextFill(targets: Ref<FillTarget[]>, provider: Ref<string | null | undefined>) {
  const extraction = useExtractModelsFromText()

  const blocks = ref<SourceBlock[]>([])
  const results = ref<ExtractedModel[] | null>(null)
  /** The source blocks the current result was read from, by 1-based index. */
  const resultSources = ref<SourceBlock[]>([])
  const selections = reactive<Record<string, FillSelection>>({})
  const extractedFor = ref('')

  const sources = computed(() => sourceBlocksOf(blocks.value))
  const notes = computed(() => noteBlocksOf(blocks.value).map((block) => block.text))
  const hasText = computed(() => sources.value.length > 0)
  const totalChars = computed(() => totalSourceChars(blocks.value))
  const overLimit = computed(() => totalChars.value > SOURCE_CHAR_LIMIT)
  const signature = computed(() =>
    JSON.stringify([sources.value.map((block) => block.id), notes.value, targets.value.map((t) => [t.key, t.ai_model, t.type ?? ''])])
  )

  const entries = computed(() => {
    if (!results.value) return []
    const byKey = new Map(results.value.map((result) => [result.target_key, result]))
    return targets.value.flatMap((target) => {
      const result = byKey.get(target.key)
      const selection = selections[target.key]
      return result && selection ? [{ target, result, selection }] : []
    })
  })

  const patches = computed<Record<string, ModelPatch>>(() => {
    const out: Record<string, ModelPatch> = {}
    for (const { target, result, selection } of entries.value) {
      const patch = buildModelPatch(result, selection, { type: target.type, configs: target.configs })
      if (Object.keys(patch).length > 0) out[target.key] = patch
    }
    return out
  })

  /** Read the sources; `true` once there is a result for the current input. */
  async function extract(): Promise<boolean> {
    if (!hasText.value || overLimit.value) return false
    if (results.value && extractedFor.value === signature.value) return true
    const forSignature = signature.value
    const forSources = sources.value
    const { success, data } = await extraction.run({
      sources: forSources.map(({ text, site, title }) => ({ text, site, title })),
      notes: notes.value,
      provider: provider.value ?? null,
      targets: targets.value
        .filter((target) => target.ai_model?.trim())
        .map(({ key, ai_model, display_name, type }) => ({
          key,
          ai_model: ai_model.trim(),
          display_name: display_name || null,
          type: type || null,
        })),
    })
    if (!success || !data) return false
    for (const key of Object.keys(selections)) delete selections[key]
    for (const result of data.results) {
      const target = targets.value.find((t) => t.key === result.target_key)
      selections[result.target_key] = defaultSelection(result, target?.type)
    }
    results.value = data.results
    resultSources.value = forSources
    extractedFor.value = forSignature
    return true
  }

  return {
    blocks,
    hasText,
    totalChars,
    overLimit,
    isExtracting: extraction.isLoading,
    extract,
    entries,
    resultSources,
    patches,
  }
}
