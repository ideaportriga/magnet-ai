<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
layouts-details-layout.q-mx-auto(v-else, v-model:name='name', v-model:description='description', v-model:systemName='system_name', :contentContainerStyle='{ maxWidth: "1200px", minWidth: "600px", margin: "0 auto" }')
  template(#content)
    q-tabs.bb-border.full-width(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      no-caps
    )
      q-tab(name='steps', label='Steps')
      q-tab(name='expected_input', label='Expected input')
      q-tab(name='test_inputs', label='Test Inputs')
    .column.no-wrap.q-gap-12.full-height.full-width.overflow-auto.q-mb-sm.q-mt-sm(style='max-height: calc(100vh - 360px) !important')
      template(v-if='tab === "steps"')
        .col-auto.full-width
          .row.items-center.justify-between.q-mb-sm
            .km-heading-6 Steps
            km-btn(label='Add step', icon='add', @click='addStep')
          .q-gutter-sm
            template(v-for='(step, stepIdx) in stepsList', :key='stepIdx')
              .ba-border.border-radius-8.q-pa-8.q-mb-sm
                .row.items-center.justify-between.q-mb-sm
                  .km-field.text-secondary-text Step {{ stepIdx + 1 }}
                  km-btn(icon='delete', flat, dense, color='negative', @click='removeStep(stepIdx)')
                .row.q-gutter-xs.q-mb-sm(v-if='getStepAvailableInputs(stepIdx).length')
                  .km-description.text-secondary-text.col-auto Available:
                  .row.q-gutter-xs.wrap
                    q-chip(
                      v-for='binding in getStepAvailableInputs(stepIdx)',
                      :key='binding',
                      dense,
                      size='sm',
                      color='primary',
                      text-color='white'
                    ) {{ binding }}
                .row.q-col-gutter-sm
                  .col-6(v-for='(prompt, promptIdx) in (step.prompts || [])', :key='promptIdx')
                    .ba-border.border-radius-8.q-pa-6.q-mb-xs
                      .row.items-center.justify-between.q-mb-xs
                        .km-field.text-secondary-text Prompt {{ promptIdx + 1 }}
                        km-btn(icon='delete', flat, dense, color='negative', size='sm', @click='removePrompt(stepIdx, promptIdx)')
                      .km-field.text-secondary-text.q-pb-xs.q-mb-xs Template
                      km-select(
                        :model-value='prompt.prompt_template_id',
                        @update:model-value='(val) => updatePromptTemplate(stepIdx, promptIdx, val)',
                        :options='promptTemplateOptions || []',
                        option-label='name',
                        option-value='system_name',
                        emit-value,
                        map-options,
                        hasDropdownSearch,
                        height='30px',
                        placeholder='Select prompt template'
                      )
                      .km-field.text-secondary-text.q-pb-xs.q-mt-sm
                        .row.items-center
                          span Input
                          q-btn.q-ml-xs(
                            v-if='getPromptPlaceholderKeys(stepIdx, promptIdx).length',
                            flat,
                            dense,
                            size='sm',
                            :label='getPromptInputMode(stepIdx, promptIdx) === "json" ? "Fields" : "JSON"',
                            @click='setPromptInputMode(stepIdx, promptIdx, getPromptInputMode(stepIdx, promptIdx) === "json" ? "keyed" : "json")'
                          )
                      template(v-if='getPromptInputMode(stepIdx, promptIdx) === "keyed" && getPromptPlaceholderKeys(stepIdx, promptIdx).length')
                        .row.q-gutter-sm(v-for='key in getPromptPlaceholderKeys(stepIdx, promptIdx)', :key='key').items-center
                          .col-auto.km-description {{ key }}
                          .col
                            km-input(
                              :label='`{${key}}`',
                              :model-value='getPromptInputValue(stepIdx, promptIdx, key)',
                              @update:model-value='(v) => updatePromptInputValue(stepIdx, promptIdx, key, v)',
                              placeholder='e.g. input.task or result.data'
                            )
                      template(v-else)
                        .km-field.text-secondary-text.q-pb-xs(v-if='getPromptPlaceholderKeys(stepIdx, promptIdx).length') Input (JSON)
                        km-input(
                          :model-value='getPromptInputText(stepIdx, promptIdx)',
                          type='textarea',
                          rows='3',
                          placeholder='{"task": "input.task", "context": "result.data"} or input.task',
                          @update:model-value='(v) => setPromptInputDraft(stepIdx, promptIdx, v)',
                          @blur='commitPromptInput(stepIdx, promptIdx)'
                        )
                        .km-description.text-secondary-text Variable name → value or path (input.task, result.data). Plain string for single placeholder.
                      .km-field.text-secondary-text.q-pb-xs.q-mt-sm Output key
                      km-input(
                        placeholder='e.g. data',
                        :model-value='prompt.output_key ?? ""',
                        @update:model-value='(v) => updatePromptOutputKey(stepIdx, promptIdx, v)'
                      )
                      .km-description.text-secondary-text Store as result.{output_key} (e.g. result.data)
                .row.q-mt-sm
                  km-btn(label='Add prompt', icon='add', flat, dense, @click='addPrompt(stepIdx)')
                template(v-if='false')
                  .row.q-mb-sm.q-mt-sm
                    q-checkbox(
                      :model-value='isStepApiToolCallEnabled(stepIdx)',
                      @update:model-value='(v) => setStepApiToolCallEnabled(stepIdx, v)',
                      label='API tool call'
                    )
                  .ba-border.border-radius-8.q-pa-6.q-mb-sm(v-if='isStepApiToolCallEnabled(stepIdx)')
                    .km-field.text-secondary-text.q-pb-xs.q-mb-xs API Server
                    km-select(
                      :model-value='getStepApiToolCall(stepIdx)?.api_server ?? ""',
                      @update:model-value='(v) => updateStepApiToolCall(stepIdx, "api_server", v)',
                      :options='apiServers || []',
                      option-label='name',
                      option-value='system_name',
                      emit-value,
                      map-options,
                      hasDropdownSearch,
                      height='30px',
                      placeholder='Select API server'
                    )
                    .km-field.text-secondary-text.q-pb-xs.q-mt-sm API Tool
                    km-select(
                      :model-value='getStepApiToolCall(stepIdx)?.api_tool ?? ""',
                      @update:model-value='(v) => updateStepApiToolCall(stepIdx, "api_tool", v)',
                      :options='getStepApiToolTools(stepIdx) || []',
                      option-label='label',
                      option-value='value',
                      emit-value,
                      map-options,
                      hasDropdownSearch,
                      height='30px',
                      placeholder='Select API tool'
                    )
                    .km-field.text-secondary-text.q-pb-xs.q-mt-sm Body (JSON)
                    km-input(
                      :model-value='getStepApiToolCallBody(stepIdx)',
                      type='textarea',
                      rows='4',
                      placeholder='{"key": "input.task"}',
                      @update:model-value='(v) => setStepApiToolCallBodyDraft(stepIdx, v)',
                      @blur='commitStepApiToolCallBody(stepIdx)'
                    )
                    .km-field.text-secondary-text.q-pb-xs.q-mt-sm Output key
                    km-input(
                      placeholder='e.g. api_result',
                      :model-value='getStepApiToolCall(stepIdx)?.output_key ?? ""',
                      @update:model-value='(v) => updateStepApiToolCall(stepIdx, "output_key", v)'
                    )
                    .km-description.text-secondary-text Store as result.{output_key} (e.g. result.api_result)
              .row.justify-center.q-py-xs(v-if='stepIdx < stepsList.length - 1')
                q-icon(name='arrow_downward', size='24px', color='grey-6')
          .ba-border.border-radius-8.q-pa-8.q-mt-sm(v-if='stepsList.length && allOutputKeys.length')
            .km-field.text-secondary-text.q-mb-sm Available outputs
            .row.q-gutter-xs.wrap
              q-chip(
                v-for='binding in allOutputKeys',
                :key='binding',
                dense,
                size='sm',
                color='primary',
                text-color='white'
              ) {{ binding }}
      template(v-if='tab === "expected_input"')
        .col-auto.full-width
          .km-heading-6.q-mb-sm Expected input parameters
          .km-description.text-secondary-text.q-mb-sm Parameters to provide when running this queue
          .row.q-gutter-sm.items-center.q-mb-sm
            km-input(
              :model-value='newParamName',
              @update:model-value='newParamName = $event',
              placeholder='e.g. task, query',
              style='max-width: 200px',
              @keydown.enter.prevent='addExpectedInputParam'
            )
            km-btn(label='Add', icon='add', flat, dense, @click='addExpectedInputParam')
          .q-gutter-sm
            .row.q-gutter-sm(v-for='param in expectedInputParams', :key='param')
              q-chip(
                dense,
                :color='isManuallyAddedParam(param) ? "primary" : "grey-4"',
                :text-color='isManuallyAddedParam(param) ? "white" : "grey-9"',
                removable,
                @remove='removeExpectedInputParam(param)'
              ) {{ param }}
          .q-mt-sm(v-if='!expectedInputParams.length && !newParamName')
            .km-description.text-secondary-text No input parameters. Add above or reference input.task, input.query in prompts.
      template(v-if='tab === "test_inputs"')
        .col-auto.full-width
          .km-heading-6.q-mb-sm Test Inputs
          .km-description.text-secondary-text.q-mb-sm Save input value sets to quickly load them in the Execute drawer
          .row.q-gutter-sm.items-center.q-mb-sm
            km-input(
              :model-value='newTestInputName',
              @update:model-value='newTestInputName = $event',
              placeholder='Test name',
              style='max-width: 200px',
              @keydown.enter.prevent='addTestInput'
            )
            km-btn(label='Add', icon='add', flat, dense, @click='addTestInput')
          .q-gutter-sm
            .ba-border.border-radius-8.q-pa-8.q-mb-sm(v-for='(ti, tiIdx) in testInputsList', :key='tiIdx')
              .row.items-center.justify-between.q-mb-sm
                .km-field.text-secondary-text {{ ti.name }}
                km-btn(icon='delete', flat, dense, color='negative', size='sm', @click='removeTestInput(tiIdx)')
              .row.q-gutter-sm(v-for='param in expectedInputParams', :key='param')
                .col-auto.km-description(style='min-width: 100px') {{ param }}
                .col
                  km-input(
                    :model-value='getTestInputValue(tiIdx, param)',
                    @update:model-value='(v) => setTestInputValue(tiIdx, param, v)',
                    placeholder='Value',
                    style='max-width: 300px'
                  )
          .q-mt-sm(v-if='!testInputsList.length')
            .km-description.text-secondary-text No test inputs. Add above. Define expected input params in Expected input tab first.
  template(#drawer)
    prompt-queue-execute-drawer(
      v-if='executeDrawerOpen',
      :open='executeDrawerOpen',
      :config-id='configId',
      :expected-input-params='expectedInputParams || []',
      :test-inputs='testInputsList',
      @update:open='(v) => store.commit("setExecuteDrawerOpen", v)'
    )
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'

const store = useStore()
const route = useRoute()

const configId = computed(() => route.params.id)
const loading = ref(true)
const executeDrawerOpen = computed(() => store.getters.executeDrawerOpen ?? false)
const tab = ref('steps')
const newParamName = ref('')
const newTestInputName = ref('')
const promptInputDrafts = ref({})
const promptInputMode = ref({})
const apiToolCallBodyDrafts = ref({})

const config = ref(null)

const promptInputKey = (stepIdx, promptIdx) => `${stepIdx}-${promptIdx}`

const getPromptInputMode = (stepIdx, promptIdx) => {
  const key = promptInputKey(stepIdx, promptIdx)
  if (promptInputMode.value[key]) return promptInputMode.value[key]
  return getPromptPlaceholderKeys(stepIdx, promptIdx).length ? 'keyed' : 'json'
}

const setPromptInputMode = (stepIdx, promptIdx, mode) => {
  const key = promptInputKey(stepIdx, promptIdx)
  if (mode === 'keyed') delete promptInputDrafts.value[key]
  promptInputMode.value[key] = mode
}

const name = computed({
  get: () => config.value?.name ?? '',
  set: (v) => {
    if (config.value) config.value.name = v
  },
})

const description = computed({
  get: () => config.value?.description ?? '',
  set: (v) => {
    if (config.value) config.value.description = v
  },
})

const system_name = computed({
  get: () => config.value?.system_name ?? '',
  set: (v) => {
    if (config.value) config.value.system_name = v
  },
})

const stepsList = computed(() => {
  const stepsData = config.value?.config?.steps
  if (!Array.isArray(stepsData)) return []
  return stepsData.map((s) => {
    if (Array.isArray(s?.prompts)) {
      return { prompts: s.prompts.map((p) => ({
        prompt_template_id: p.prompt_template_id ?? '',
        input: p.input ?? null,
        output_key: p.output_key ?? null,
      })) }
    }
    if (Array.isArray(s?.prompt_template_ids)) {
      return {
        prompts: s.prompt_template_ids.map((id) => ({
          prompt_template_id: id,
          input: null,
          output_key: null,
        })),
      }
    }
    return { prompts: [] }
  })
})

const getPromptTemplateBySystemName = (systemName) => {
  return promptTemplates.value.find((p) => p.system_name === systemName)
}

const getPromptTemplateText = (systemName) => {
  const prompt = getPromptTemplateBySystemName(systemName)
  if (!prompt?.variants?.length) return ''
  const activeVariant = prompt.active_variant
  const variant = prompt.variants.find((v) => v.variant === activeVariant) || prompt.variants[0]
  return variant?.text ?? ''
}

const getPromptPlaceholderKeys = (stepIdx, promptIdx) => {
  const prompt = config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]
  const templateId = prompt?.prompt_template_id
  if (!templateId) return []
  const text = getPromptTemplateText(templateId)
  const keys = [...new Set((text.match(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g) || []).map((m) => m.slice(1, -1)))]
  return keys
}

const getPromptInputValue = (stepIdx, promptIdx, key) => {
  const prompt = config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]
  if (!prompt?.input || typeof prompt.input !== 'object') return ''
  const val = prompt.input[key]
  return val != null ? String(val) : ''
}

