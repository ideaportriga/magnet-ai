import _ from 'lodash'
import { fetchData } from '@shared'
import Papa from 'papaparse'

const state = () => ({
  evaluation: {},
  initialEvaluation: null,
  evaluation_job_record: {},
  evaluation_list: [],
})

const getters = {
  evaluation: (state) => state.evaluation,
  evaluation_job_record: (state) => state.evaluation_job_record,
  evaluation_list: (state) => state.evaluation_list,
}

const mutations = {
  setEvaluation(state, payload) {
    state.evaluation = _.cloneDeep(payload)
    state.initialEvaluation = _.cloneDeep(payload)
    state.evaluation_job_record = payload?.results?.[0] || {}
  },

  updateNestedEvaluationProperty(state, { path, value }) {
    _.set(state.evaluation, path, value)
  },

  revertEvaluationChanges(state) {
    state.evaluation = _.cloneDeep(state.initialEvaluation)
  },

  setEvaluationJobRecord(state, payload) {
    state.evaluation_job_record = payload
  },

  setEvaluationList(state, payload) {
    state.evaluation_list = _.cloneDeep(payload)
  },
}

const actions = {
  async getListOfEvaluations({ getters, commit }, { ids }) {
    try {
      commit('set', { loading: true })

      const endpoint = getters.config?.search?.endpoint
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
      commit('setEvaluationList', data?.items || [])
      commit('set', { loading: false })

      return data?.items || []
    } catch (error) {
      commit('set', { loading: false })
      throw {
        technicalError: error.message,
        text: `Error fetching evaluations list`,
      }
    }
  },

  async getEvaluation({ getters, commit }, { id }) {
    try {
      commit('set', { loading: true })

      const endpoint = getters.config?.search?.endpoint
      const params = new URLSearchParams({
        ids: id,
      })
      const response = await fetchData({
        endpoint,
        credentials: 'include',
        service: `evaluations?${params.toString()}`,
      })

      if (!response.ok) throw new Error(response.error || 'Failed to fetch data')

      const data = await response.json()
      commit('setEvaluation', data?.items[0] || {})
      return data?.items[0]
    } catch (error) {
      commit('set', { loading: false })
      throw {
        technicalError: error.message,
        text: `Error in getting evaluation details`,
      }
    }
  },
  async setScore({ getters, commit, state }, payload) {
    const endpoint = getters.config?.search?.endpoint
    const credentials = getters.config?.search?.credentials
    commit('set', { loading: true })

    const { id, result_id, score, score_comment } = payload
    const service = `evaluations/${id}/result/${result_id}/score`

    const response = await fetchData({
      endpoint,
      service,
      credentials,
      method: 'PATCH',
      body: JSON.stringify({ score, score_comment }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { loading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error setting score`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },

  async createJob({ getters, rootGetters, commit, state, dispatch }, payload) {
    const endpoint = getters.config?.search?.endpoint
    const credentials = getters.config?.search?.credentials
    commit('set', { loading: true })

    const response = await fetchData({
      endpoint,
      service: 'scheduler/create-job',
      credentials,
      method: 'POST',
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    dispatch('chroma/get', { entity: 'evaluation_jobs' })

    commit('set', { loading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error starting job`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },

  async generateEvaluationReport({ dispatch }, { ids, download = true }) {
    const evaluations = await dispatch('getListOfEvaluations', { ids })
    console.log('evaluations', ids, evaluations)

    if (!evaluations || evaluations.length === 0) return null

    const csvItems = evaluations.flatMap((evaluation) => {
      if (!evaluation?.results) return []

      const evaluationSetType = evaluation?.type

      return evaluation.results.map((resultItem) => {
        if (!resultItem) {
          return {}
        }

        const mainColumns = {
          Id: resultItem?.id,
          'User input': resultItem?.user_message,
          'Expected result': resultItem?.expected_output,
          Answer: resultItem?.generated_output,
          Iteration: resultItem?.iteration,
          Variant: evaluation?.tool?.variant_name,
          Score: resultItem?.score,
          'Score comment': resultItem?.score_comment,
          'Usage - completion_tokens': resultItem?.usage?.completion_tokens,
          'Usage - prompt_tokens': resultItem?.usage?.prompt_tokens,
          Latency: resultItem?.latency,
        }

        const evaluatedToolConfig = evaluation?.tool

        let additionalColumns = {}

        if (evaluationSetType === 'prompt_eval') {
          additionalColumns = generateColumnsPromptTemplate(evaluatedToolConfig)
        } else if (evaluationSetType === 'rag_eval') {
          additionalColumns = generateColumnsRagTool(evaluatedToolConfig)
        }

        return {
          ...mainColumns,
          ...additionalColumns,
        }
      })
    })

    const csv = Papa.unparse(csvItems, {
      delimiter: ';',
      quotes: true,
    })

    if (download) {
      downloadCSV(csv, 'evaluation_report.csv')
    }

    return csv
  },
}

function downloadCSV(csvContent, fileName) {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', fileName)
  document.body.appendChild(link)
  link.click()

  // Cleanup
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function generateColumnsPromptTemplate(promptTemplateConfig) {
  const variantObject = promptTemplateConfig?.variant_object

  return {
    'Prompt template': promptTemplateConfig.name,
    'Prompt template system name': promptTemplateConfig.system_name,
    'LLM Model': variantObject?.system_name_for_model,
    Temperature: variantObject?.temperature,
    'Top P': variantObject?.topP,
    'Output limit': variantObject?.maxTokens,
  }
}

function generateColumnsRagTool(ragToolConfig) {
  const variantObject = ragToolConfig?.variant_object

  return {
    'RAG name': ragToolConfig.name,
    'RAG System name': ragToolConfig.system_name,
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

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
