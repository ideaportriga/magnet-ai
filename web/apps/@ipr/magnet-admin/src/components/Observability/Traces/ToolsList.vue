<template>
  <div class="column q-gap-12">
    <div v-for="(toolCall, index) in tools" :key="getToolKey(toolCall, index)" class="col-auto ba-border border-radius-8 overflow-hidden">
      <div class="row q-pa-sm bg-light justify-between items-center cursor-pointer km-body-sm" @click="toggleExpand(index)">
        <span>{{ getFunctionName(toolCall) }}</span>
        <q-icon :name="expanded[index] ? 'expand_less' : 'expand_more'" size="16px" />
      </div>

      <div v-if="expanded[index]" class="column bt-border">
        <div v-if="getDescription(toolCall)" class="q-pa-sm text-grey-8 km-caption" style="white-space: pre-line">
          {{ getDescription(toolCall) }}
        </div>

        <div v-if="hasParameters(toolCall)" class="column bt-border">
          <div class="params-header km-tiny">Parameters</div>
          <div class="params-list">
            <div
              v-for="(param, paramIdx) in getParameters(toolCall)"
              :key="param.name"
              class="param-item"
              :class="{ 'param-item--bordered': paramIdx > 0 }"
            >
              <div class="row items-center q-gap-6" style="flex-wrap: wrap">
                <code class="param-name km-tiny">{{ param.name }}</code>
                <span class="param-type km-tiny">{{ param.type }}</span>
                <span v-if="param.required" class="param-required km-tiny">required</span>
                <span v-if="param.enum" class="param-enum km-tiny">enum</span>
              </div>
              <div v-if="param.description" class="param-description km-tiny">
                {{ param.description }}
              </div>
              <div v-if="param.enum" class="row q-gap-4" style="flex-wrap: wrap; margin-top: 4px">
                <code v-for="val in param.enum" :key="val" class="param-enum-value km-tiny">{{ val }}</code>
              </div>
              <div v-if="param.items" class="param-items-type km-tiny">
                items:
                <code>{{ param.items }}</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'

type ParameterProperty = {
  type?: string
  description?: string
  enum?: string[]
  items?: { type?: string }
  [key: string]: unknown
}

type ParametersSchema = {
  type?: string
  properties?: Record<string, ParameterProperty>
  required?: string[]
  [key: string]: unknown
}

type ToolFunction = {
  name?: string
  description?: string
  parameters?: ParametersSchema
}

type Tool = {
  id?: string
  type?: string
  function?: ToolFunction
  name?: string
  description?: string
  parameters?: ParametersSchema
  [key: string]: unknown
}

type ParsedParam = {
  name: string
  type: string
  description: string
  required: boolean
  enum?: string[]
  items?: string
}

const props = defineProps<{
  tools: Tool[]
}>()

const expanded = ref<boolean[]>(props.tools.map(() => false))

const toggleExpand = (index: number) => {
  expanded.value[index] = !expanded.value[index]
}

const getToolKey = (toolCall: Tool, index: number): string => {
  return toolCall.id ?? `${getFunctionName(toolCall)}-${index}`
}

const getFunctionName = (toolCall: Tool): string => {
  return toolCall.function?.name ?? toolCall.name ?? 'Unknown'
}

const getDescription = (toolCall: Tool): string => {
  return toolCall.function?.description ?? toolCall.description ?? ''
}

const getParametersSchema = (toolCall: Tool): ParametersSchema | undefined => {
  return toolCall.function?.parameters ?? toolCall.parameters
}

const hasParameters = (toolCall: Tool): boolean => {
  const schema = getParametersSchema(toolCall)
  return !!schema?.properties && Object.keys(schema.properties).length > 0
}

const formatType = (prop: ParameterProperty): string => {
  if (!prop.type) return 'any'
  if (prop.type === 'array' && prop.items?.type) return `${prop.items.type}[]`
  return prop.type
}

const getParameters = (toolCall: Tool): ParsedParam[] => {
  const schema = getParametersSchema(toolCall)
  if (!schema?.properties) return []

  const required = new Set(schema.required ?? [])

  return Object.entries(schema.properties).map(([name, prop]) => ({
    name,
    type: formatType(prop),
    description: prop.description ?? '',
    required: required.has(name),
    enum: prop.enum,
    items: prop.type === 'array' && prop.items?.type ? prop.items.type : undefined,
  }))
}
</script>

<style scoped>
.params-header {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--q-label);
  padding: 10px 12px 6px;
  background: var(--q-background);
}

.params-list {
  padding: 0 12px 10px;
  background: var(--q-background);
}

.param-item {
  padding: 8px 0;
}

.param-item--bordered {
  border-top: 1px solid var(--q-border);
}

.param-name,
.param-type,
.param-required,
.param-enum {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--radius-sm);
  line-height: 1;
}

.param-name {
  font-weight: 600;
  color: var(--q-black);
  background: var(--q-white);
  border: 1px solid var(--q-border);
}

.param-type {
  color: var(--q-primary);
  background: var(--q-primary-bg);
}

.param-required {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: var(--q-warning);
  background: var(--q-warning-bg);
}

.param-enum {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: var(--q-success-text);
  background: var(--q-success);
}

.param-description {
  line-height: 1.5;
  color: var(--q-secondary-text);
  margin-top: 4px;
}

.param-enum-value {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 6px;
  color: var(--q-success-text);
  background: var(--q-success);
  border-radius: var(--radius-sm);
}

.param-items-type {
  color: var(--q-icon);
  margin-top: 4px;
}

.param-items-type code {
  color: var(--q-primary);
}
</style>
