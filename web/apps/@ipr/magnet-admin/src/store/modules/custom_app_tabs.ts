import { fetchData } from '@shared'

const state = () => ({
  invoiceDifferenceExplanation: '',
})

const getters = {
  invoiceDifferenceExplanation: (state) => state.invoiceDifferenceExplanation,
}

const mutations = {}

const actions = {
  parsePdf: async ({ getters }, { file }) => {
    const endpoint = getters.config.api.aiBridge.urlAdmin
    const formData = new FormData()

    if (!file) {
      throw Error('File is mising')
    }

    formData.append('file', file)

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `utils/parse-pdf`,
      body: formData,
      headers: {},
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((pdfContent) => {
        return pdfContent
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error parsing PDF file collection`,
        }
      })
  },

  parseOpenapiSpec: async ({ getters }, { file }) => {
    const endpoint = getters.config.api.aiBridge.urlAdmin
    const formData = new FormData()

    if (!file) {
      throw Error('File is mising')
    }

    formData.append('file', file)

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: 'experimental/parse-openapi-spec',
      body: formData,
      headers: {},
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((pdfContent) => {
        return pdfContent
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error parsing OpenAPI spec file`,
        }
      })
  },

  chatCompletionsWithOpenapiFunctions: async ({ getters }, { data, signal }) => {
    const endpoint = getters.config.api.aiBridge.urlAdmin

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: 'experimental/chat-completions-with-openapi-functions',
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
      signal,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((pdfContent) => {
        return pdfContent
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error running chat completion`,
        }
      })
  },
  //chat-completions-with-assistant-tools
  chatCompletionsWithAssistantTools: async ({ getters }, { data, signal }) => {
    const endpoint = getters.config.api.aiBridge.urlAdmin

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: 'experimental/chat-completions-with-assistant-tools',
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
      signal,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((pdfContent) => {
        return pdfContent
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error running chat completion`,
        }
      })
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
