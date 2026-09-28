import { ref } from 'vue'
import { useStore } from 'vuex'
import { fetchData } from '@shared'

import type { ExtractFromTextRequest, ExtractFromTextResponse } from './modelTextFill'
import { useModelNotify } from './notifyModels'

/** The server's `detail` from a failed request, else its raw text. */
function errorMessage(error: unknown): string {
  const text = error instanceof Error ? error.message : String(error ?? '')
  try {
    const body = JSON.parse(text)
    if (typeof body?.detail === 'string' && body.detail) return body.detail
  } catch {
    // Not JSON — fall through to the text itself.
  }
  return text || 'Could not read the model info from the pasted text.'
}

/**
 * `POST models/extract-from-text` — reads model settings from pasted text via
 * the `MODEL_CONFIG_EXTRACTION` prompt template. Saves nothing, so there is
 * nothing to refresh; failures (missing template, unusable LLM answer)
 * surface as the server's message in an error toast.
 */
export function useExtractModelsFromText() {
  const store = useStore()
  const notify = useModelNotify()
  const isLoading = ref(false)

  async function run(request: ExtractFromTextRequest): Promise<{ success: boolean; data?: ExtractFromTextResponse }> {
    isLoading.value = true
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: store.getters.config?.collections?.endpoint,
        credentials: 'include',
        service: 'models/extract-from-text',
        body: JSON.stringify(request),
        headers: { 'Content-Type': 'application/json' },
      })
      if (response.error) throw response.error
      return { success: true, data: (await response.json()) as ExtractFromTextResponse }
    } catch (error) {
      notify('error', errorMessage(error))
      return { success: false }
    } finally {
      isLoading.value = false
    }
  }

  return { run, isLoading }
}