const updatePromptInputValue = (stepIdx, promptIdx, key, val) => {
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  const prompt = config.value.config.steps[stepIdx].prompts[promptIdx]
  if (!prompt.input) prompt.input = {}
  if (val?.trim()) {
    prompt.input[key] = val.trim()
  } else {
    delete prompt.input[key]
    if (Object.keys(prompt.input).length === 0) prompt.input = null
  }
}

const getPromptInputText = (stepIdx, promptIdx) => {
  const key = promptInputKey(stepIdx, promptIdx)
  if (promptInputDrafts.value[key] !== undefined) return promptInputDrafts.value[key]
  const prompt = config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]
  if (!prompt?.input) return ''
  try {
    return JSON.stringify(prompt.input, null, 2)
  } catch {
    return ''
  }
}

const setPromptInputDraft = (stepIdx, promptIdx, val) => {
  promptInputDrafts.value[promptInputKey(stepIdx, promptIdx)] = val ?? ''
}

const commitPromptInput = (stepIdx, promptIdx) => {
  const key = promptInputKey(stepIdx, promptIdx)
  const val = promptInputDrafts.value[key]
  const trimmed = val?.trim()
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  if (!trimmed) {
    delete promptInputDrafts.value[key]
    config.value.config.steps[stepIdx].prompts[promptIdx].input = null
    return
  }
  try {
    const parsed = JSON.parse(trimmed)
    if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
      delete promptInputDrafts.value[key]
      config.value.config.steps[stepIdx].prompts[promptIdx].input = parsed
    } else if (typeof parsed === 'string') {
      const keys = getPromptPlaceholderKeys(stepIdx, promptIdx)
      if (keys.length === 1) {
        delete promptInputDrafts.value[key]
        config.value.config.steps[stepIdx].prompts[promptIdx].input = { [keys[0]]: parsed }
      }
    }
  } catch {
    const keys = getPromptPlaceholderKeys(stepIdx, promptIdx)
    if (keys.length === 1 && (trimmed.startsWith('input.') || trimmed.startsWith('result.'))) {
      delete promptInputDrafts.value[key]
      config.value.config.steps[stepIdx].prompts[promptIdx].input = { [keys[0]]: trimmed }
    }
  }
}

