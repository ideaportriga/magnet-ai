<template>
  <div v-if="loading" class="cluster overflow-hidden full-height prompt-queue-details__viewport" data-wrap="no">
    <km-inner-loading :showing="loading" />
  </div>
  <layouts-details-layout v-else :name="name" :description="description" :system-name="system_name" class="mx-auto" :content-container-style="{ maxWidth: &quot;1200px&quot;, minWidth: &quot;600px&quot;, margin: &quot;0 auto&quot; }" :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn :label="m.common_execute()" flat icon="play" icon-size="16px" @click="pqStore.executeDrawerOpen = true" />
      <km-btn v-if="canEdit" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving" @click="save" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="prompt-queue-readonly-icon" />
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabs" class="bb-border full-width" narrow-indicator dense align="left" no-caps />
      <div :inert="recordReadonly" :class="recordReadonly ? 'prompt-queue-details__readonly-zone' : null" class="stack full-height full-width overflow-auto mb-sm mt-sm min-h-0" data-gap="sm">
        <template v-if="tab === &quot;steps&quot;">
          <div class="full-width">
            <div class="cluster mb-sm" data-justify="between">
              <div class="km-heading-6">Steps</div>
              <km-btn :label="m.common_addStep()" icon="add" @click="addStep" />
            </div>
            <div class="gap-sm">
              <template v-for="(step, stepIdx) in stepsList" :key="stepIdx">
                <div class="ba-border border-radius-8 p-sm mb-sm">
                  <div class="cluster mb-sm" data-justify="between">
                    <div class="km-field text-secondary-text">Step {{ stepIdx + 1 }}</div>
                    <km-btn icon="delete" flat dense tone="danger" @click="removeStep(stepIdx)" />
                  </div>
                  <div v-if="getStepAvailableInputs(stepIdx).length" class="cluster mb-sm" data-gap="xs">
                    <div class="km-description text-secondary-text flex-none">Available:</div>
                    <div class="cluster" data-gap="xs">
                      <km-chip v-for="binding in getStepAvailableInputs(stepIdx)" :key="binding" dense size="sm" tone="brand">{{ binding }}</km-chip>
                    </div>
                  </div>
                  <div class="prompt-queue-details__prompt-grid">
                    <div v-for="(prompt, promptIdx) in (step.prompts || [])" :key="promptIdx">
                      <div class="ba-border border-radius-8 p-sm mb-xs">
                        <div class="cluster mb-xs" data-justify="between">
                          <div class="km-field text-secondary-text">Prompt {{ promptIdx + 1 }}</div>
                          <km-btn icon="delete" flat dense tone="danger" size="sm" @click="removePrompt(stepIdx, promptIdx)" />
                        </div>
                        <div class="km-field text-secondary-text pb-xs mb-xs">Template</div>
                        <km-select :model-value="prompt.prompt_template_id" :options="promptTemplateOptions || []" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" :placeholder="m.promptQueue_selectPromptTemplate()" @update:model-value="(val) =&gt; updatePromptTemplate(stepIdx, promptIdx, val)" />
                        <div class="km-field text-secondary-text pb-xs mt-sm">
                          <div class="cluster">
                            <span>Input</span>
                            <km-btn v-if="getPromptPlaceholderKeys(stepIdx, promptIdx).length" class="ml-xs" flat dense size="sm" :label="getPromptInputMode(stepIdx, promptIdx) === &quot;json&quot; ? &quot;Fields&quot; : &quot;JSON&quot;" @click="setPromptInputMode(stepIdx, promptIdx, getPromptInputMode(stepIdx, promptIdx) === &quot;json&quot; ? &quot;keyed&quot; : &quot;json&quot;)" />
                          </div>
                        </div>
                        <template v-if="getPromptInputMode(stepIdx, promptIdx) === &quot;keyed&quot; &amp;&amp; getPromptPlaceholderKeys(stepIdx, promptIdx).length">
                          <div v-for="key in getPromptPlaceholderKeys(stepIdx, promptIdx)" :key="key" class="cluster" data-gap="sm">
                            <div class="flex-none km-description">{{ key }}</div>
                            <div class="flex-1">
                              <km-input :label="`{${key}}`" :model-value="getPromptInputValue(stepIdx, promptIdx, key)" :placeholder="m.promptQueue_exampleInputTaskPath()" @update:model-value="(v) =&gt; updatePromptInputValue(stepIdx, promptIdx, key, v)" />
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <div v-if="getPromptPlaceholderKeys(stepIdx, promptIdx).length" class="km-field text-secondary-text pb-xs">Input (JSON)</div>
                          <km-input :model-value="getPromptInputText(stepIdx, promptIdx)" type="textarea" rows="3" :placeholder="m.promptQueue_exampleMappingOrPath()" @update:model-value="(v) =&gt; setPromptInputDraft(stepIdx, promptIdx, v)" @blur="commitPromptInput(stepIdx, promptIdx)" />
                          <div class="km-description text-secondary-text">Variable name → value or path (input.task, result.data). Plain string for single placeholder.</div>
                        </template>
                        <div class="km-field text-secondary-text pb-xs mt-sm">Output key</div>
                        <km-input :placeholder="m.promptQueue_exampleData()" :model-value="prompt.output_key ?? &quot;&quot;" @update:model-value="(v) =&gt; updatePromptOutputKey(stepIdx, promptIdx, v)" />
                        <div class="km-description text-secondary-text">Store as result.{output_key} (e.g. result.data)</div>
                      </div>
                    </div>
                  </div>
                  <div class="cluster mt-sm">
                    <km-btn :label="m.common_addPrompt()" icon="add" flat dense @click="addPrompt(stepIdx)" />
                  </div>
                  <template v-if="false">
                    <div class="cluster mb-sm mt-sm">
                      <km-checkbox :model-value="isStepApiToolCallEnabled(stepIdx)" :label="m.promptQueue_apiToolCall()" @update:model-value="(v) =&gt; setStepApiToolCallEnabled(stepIdx, v)" />
                    </div>
                    <div v-if="isStepApiToolCallEnabled(stepIdx)" class="ba-border border-radius-8 p-sm mb-sm">
                      <div class="km-field text-secondary-text pb-xs mb-xs">API Server</div>
                      <km-select :model-value="getStepApiToolCall(stepIdx)?.api_server ?? &quot;&quot;" :options="apiServers || []" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" :placeholder="m.promptQueue_selectApiServer()" @update:model-value="(v) =&gt; updateStepApiToolCall(stepIdx, &quot;api_server&quot;, v)" />
                      <div class="km-field text-secondary-text pb-xs mt-sm">API Tool</div>
                      <km-select :model-value="getStepApiToolCall(stepIdx)?.api_tool ?? &quot;&quot;" :options="getStepApiToolTools(stepIdx) || []" option-label="label" option-value="value" emit-value map-options has-dropdown-search height="30px" :placeholder="m.promptQueue_selectApiTool()" @update:model-value="(v) =&gt; updateStepApiToolCall(stepIdx, &quot;api_tool&quot;, v)" />
                      <div class="km-field text-secondary-text pb-xs mt-sm">Body (JSON)</div>
                      <km-input :model-value="getStepApiToolCallBody(stepIdx)" type="textarea" rows="4" :placeholder="m.promptQueue_exampleKeyMapping()" @update:model-value="(v) =&gt; setStepApiToolCallBodyDraft(stepIdx, v)" @blur="commitStepApiToolCallBody(stepIdx)" />
                      <div class="km-field text-secondary-text pb-xs mt-sm">Output key</div>
                      <km-input :placeholder="m.promptQueue_exampleApiResult()" :model-value="getStepApiToolCall(stepIdx)?.output_key ?? &quot;&quot;" @update:model-value="(v) =&gt; updateStepApiToolCall(stepIdx, &quot;output_key&quot;, v)" />
                      <div class="km-description text-secondary-text">Store as result.{output_key} (e.g. result.api_result)</div>
                    </div>
                  </template>
                </div>
                <div v-if="stepIdx &lt; stepsList.length - 1" class="cluster py-xs" data-justify="center">
                  <km-glyph name="arrow_downward" size="24px" tone="muted" />
                </div>
              </template>
            </div>
            <div v-if="stepsList.length &amp;&amp; allOutputKeys.length" class="ba-border border-radius-8 p-sm mt-sm">
              <div class="km-field text-secondary-text mb-sm">Available outputs</div>
              <div class="cluster" data-gap="xs">
                <km-chip v-for="binding in allOutputKeys" :key="binding" dense size="sm" tone="brand">{{ binding }}</km-chip>
              </div>
            </div>
          </div>
        </template>
        <template v-if="tab === &quot;expected_input&quot;">
          <div class="full-width">
            <div class="km-heading-6 mb-sm">Expected input parameters</div>
            <div class="km-description text-secondary-text mb-sm">Parameters to provide when running this queue</div>
            <div class="cluster mb-sm" data-gap="sm">
              <km-input :model-value="newParamName" :placeholder="m.promptQueue_exampleTaskQuery()" class="prompt-queue-details__input-200" @update:model-value="newParamName = $event" @keydown.enter.prevent="addExpectedInputParam" />
              <km-btn :label="m.common_add()" icon="add" flat dense @click="addExpectedInputParam" />
            </div>
            <div class="cluster" data-gap="sm">
              <km-chip v-for="param in expectedInputParams" :key="param" dense :tone="isManuallyAddedParam(param) ? &quot;brand&quot; : &quot;neutral&quot;" removable @remove="removeExpectedInputParam(param)">{{ param }}</km-chip>
            </div>
            <div v-if="!expectedInputParams.length &amp;&amp; !newParamName" class="mt-sm">
              <div class="km-description text-secondary-text">No input parameters. Add above or reference input.task, input.query in prompts.</div>
            </div>
          </div>
        </template>
        <template v-if="tab === &quot;test_inputs&quot;">
          <div class="full-width">
            <div class="km-heading-6 mb-sm">Test Inputs</div>
            <div class="km-description text-secondary-text mb-sm">Save input value sets to quickly load them in the Execute drawer</div>
            <div class="cluster mb-sm" data-gap="sm">
              <km-input :model-value="newTestInputName" :placeholder="m.promptQueue_testName()" class="prompt-queue-details__input-200" @update:model-value="newTestInputName = $event" @keydown.enter.prevent="addTestInput" />
              <km-btn :label="m.common_add()" icon="add" flat dense @click="addTestInput" />
            </div>
            <div class="gap-sm">
              <div v-for="(ti, tiIdx) in testInputsList" :key="tiIdx" class="ba-border border-radius-8 p-sm mb-sm">
                <div class="cluster mb-sm" data-justify="between">
                  <div class="km-field text-secondary-text">{{ ti.name }}</div>
                  <km-btn icon="delete" flat dense tone="danger" size="sm" @click="removeTestInput(tiIdx)" />
                </div>
                <div v-for="param in expectedInputParams" :key="param" class="cluster" data-gap="sm">
                  <div class="flex-none km-description prompt-queue-details__param-label">{{ param }}</div>
                  <div class="flex-1">
                    <km-input :model-value="getTestInputValue(tiIdx, param)" :placeholder="m.common_value()" class="prompt-queue-details__input-300" @update:model-value="(v) =&gt; setTestInputValue(tiIdx, param, v)" />
                  </div>
                </div>
              </div>
            </div>
            <div v-if="!testInputsList.length" class="mt-sm">
              <div class="km-description text-secondary-text">No test inputs. Add above. Define expected input params in Expected input tab first.</div>
            </div>
          </div>
        </template>
      </div>
    </template>
    <template #drawer>
      <prompt-queue-execute-drawer v-if="executeDrawerOpen" :open="executeDrawerOpen" :config-id="configId" :expected-input-params="expectedInputParams || []" :test-inputs="testInputsList" @update:open="(v) =&gt; pqStore.executeDrawerOpen = v" />
    </template>
  </layouts-details-layout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePermissions } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { usePromptQueueStore } from '@/stores/promptQueueStore'
