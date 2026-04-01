import { defineStore } from 'pinia'
import { ref } from 'vue'
import { cloneDeep } from 'lodash'
import { fetchData } from '@shared'
import Papa from 'papaparse'
import { useAppStore } from './appStore'

export const useEvaluationStore = defineStore('evaluation', () => {
  const appStore = useAppStore()

  const evaluation = ref<Record<string, any>>({})
  const initialEvaluation = ref<Record<string, any> | null>(null)
  const evaluationJobRecord = ref<Record<string, any>>({})
  const evaluationList = ref<any[]>([])

  function setEvaluation(payload: any) {
    evaluation.value = cloneDeep(payload)
    initialEvaluation.value = cloneDeep(payload)
    evaluationJobRecord.value = payload?.results?.[0] || {}
  }

  function updateNestedProperty({ path, value }: { path: string; value: any }) {
    const { set } = require('lodash')
    set(evaluation.value, path, value)
  }

  function revertChanges() {
    evaluation.value = cloneDeep(initialEvaluation.value)
  }

  function setEvaluationJobRecord(payload: any) {
    evaluationJobRecord.value = payload
  }

  async function getListOfEvaluations({ ids }: { ids: string | string[] }) {
    const endpoint = appStore.config?.search?.endpoint
    const params = new URLSearchParams()
    if (Array.isArray(ids)) {
      ids.forEach((id) => params.append('ids', id))
    } else if (ids) {
      params.append('ids', ids)
    }

    const response = await fetchData({
      endpoint,
      credentials: 'include',
      service: `evaluations?${params.toString()}`,
    })

    if (!response.ok) throw new Error(response.error || 'Failed to fetch evaluations list')

    const data = await response.json()
    evaluationList.value = cloneDeep(data?.items || [])
    return data?.items || []
  }

  async function getEvaluation({ id }: { id: string }) {
    const endpoint = appStore.config?.search?.endpoint
    const params = new URLSearchParams({ ids: id })
    const response = await fetchData({
      endpoint,
      credentials: 'include',
      service: `evaluations?${params.toString()}`,
    })

    if (!response.ok) throw new Error(response.error || 'Failed to fetch data')

    const data = await response.json()
    setEvaluation(data?.items[0] || {})
    return data?.items[0]
  }

  async function setScore(payload: { id: string; result_id: string; score: any; score_comment: string }) {
    const endpoint = appStore.config?.search?.endpoint
    const { id, result_id, score, score_comment } = payload
    const service = `evaluations/${id}/result/${result_id}/score`

    const response = await fetchData({
      endpoint,
      service,
      credentials: 'include',
      method: 'PATCH',
      body: JSON.stringify({ score, score_comment }),
      headers: { 'Content-Type': 'application/json' },
    })

    if (response?.error) {
      throw new Error(response.error)
    }

    return response.json()
  }

  async function createJob(payload: string) {
    const endpoint = appStore.config?.search?.endpoint

    const response = await fetchData({
      endpoint,
      service: 'scheduler/create-job',
      credentials: 'include',
      method: 'POST',
      body: payload,
      headers: { 'Content-Type': 'application/json' },
    })

    if (response?.error) {
      throw new Error(response.error)
    }

    return response.json()
  }

  async function generateEvaluationReport({ ids, download = true }: { ids: string[]; download?: boolean }) {
    const evaluations = await getListOfEvaluations({ ids })

    if (!evaluations || evaluations.length === 0) return null

    const csvItems = evaluations.flatMap((ev: any) => {
      if (!ev?.results) return []

      const evaluationSetType = ev?.type

      return ev.results.map((resultItem: any) => {
        if (!resultItem) return {}

        const mainColumns = {
          Id: resultItem?.id,
          'User input': resultItem?.user_message,
          'Expected result': resultItem?.expected_output,
          Answer: resultItem?.generated_output,
          Iteration: resultItem?.iteration,
          Variant: ev?.tool?.variant_name,
          Score: resultItem?.score,
          'Score comment': resultItem?.score_comment,
          'Usage - completion_tokens': resultItem?.usage?.completion_tokens,
          'Usage - prompt_tokens': resultItem?.usage?.prompt_tokens,
          Latency: resultItem?.latency,
        }

        const evaluatedToolConfig = ev?.tool
        let additionalColumns = {}

        if (evaluationSetType === 'prompt_eval') {
          const variantObject = evaluatedToolConfig?.variant_object
          additionalColumns = {
            'Prompt template': evaluatedToolConfig.name,
            'Prompt template system name': evaluatedToolConfig.system_name,
            'LLM Model': variantObject?.system_name_for_model,
            Temperature: variantObject?.temperature,
            'Top P': variantObject?.topP,
            'Output limit': variantObject?.maxTokens,
          }
        } else if (evaluationSetType === 'rag_eval') {
          const variantObject = evaluatedToolConfig?.variant_object
          additionalColumns = {
            'RAG name': evaluatedToolConfig.name,
            'RAG System name': evaluatedToolConfig.system_name,
            'Knowledge source(s)': variantObject?.retrieve?.collection_system_names,
            'Similarity score threshold': variantObject?.retrieve?.similarity_score_threshold,
            'Number of chunks to select': variantObject?.retrieve?.max_chunks_retrieved,
            'Context window expansion size': variantObject?.retrieve?.chunk_context_window_expansion_size,
            'Generation prompt template': variantObject?.generate?.prompt_template,
            'Multi-lingual RAG enabled ': variantObject?.language?.multilanguage?.enabled,
            'Translation prompt template': variantObject?.language?.multilanguage?.prompt_template,
            'RAG Tool source language': variantObject?.language?.multilanguage?.source_language,
          }
        }

        return { ...mainColumns, ...additionalColumns }
      })
    })

    const csv = Papa.unparse(csvItems, { delimiter: ';', quotes: true })

    if (download) {
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', 'evaluation_report.csv')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }

    return csv
  }

  return {
    evaluation,
    initialEvaluation,
    evaluationJobRecord,
    evaluationList,
    setEvaluation,
    updateNestedProperty,
    revertChanges,
    setEvaluationJobRecord,
    getListOfEvaluations,
    getEvaluation,
    setScore,
    createJob,
    generateEvaluationReport,
  }
})