const updatePromptTemplate = (stepIdx, promptIdx, val) => {
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  config.value.config.steps[stepIdx].prompts[promptIdx].prompt_template_id = val ?? ''
}

const updatePromptOutputKey = (stepIdx, promptIdx, val) => {
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  config.value.config.steps[stepIdx].prompts[promptIdx].output_key = val?.trim() || null
}

const ensurePrompts = (stepIdx) => {
  if (!config.value?.config?.steps?.[stepIdx]) return
  const step = config.value.config.steps[stepIdx]
  if (Array.isArray(step.prompt_template_ids) && !Array.isArray(step.prompts)) {
    step.prompts = step.prompt_template_ids.map((id) => ({
      prompt_template_id: id,
      input: null,
      output_key: null,
    }))
    delete step.prompt_template_ids
  }
  if (!Array.isArray(step.prompts)) {
    step.prompts = []
  }
}

const addPrompt = (stepIdx) => {
  ensurePrompts(stepIdx)
  config.value.config.steps[stepIdx].prompts.push({
    prompt_template_id: '',
    input: null,
    output_key: null,
  })
}

const removePrompt = (stepIdx, promptIdx) => {
  if (!config.value?.config?.steps?.[stepIdx]?.prompts) return
  config.value.config.steps[stepIdx].prompts.splice(promptIdx, 1)
}