import { useNotify } from '@/composables/useNotify'
import { m } from '@/paraglide/messages'

const pqStore = usePromptQueueStore()
const route = useRoute()
const { notifySuccess, notifyError } = useNotify()
const queries = useEntityQueries()
const { can } = usePermissions()

const { data: promptTemplatesListData } = queries.promptTemplates.useList()
const { data: apiServersListData } = queries.api_servers.useList()

const configId = computed(() => route.params.id)
const loading = ref(true)
const saving = ref(false)
const executeDrawerOpen = computed(() => pqStore.executeDrawerOpen ?? false)
const tab = ref('steps')
const tabs = ref([
  { value: 'steps', label: m.common_steps() },
  { value: 'expected_input', label: m.common_expectedInput() },
  { value: 'test_inputs', label: m.common_testInputs() },
])
const newParamName = ref('')
const newTestInputName = ref('')
const promptInputDrafts = ref({})
const promptInputMode = ref({})
const apiToolCallBodyDrafts = ref({})

const config = ref(null)
const canEdit = computed(() => can('write:prompt_queue'))
const recordReadonly = computed(() => !canEdit.value)

const promptInputKey = (stepIdx, promptIdx) => `${stepIdx}-${promptIdx}`

const getPromptInputMode = (stepIdx, promptIdx) => {
  const key = promptInputKey(stepIdx, promptIdx)
  if (promptInputMode.value[key]) return promptInputMode.value[key]
  return getPromptPlaceholderKeys(stepIdx, promptIdx).length ? 'keyed' : 'json'
}

