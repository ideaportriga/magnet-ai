<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else, style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-sm.relative-position.q-px-md
        .row.items-center.q-gap-8.no-wrap.full-width.q-mt-md.q-mb-xs.bg-white.border-radius-8.q-py-8.q-px-12
          .col
            .row.items-center
              km-input.km-heading-4.full-width.text-black(placeholder='Name', :model-value='name', @update:model-value='name = $event')
            .row.items-center
              km-input.km-description.full-width.text-black(placeholder='Description', :model-value='description', @update:model-value='description = $event')
            .row.items-center.q-pl-4
              q-icon.col-auto(name='o_info', color='text-secondary')
                q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
              km-input.col.km-description.full-width(
                placeholder='Enter system name',
                :model-value='system_name',
                @update:model-value='system_name = $event',
                @focus='showInfo = true',
                @blur='showInfo = false'
              )
            .km-description.text-secondary.q-pl-4(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
        .ba-border.bg-white.border-radius-12.q-pa-12(style='min-width: 300px')
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
            q-tab(name='execute', label='Execute')
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
                          color='grey-3',
                          text-color='grey-9'
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
                          template(v-if='getPromptPlaceholderKeys(stepIdx, promptIdx).length')
                            .km-field.text-secondary-text.q-pb-xs.q-mt-sm Input
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
                            .km-field.text-secondary-text.q-pb-xs.q-mt-sm Input (JSON)
                            km-input(
                              :model-value='getPromptInputText(stepIdx, promptIdx)',
                              type='textarea',
                              rows='3',
                              placeholder='{"task": "input.task", "context": "result.data"}',
                              @update:model-value='(v) => setPromptInputDraft(stepIdx, promptIdx, v)',
                              @blur='commitPromptInput(stepIdx, promptIdx)'
                            )
                            .km-description.text-secondary-text Variable name → value or path (input.task, result.data)
                          .km-field.text-secondary-text.q-pb-xs.q-mt-sm Output key
                          km-input(
                            placeholder='e.g. data',
                            :model-value='prompt.output_key ?? ""',
                            @update:model-value='(v) => updatePromptOutputKey(stepIdx, promptIdx, v)'
                          )
                          .km-description.text-secondary-text Store as result.{output_key} (e.g. result.data)
                    .row.q-mt-sm
                      km-btn(label='Add prompt', icon='add', flat, dense, @click='addPrompt(stepIdx)')
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
            template(v-if='tab === "execute"')
              .col-auto.full-width
                .km-heading-6.q-mb-sm Execute
                .km-description.text-secondary-text.q-mb-sm Run the queue with the input values below
                .q-gutter-sm.q-mb-sm
                  .row.q-gutter-sm(v-for='param in expectedInputParams', :key='param')
                    .col-auto.km-field(style='min-width: 120px') {{ param }}
                    .col
                      km-input(
                        :model-value='executeInput[param]',
                        @update:model-value='executeInput[param] = $event',
                        placeholder='Enter value',
                        style='max-width: 400px'
                      )
                .row.q-gutter-sm.items-center.q-mb-sm
                  km-btn(label='Execute', icon='play_arrow', @click='execute', :loading='executing')
                  .km-description.text-secondary-text(v-if='!expectedInputParams.length') No input params. Add in Expected input tab or use empty input.
                .ba-border.border-radius-8.q-pa-8.q-mt-sm(v-if='executeResult !== null')
                  .km-field.text-secondary-text.q-mb-sm Result
                  pre.km-description.q-ma-none(style='white-space: pre-wrap; word-break: break-word; max-height: 400px; overflow: auto') {{ JSON.stringify(executeResult, null, 2) }}
        .row.q-mt-md.justify-end
          km-btn(label='Save', @click='save', :loading='saving')
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'

const store = useStore()
const route = useRoute()
const router = useRouter()
const $q = useQuasar()

const configId = computed(() => route.params.id as string)
const loading = ref(true)
const saving = ref(false)
const executing = ref(false)
const showInfo = ref(false)
const tab = ref('steps')
const newParamName = ref('')
const promptInputDrafts = ref<Record<string, string>>({})
const apiToolCallBodyDrafts = ref<Record<number, string>>({})
const executeInput = ref<Record<string, string>>({})
const executeResult = ref<Record<string, any> | null>(null)

const config = ref<any>(null)

const promptInputKey = (stepIdx: number, promptIdx: number) => `${stepIdx}-${promptIdx}`

const name = computed({
  get: () => config.value?.name ?? '',
  set: (v: string) => {
    if (config.value) config.value.name = v
  },
})

const description = computed({
  get: () => config.value?.description ?? '',
  set: (v: string) => {
    if (config.value) config.value.description = v
  },
})

const system_name = computed({
  get: () => config.value?.system_name ?? '',
  set: (v: string) => {
    if (config.value) config.value.system_name = v
  },
})

const stepsList = computed(() => {
  const stepsData = config.value?.config?.steps
  if (!Array.isArray(stepsData)) return []
  return stepsData.map((s: any) => {
    if (Array.isArray(s?.prompts)) {
      return { prompts: s.prompts.map((p: any) => ({
        prompt_template_id: p.prompt_template_id ?? '',
        input: p.input ?? null,
        output_key: p.output_key ?? null,
      })) }
    }
    if (Array.isArray(s?.prompt_template_ids)) {
      return {
        prompts: s.prompt_template_ids.map((id: string) => ({
          prompt_template_id: id,
          input: null,
          output_key: null,
        })),
      }
    }
    return { prompts: [] }
  })
})

const getPromptTemplateBySystemName = (systemName: string) => {
  return promptTemplates.value.find((p: any) => p.system_name === systemName)
}

const getPromptTemplateText = (systemName: string): string => {
  const prompt = getPromptTemplateBySystemName(systemName)
  if (!prompt?.variants?.length) return ''
  const activeVariant = prompt.active_variant
  const variant = prompt.variants.find((v: any) => v.variant === activeVariant) || prompt.variants[0]
  return variant?.text ?? ''
}

const getPromptPlaceholderKeys = (stepIdx: number, promptIdx: number): string[] => {
  const prompt = config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]
  const templateId = prompt?.prompt_template_id
  if (!templateId) return []
  const text = getPromptTemplateText(templateId)
  const keys = [...new Set((text.match(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g) || []).map((m) => m.slice(1, -1)))]
  return keys
}