const promptTemplates = computed(() => {
  return store.getters['chroma/promptTemplates']?.items || []
})

const apiServers = computed(() => {
  return store.getters['chroma/api_servers']?.items || []
})

const getStepApiToolCall = (stepIdx) => {
  return config.value?.config?.steps?.[stepIdx]?.api_tool_call
}

const isStepApiToolCallEnabled = (stepIdx) => {
  return !!getStepApiToolCall(stepIdx)?.enabled
}

const setStepApiToolCallEnabled = (stepIdx, enabled) => {
  ensureStep(stepIdx)
  const step = config.value?.config?.steps?.[stepIdx]
  if (!step) return
  if (enabled) {
    if (!step.api_tool_call) {
      step.api_tool_call = { enabled: true, api_server: '', api_tool: '', body: '', output_key: null }
    } else {
      step.api_tool_call.enabled = true
    }
  } else {
    if (step.api_tool_call) {
      step.api_tool_call.enabled = false
    }
  }
}

const updateStepApiToolCall = (stepIdx, field, value) => {
  ensureStep(stepIdx)
  const step = config.value?.config?.steps?.[stepIdx]
  if (!step) return
  if (!step.api_tool_call) step.api_tool_call = { enabled: true, api_server: '', api_tool: '', body: '', output_key: null }
  if (field === 'output_key') {
    step.api_tool_call.output_key = value?.trim() || null
  } else {
    step.api_tool_call[field] = value ?? ''
  }
  if (field === 'api_server') {
    step.api_tool_call.api_tool = ''
  }
}