const setPromptInputMode = (stepIdx, promptIdx, mode) => {
  if (recordReadonly.value) return
  const key = promptInputKey(stepIdx, promptIdx)
  if (mode === 'keyed') delete promptInputDrafts.value[key]
  promptInputMode.value[key] = mode
}

const name = computed({
  get: () => config.value?.name ?? '',
  set: (v) => {
    if (recordReadonly.value) return
    if (config.value) config.value.name = v
  },
})

const description = computed({
  get: () => config.value?.description ?? '',
  set: (v) => {
    if (recordReadonly.value) return
    if (config.value) config.value.description = v
  },
})

const system_name = computed({
  get: () => config.value?.system_name ?? '',
  set: (v) => {
    if (recordReadonly.value) return
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
  if (recordReadonly.value) return
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
    return typeof prompt.input === 'string'
      ? prompt.input
      : JSON.stringify(prompt.input, null, 2)
  } catch {
    return ''
  }
}

const setPromptInputDraft = (stepIdx, promptIdx, val) => {
  if (recordReadonly.value) return
  promptInputDrafts.value[promptInputKey(stepIdx, promptIdx)] = val ?? ''
}

const commitPromptInput = (stepIdx, promptIdx) => {
  if (recordReadonly.value) return
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
      } else {
        delete promptInputDrafts.value[key]
        config.value.config.steps[stepIdx].prompts[promptIdx].input = parsed
      }
    }
  } catch {
    const keys = getPromptPlaceholderKeys(stepIdx, promptIdx)
    if (keys.length === 1 && (trimmed.startsWith('input.') || trimmed.startsWith('result.'))) {
      delete promptInputDrafts.value[key]
      config.value.config.steps[stepIdx].prompts[promptIdx].input = { [keys[0]]: trimmed }
    } else {
      delete promptInputDrafts.value[key]
      config.value.config.steps[stepIdx].prompts[promptIdx].input = trimmed
    }
  }
}