const getPromptInputValue = (stepIdx: number, promptIdx: number, key: string) => {
  const prompt = config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]
  if (!prompt?.input || typeof prompt.input !== 'object') return ''
  const val = prompt.input[key]
  return val != null ? String(val) : ''
}

const updatePromptInputValue = (stepIdx: number, promptIdx: number, key: string, val: string) => {
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

const getPromptInputText = (stepIdx: number, promptIdx: number) => {
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

const setPromptInputDraft = (stepIdx: number, promptIdx: number, val: string) => {
  promptInputDrafts.value[promptInputKey(stepIdx, promptIdx)] = val ?? ''
}

const commitPromptInput = (stepIdx: number, promptIdx: number) => {
  const key = promptInputKey(stepIdx, promptIdx)
  const val = promptInputDrafts.value[key]
  delete promptInputDrafts.value[key]
  const trimmed = val?.trim()
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  if (!trimmed) {
    config.value.config.steps[stepIdx].prompts[promptIdx].input = null
    return
  }
  try {
    config.value.config.steps[stepIdx].prompts[promptIdx].input = JSON.parse(trimmed)
  } catch {
    // Keep previous value on parse error
  }
}

const updatePromptTemplate = (stepIdx: number, promptIdx: number, val: string) => {
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  config.value.config.steps[stepIdx].prompts[promptIdx].prompt_template_id = val ?? ''
}

const updatePromptOutputKey = (stepIdx: number, promptIdx: number, val: string) => {
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  config.value.config.steps[stepIdx].prompts[promptIdx].output_key = val?.trim() || null
}

const ensurePrompts = (stepIdx: number) => {
  if (!config.value?.config?.steps?.[stepIdx]) return
  const step = config.value.config.steps[stepIdx]
  if (Array.isArray(step.prompt_template_ids) && !Array.isArray(step.prompts)) {
    step.prompts = step.prompt_template_ids.map((id: string) => ({
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

const addPrompt = (stepIdx: number) => {
  ensurePrompts(stepIdx)
  config.value.config.steps[stepIdx].prompts.push({
    prompt_template_id: '',
    input: null,
    output_key: null,
  })
}

const removePrompt = (stepIdx: number, promptIdx: number) => {
  if (!config.value?.config?.steps?.[stepIdx]?.prompts) return
  config.value.config.steps[stepIdx].prompts.splice(promptIdx, 1)
}

const promptTemplates = computed(() => {
  return store.getters['chroma/promptTemplates']?.items || []
})

const apiServers = computed(() => {
  return store.getters['chroma/api_servers']?.items || []
})

const getStepApiToolCall = (stepIdx: number) => {
  return config.value?.config?.steps?.[stepIdx]?.api_tool_call
}

const isStepApiToolCallEnabled = (stepIdx: number) => {
  return !!getStepApiToolCall(stepIdx)?.enabled
}

const setStepApiToolCallEnabled = (stepIdx: number, enabled: boolean) => {
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

const updateStepApiToolCall = (stepIdx: number, field: string, value: string) => {
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

const getStepApiToolTools = (stepIdx: number) => {
  const serverName = getStepApiToolCall(stepIdx)?.api_server
  if (!serverName) return []
  const server = apiServers.value.find((s: any) => s.system_name === serverName)
  return (server?.tools || []).map((t: any) => ({ label: t.name, value: t.system_name }))
}

const getStepApiToolCallBody = (stepIdx: number) => {
  if (apiToolCallBodyDrafts.value[stepIdx] !== undefined) return apiToolCallBodyDrafts.value[stepIdx]
  const body = getStepApiToolCall(stepIdx)?.body
  return body ?? ''
}

const setStepApiToolCallBodyDraft = (stepIdx: number, val: string) => {
  apiToolCallBodyDrafts.value[stepIdx] = val ?? ''
}

const commitStepApiToolCallBody = (stepIdx: number) => {
  const val = apiToolCallBodyDrafts.value[stepIdx]
  delete apiToolCallBodyDrafts.value[stepIdx]
  ensureStep(stepIdx)
  const step = config.value?.config?.steps?.[stepIdx]
  if (!step?.api_tool_call) return
  step.api_tool_call.body = val?.trim() ?? ''
}

const ensureStep = (stepIdx: number) => {
  if (!config.value?.config?.steps?.[stepIdx]) return
}

const promptTemplateOptions = computed(() => {
  return promptTemplates.value.map((p: any) => ({
    name: p.name,
    system_name: p.system_name,
  }))
})

const allOutputKeys = computed(() => {
  const seen = new Set<string>()
  const bindings: string[] = []
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

const getStepAvailableInputs = (stepIdx: number): string[] => {
  const seen = new Set<string>()
  const bindings: string[] = []
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
  const params = new Set<string>()
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

const isManuallyAddedParam = (param: string) => {
  const manual = config.value?.config?.expected_input
  if (!Array.isArray(manual)) return false
  return manual.some((p: string) => String(p).trim() === param)
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

const removeExpectedInputParam = (param: string) => {
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

const removeStep = (idx: number) => {
  if (!config.value?.config?.steps) return
  config.value.config.steps.splice(idx, 1)
}

const migrateLegacySteps = () => {
  const steps = config.value?.config?.steps
  if (!Array.isArray(steps)) return
  steps.forEach((step: any) => {
    if (Array.isArray(step.prompt_template_ids) && !Array.isArray(step.prompts)) {
      step.prompts = step.prompt_template_ids.map((id: string) => ({
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

const execute = async () => {
  if (!configId.value) return
  executing.value = true
  executeResult.value = null
  try {
    const input: Record<string, string> = {}
    for (const param of (expectedInputParams.value || [])) {
      const val = executeInput.value[param]
      if (val != null && val !== '') input[param] = String(val)
    }
    const result = await store.dispatch('executePromptQueue', {
      configId: configId.value,
      input,
    })
    executeResult.value = result
    $q.notify({
      position: 'top',
      message: 'Execution completed',
      color: 'positive',
      timeout: 1000,
    })
  } catch (error: any) {
    $q.notify({
      position: 'top',
      message: error?.message || 'Execution failed',
      color: 'negative',
      timeout: 2000,
    })
    executeResult.value = { error: error?.message || 'Execution failed' }
  } finally {
    executing.value = false
  }
}

const save = async () => {
  saving.value = true
  try {
    await store.dispatch('updatePromptQueueConfig', {
      configId: configId.value,
      updates: {
        name: config.value?.name,
        description: config.value?.description,
        system_name: config.value?.system_name,
        config: config.value?.config,
      },
    })
    $q.notify({
      position: 'top',
      message: 'Prompt Queue Config saved',
      color: 'positive',
      timeout: 1000,
    })
  } catch (error: any) {
    $q.notify({
      position: 'top',
      message: error?.message || 'Failed to save',
      color: 'negative',
      timeout: 2000,
    })
  } finally {
    saving.value = false
  }
}

const loadConfig = () => {
  const configs = store.getters.promptQueueConfigs
  if (!Array.isArray(configs)) return
  const found = configs.find((c: any) => c.id === configId.value)
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
  let cfg = store.getters.promptQueueConfigs?.find((c: any) => c.id === configId.value)
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