const getStepApiToolTools = (stepIdx) => {
  const serverName = getStepApiToolCall(stepIdx)?.api_server
  if (!serverName) return []
  const server = apiServers.value.find((s) => s.system_name === serverName)
  return (server?.tools || []).map((t) => ({ label: t.name, value: t.system_name }))
}

const getStepApiToolCallBody = (stepIdx) => {
  if (apiToolCallBodyDrafts.value[stepIdx] !== undefined) return apiToolCallBodyDrafts.value[stepIdx]
  const body = getStepApiToolCall(stepIdx)?.body
  return body ?? ''
}

const setStepApiToolCallBodyDraft = (stepIdx, val) => {
  apiToolCallBodyDrafts.value[stepIdx] = val ?? ''
}

const commitStepApiToolCallBody = (stepIdx) => {
  const val = apiToolCallBodyDrafts.value[stepIdx]
  delete apiToolCallBodyDrafts.value[stepIdx]
  ensureStep(stepIdx)
  const step = config.value?.config?.steps?.[stepIdx]
  if (!step?.api_tool_call) return
  step.api_tool_call.body = val?.trim() ?? ''
}

const ensureStep = (stepIdx) => {
  if (!config.value?.config?.steps?.[stepIdx]) return
}

const promptTemplateOptions = computed(() => {
  return promptTemplates.value.map((p) => ({
    name: p.name,
    system_name: p.system_name,
  }))
})