const updatePromptTemplate = (stepIdx, promptIdx, val) => {
  if (recordReadonly.value) return
  ensurePrompts(stepIdx)
  if (!config.value?.config?.steps?.[stepIdx]?.prompts?.[promptIdx]) return
  config.value.config.steps[stepIdx].prompts[promptIdx].prompt_template_id = val ?? ''
}

const updatePromptOutputKey = (stepIdx, promptIdx, val) => {
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
  ensurePrompts(stepIdx)
  config.value.config.steps[stepIdx].prompts.push({
    prompt_template_id: '',
    input: null,
    output_key: null,
  })
}

const removePrompt = (stepIdx, promptIdx) => {
  if (recordReadonly.value) return
  if (!config.value?.config?.steps?.[stepIdx]?.prompts) return
  config.value.config.steps[stepIdx].prompts.splice(promptIdx, 1)
}

const promptTemplates = computed(() => promptTemplatesListData.value?.items || [])

const apiServers = computed(() => apiServersListData.value?.items || [])

const getStepApiToolCall = (stepIdx) => {
  return config.value?.config?.steps?.[stepIdx]?.api_tool_call
}

const isStepApiToolCallEnabled = (stepIdx) => {
  return !!getStepApiToolCall(stepIdx)?.enabled
}

const setStepApiToolCallEnabled = (stepIdx, enabled) => {
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
  apiToolCallBodyDrafts.value[stepIdx] = val ?? ''
}

