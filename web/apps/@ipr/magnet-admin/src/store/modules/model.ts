import { fetchData } from '@shared'
import { createEntityStore } from '../utils'

const baseModelConfig = createEntityStore('modelConfig')

const modelConfig = {
  ...baseModelConfig,
  actions: {
    ...baseModelConfig.actions,

    async setDefault({ getters, rootGetters, commit, state, dispatch }, payload) {
      const endpoint = rootGetters.config?.model?.endpoint
      const service = rootGetters.config?.model?.service || ''
      const credentials = rootGetters.config?.model?.credentials
      console.log('setDefault', payload, endpoint, service)
      // commit('set', { answersLoading: true })
      const response = await fetchData({
        method: 'POST',
        endpoint,
        service: `${service}/set_default`,
        credentials,
        body: JSON.stringify({
          type: payload?.type,
          system_name: payload?.system_name,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      await dispatch('chroma/get', { entity: 'model' }, { root: true })

      if (response?.error) {
        commit(
          'set',
          {
            errorMessage: {
              technicalError: response?.error,
              text: `Error calling set default model service`,
            },
          },
          { root: true }
        )
      }
    },
  },
}

export default modelConfig