const allOutputKeys = computed(() => {
  const seen = new Set()
  const bindings = []
  const steps = config.value?.config?.steps
  if (!Array.isArray(steps)) return []
  for (const step of steps) {
    const prompts = step?.prompts || []
    for (const prompt of prompts) {
      const key = prompt?.output_key
      if (typeof key === 'string' && key.trim()) {
        const b = `result.${key.trim()}`
        if (!seen.has(b)) {
          seen.add(b)
          bindings.push(b)
        }
      }
    }
    const apiKey = step?.api_tool_call?.output_key
    if (typeof apiKey === 'string' && apiKey.trim()) {
      const b = `result.${apiKey.trim()}`
      if (!seen.has(b)) {
        seen.add(b)
        bindings.push(b)
      }
    }
  }
  return bindings
})

const getStepAvailableInputs = (stepIdx) => {
  const seen = new Set()
  const bindings = []
  for (const param of (expectedInputParams.value || [])) {
    const b = `input.${param}`
    if (!seen.has(b)) {
      seen.add(b)
      bindings.push(b)
    }
  }
  const steps = config.value?.config?.steps
  if (Array.isArray(steps)) {
    for (let i = 0; i < stepIdx && i < steps.length; i++) {
      const prompts = steps[i]?.prompts || []
      for (const prompt of prompts) {
        const key = prompt?.output_key
        if (typeof key === 'string' && key.trim()) {
          const b = `result.${key.trim()}`
          if (!seen.has(b)) {
            seen.add(b)
            bindings.push(b)
          }
        }
      }
      const apiKey = steps[i]?.api_tool_call?.output_key
      if (typeof apiKey === 'string' && apiKey.trim()) {
        const b = `result.${apiKey.trim()}`
        if (!seen.has(b)) {
          seen.add(b)
          bindings.push(b)
        }
      }
    }
  }
  return bindings
}

const expectedInputParams = computed(() => {
  const params = new Set()
  const steps = config.value?.config?.steps
  if (Array.isArray(steps)) {
    for (const step of steps) {
      const prompts = step?.prompts || []
      for (const prompt of prompts) {
        const input = prompt?.input
        if (input && typeof input === 'object') {
          for (const val of Object.values(input)) {
            if (typeof val === 'string' && val.startsWith('input.')) {
              const param = val.slice(6).trim()
              if (param) params.add(param)
            }
          }
        }
      }
    }
  }
  const manual = config.value?.config?.expected_input
  if (Array.isArray(manual)) {
    for (const p of manual) {
      if (typeof p === 'string' && p.trim()) params.add(p.trim())
    }
  }
  const exclude = new Set(config.value?.config?.expected_input_exclude || [])
  return [...params].filter((p) => !exclude.has(p)).sort()
})

const isManuallyAddedParam = (param) => {
  const manual = config.value?.config?.expected_input
  if (!Array.isArray(manual)) return false
  return manual.some((p) => String(p).trim() === param)
}

const addExpectedInputParam = () => {
  const name = newParamName.value?.trim()
  if (!name) return
  if (!config.value) config.value = {}
  if (!config.value.config) config.value.config = {}
  if (!Array.isArray(config.value.config.expected_input)) {
    config.value.config.expected_input = []
  }
  if (!config.value.config.expected_input.includes(name)) {
    config.value.config.expected_input.push(name)
    config.value.config.expected_input.sort()
  }
  newParamName.value = ''
}

const testInputsList = computed(() => {
  const list = config.value?.config?.test_inputs
  return Array.isArray(list) ? list : []
})

const addTestInput = () => {
  const name = newTestInputName.value?.trim()
  if (!name) return
  if (!config.value) config.value = {}
  if (!config.value.config) config.value.config = {}
  if (!Array.isArray(config.value.config.test_inputs)) {
    config.value.config.test_inputs = []
  }
  config.value.config.test_inputs.push({ name, values: {} })
  newTestInputName.value = ''
}

const removeTestInput = (idx) => {
  if (!config.value?.config?.test_inputs) return
  config.value.config.test_inputs.splice(idx, 1)
  if (config.value.config.test_inputs.length === 0) {
    delete config.value.config.test_inputs
  }
}