const commitStepApiToolCallBody = (stepIdx) => {
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
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
  if (recordReadonly.value) return
  if (!config.value) config.value = { config: {} }
  if (!config.value.config) config.value.config = {}
  if (!Array.isArray(config.value.config.steps)) config.value.config.steps = []
  config.value.config.steps.push({ prompts: [] })
}

const removeStep = (idx) => {
  if (recordReadonly.value) return
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

const save = async () => {
  if (recordReadonly.value) return
  const cfg = config.value
  if (!cfg || !configId.value) return

  saving.value = true
  try {
    await pqStore.updatePromptQueueConfig({
      configId: configId.value,
      updates: {
        name: cfg.name,
        description: cfg.description,
        system_name: cfg.system_name,
        config: cfg.config,
      },
    })
    notifySuccess('Prompt Queue Config saved')
  } catch (error) {
    notifyError(error?.message || 'Failed to save')
  } finally {
    saving.value = false
  }
}

const loadConfig = () => {
  const configs = pqStore.promptQueueConfigs
  if (!Array.isArray(configs)) return
  const found = configs.find((c) => c.id === configId.value)
  if (found) {
    config.value = JSON.parse(JSON.stringify(found))
    migrateLegacySteps()
  }
}

onMounted(async () => {
  await pqStore.fetchPromptQueueConfigs(true)
  let cfg = pqStore.promptQueueConfigs?.find((c) => c.id === configId.value)
  if (!cfg) {
    cfg = await pqStore.fetchPromptQueueConfigById(configId.value)
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

watch(() => pqStore.promptQueueConfigs, () => {
  if (!config.value && configId.value) loadConfig()
}, { deep: true })

watch(config, (val) => {
  if (val && configId.value) {
    pqStore.selectedPromptQueueConfig = JSON.parse(JSON.stringify(val))
  }
}, { deep: true })
</script>

<style scoped>
.ba-border {
  border-color: rgba(0,0,0,0.24) !important;
}
.bb-border {
  border-block-end-color: rgba(0,0,0,0.24) !important;
}

.prompt-queue-details__prompt-grid {
  display: grid;
  gap: var(--ds-space-sm);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 767px) {
  .prompt-queue-details__prompt-grid {
    grid-template-columns: 1fr;
  }
}

.prompt-queue-details__viewport {
  min-inline-size: 1200px;
}

.prompt-queue-details__input-200 {
  max-inline-size: 200px;
}

.prompt-queue-details__input-300 {
  max-inline-size: 300px;
}

.prompt-queue-details__param-label {
  min-inline-size: 100px;
}

.prompt-queue-details__readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}

.prompt-queue-details__readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>
