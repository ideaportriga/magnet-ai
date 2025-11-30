import _ from 'lodash'
import { fetchData } from '@shared'

// state
const state = () => ({
  draftText: '',
  enhancedText: [],
  enhancementPrompt: '',
  enhancedTextLoading: false,
})

// getters
const getters = {
  draftText: (state) => state.draftText,
  enhancedText: (state) => state.enhancedText,
  enhancementPrompt: (state) => state.enhancementPrompt,
  enhancementPromptList: (state) => state.prompts,
  enhancedTextLoading: (state) => state.enhancedTextLoading,
}

// mutations
const mutations = {
  setEnhancedText(state, text) {
    state.enhancedText = [text, ...state.enhancedText]
  },
}

// actions
const actions = {
  async enhanceText(
    { getters, commit, state, rootGetters },
    { text, prompt, temperature = 1, model, topP = 1, maxTokens, response_format, system_name_for_model }
  ) {
    const defaultModel = (rootGetters['chroma/model'].items || []).find((el) => el?.is_default && el?.type == 'prompts')
    const config = getters.config?.chatCompletion || {}

    const inputs = {
      messages: [
        {
          role: 'system',
          content: prompt,
        },
        {
          role: 'user',
          content: text,
        },
      ],
    }
    if (temperature) inputs['temperature'] = temperature
    if (model || defaultModel) inputs['model'] = model ? model : defaultModel?.model
    if (topP) inputs['topP'] = topP
    if (maxTokens) inputs['maxTokens'] = maxTokens
    if (response_format) inputs['response_format'] = response_format
    if (system_name_for_model) inputs['system_name_for_model'] = system_name_for_model ? system_name_for_model : defaultModel?.system_name
    commit('set', { enhancedTextLoading: true })

    const response = await fetchData({
      endpoint: config.endpoint,
      service: config.service,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        ...config.inputs,
        ...inputs,
      }),
    })

    commit('set', { enhancedTextLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling enhance text service`,
        },
      })
      return ''
    } else {
      const enhancement = await response.json()
      return enhancement?.['content'] ?? ''
    }
  },
  async enhanceTextDetails(
    { getters, commit, state, rootGetters },
    {
      name,
      text,
      prompt,
      temperature = 1,
      model,
      topP = 1,
      maxTokens,
      response_format,
      system_name_for_model,
      system_name_for_prompt_template,
      prompt_template_variant,
    }
  ) {
    const defaultModel = (rootGetters['chroma/model'].items || []).find((el) => el?.is_default && el?.type == 'prompts')
    const config = getters.config?.chatCompletion || {}

    const inputs = {
      messages: [
        {
          role: 'system',
          content: prompt,
        },
        {
          role: 'user',
          content: text,
        },
      ],
    }
    if (name) inputs['name'] = name
    if (temperature) inputs['temperature'] = temperature
    if (model || defaultModel) inputs['model'] = model ? model : defaultModel?.model
    if (topP) inputs['top_p'] = topP
    if (maxTokens) inputs['max_tokens'] = maxTokens
    if (response_format) inputs['response_format'] = response_format
    if (system_name_for_model) inputs['system_name_for_model'] = system_name_for_model ? system_name_for_model : defaultModel?.system_name
    if (system_name_for_prompt_template) inputs['system_name_for_prompt_template'] = system_name_for_prompt_template
    if (prompt_template_variant) inputs['prompt_template_variant'] = prompt_template_variant
    commit('set', { enhancedTextLoading: true })

    const response = await fetchData({
      endpoint: config.endpoint,
      service: config.service,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        ...config.inputs,
        ...inputs,
      }),
    })

    commit('set', { enhancedTextLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling enhance text details service`,
        },
      })
      return ''
    } else {
      const enhancement = await response.json()
      enhancement['inputs'] = inputs
      return enhancement
    }
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