const getTestInputValue = (tiIdx, param) => {
  const ti = config.value?.config?.test_inputs?.[tiIdx]
  if (!ti?.values) return ''
  return ti.values[param] ?? ''
}

const setTestInputValue = (tiIdx, param, val) => {
  if (!config.value?.config?.test_inputs?.[tiIdx]) return
  const ti = config.value.config.test_inputs[tiIdx]
  if (!ti.values) ti.values = {}
  if (val?.trim()) {
    ti.values[param] = val.trim()
  } else {
    delete ti.values[param]
  }
}

const removeExpectedInputParam = (param) => {
  if (!config.value?.config) return
  const manual = config.value.config.expected_input
  if (Array.isArray(manual)) {
    const idx = manual.indexOf(param)
    if (idx >= 0) {
      config.value.config.expected_input.splice(idx, 1)
      if (config.value.config.expected_input.length === 0) {
        delete config.value.config.expected_input
      }
      return
    }
  }
  if (!Array.isArray(config.value.config.expected_input_exclude)) {
    config.value.config.expected_input_exclude = []
  }
  if (!config.value.config.expected_input_exclude.includes(param)) {
    config.value.config.expected_input_exclude.push(param)
    config.value.config.expected_input_exclude.sort()
  }
}

const addStep = () => {
  if (!config.value) config.value = { config: {} }
  if (!config.value.config) config.value.config = {}
  if (!Array.isArray(config.value.config.steps)) config.value.config.steps = []
  config.value.config.steps.push({ prompts: [] })
}

const removeStep = (idx) => {
  if (!config.value?.config?.steps) return
  config.value.config.steps.splice(idx, 1)
}

const migrateLegacySteps = () => {
  const steps = config.value?.config?.steps
  if (!Array.isArray(steps)) return
  steps.forEach((step) => {
    if (Array.isArray(step.prompt_template_ids) && !Array.isArray(step.prompts)) {
      step.prompts = step.prompt_template_ids.map((id) => ({
        prompt_template_id: id,
        input: null,
        output_key: null,
      }))
      delete step.prompt_template_ids
    }
    if (!Array.isArray(step.prompts)) {
      step.prompts = []
    }
  })
}

const loadConfig = () => {
  const configs = store.getters.promptQueueConfigs
  if (!Array.isArray(configs)) return
  const found = configs.find((c) => c.id === configId.value)
  if (found) {
    config.value = JSON.parse(JSON.stringify(found))
    migrateLegacySteps()
  }
}

onMounted(async () => {
  await store.dispatch('fetchPromptQueueConfigs', true)
  if (!store.getters['chroma/promptTemplates']?.items?.length) {
    store.dispatch('chroma/get', { entity: 'promptTemplates' })
  }
  if (!store.getters['chroma/api_servers']?.items?.length) {
    store.dispatch('chroma/get', { entity: 'api_servers' })
  }
  let cfg = store.getters.promptQueueConfigs?.find((c) => c.id === configId.value)
  if (!cfg) {
    cfg = await store.dispatch('fetchPromptQueueConfigById', configId.value)
  }
  if (cfg) {
    config.value = JSON.parse(JSON.stringify(cfg))
    if (!config.value.config) config.value.config = {}
    if (!Array.isArray(config.value.config.steps)) config.value.config.steps = []
    migrateLegacySteps()
  } else {
    loadConfig()
  }
  loading.value = false
})

watch(() => configId.value, () => {
  loadConfig()
})

watch(() => store.getters.promptQueueConfigs, () => {
  if (!config.value && configId.value) loadConfig()
}, { deep: true })

watch(config, (val) => {
  if (val && configId.value) {
    store.commit('setSelectedPromptQueueConfig', JSON.parse(JSON.stringify(val)))
  }
}, { deep: true })
</script>

<style lang="stylus" scoped>
.collection-container {
  min-width: 600px;
  max-width: 1200px;
  width: 100%;
}

.ba-border
  border-color: rgba(0, 0, 0, 0.24) !important

.bb-border
  border-bottom-color: rgba(0, 0, 0, 0.24) !important
</style>
