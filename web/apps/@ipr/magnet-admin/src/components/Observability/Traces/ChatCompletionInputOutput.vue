<template>
  <div class="column q-gap-32">
    <section class="column q-gap-12">
      <header class="section-header">
        <span class="section-title">Messages</span>
        <span class="section-meta">{{ messages.length }}</span>
      </header>
      <div class="column q-gap-8">
        <div v-for="(message, msgIdx) in messages" :key="msgIdx" class="col-auto ba-border border-radius-8 overflow-hidden">
          <div class="row q-pa-sm bg-light justify-between items-center cursor-pointer" style="font-size: 13px" @click="toggleCollapse(msgIdx)">
            <span class="message-label">{{ message?.label }}</span>
            <q-icon :name="collapsed[msgIdx] ? 'expand_less' : 'expand_more'" size="16px" />
          </div>
          <div v-if="collapsed[msgIdx]" class="row bt-border">
            <template v-if="message?.type === 'text'">
              <div class="row q-pa-sm" style="min-height: 30px; font-size: 13px; white-space: pre-wrap; word-break: break-all">
                {{ message?.content }}
              </div>
            </template>
            <template v-else-if="message?.type === 'tools'">
              <ToolCallDisplay :tool-calls="message?.content" />
            </template>
          </div>
        </div>
      </div>
    </section>
    <section v-if="span?.request || span?.response" class="column q-gap-12">
      <header class="section-header">
        <span class="section-title">Raw Payloads</span>
      </header>
      <div class="column q-gap-8">
        <div v-for="(payload, pIdx) in payloads" :key="payload.key" class="col-auto ba-border border-radius-8 overflow-hidden">
          <div class="row q-pa-sm bg-light justify-between items-center cursor-pointer" style="font-size: 13px" @click="togglePayload(pIdx)">
            <span class="message-label">{{ payload.label }}</span>
            <q-icon :name="payloadCollapsed[pIdx] ? 'expand_less' : 'expand_more'" size="16px" />
          </div>
          <div v-if="payloadCollapsed[pIdx]" class="row bt-border full-width">
            <pre class="json-payload" v-html="payload.html" />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import ToolCallDisplay from './ToolCallDisplay.vue'
import { highlightJson, prettyJson } from './jsonHighlight'

type ToolFunction = {
  name?: string
  arguments?: string
  [key: string]: unknown
}
type ToolCall = {
  function: ToolFunction
  [key: string]: unknown
}

type Message = {
  role?: string
  label?: string
  content?: string | ToolCall[]
  tool_calls?: ToolCall[]
  type?: string
  [key: string]: unknown
}

type Span = {
  input?: Message[]
  output?: Message | string
  request?: Record<string, unknown>
  response?: Record<string, unknown>
  [key: string]: unknown
}

const props = defineProps<{
  span: Span | null
}>()

const collapsed = ref<boolean[]>([])
const payloadCollapsed = ref<boolean[]>([])

const ROLE_LABELS: Record<string, string> = {
  system: 'System Message',
  user: 'User Message',
  assistant: 'Assistant Message',
  tool: 'Call Results',
}

function labelForRole(role?: string): string {
  if (!role) return ''
  return ROLE_LABELS[role] ?? role.charAt(0).toUpperCase() + role.slice(1)
}

const getOutputMessage = () => {
  // Maintain backward compatibility, when output is a string
  if (typeof props.span?.output === 'string') {
    return { role: 'assistant', label: 'Assistant Message', content: props.span?.output ?? '' }
  }
  return { ...(props.span?.output ?? {}), role: 'assistant', label: 'Assistant Message' }
}

// Format message
function formatMessage(message: any): any {
  if (message?.role === 'assistant' && message?.tool_calls) {
    return { type: 'tools', label: 'Tool Calls', content: message.tool_calls }
  } else if (message?.role === 'tool') {
    return { type: 'text', label: 'Call Results', content: message.content }
  } else if (message?.content) {
    return { type: 'text', label: message.label ?? labelForRole(message.role), content: message.content }
  }
  return ''
}

const messages = computed(() => {
  const inputMessages = props.span?.input ?? []
  const outputMessage = getOutputMessage()
  return [...inputMessages, outputMessage].map(formatMessage)
})

const payloads = computed(() => {
  const list: { key: string; label: string; html: string }[] = []
  if (props.span?.request) {
    list.push({ key: 'request', label: 'Request', html: highlightJson(prettyJson(props.span.request)) })
  }
  if (props.span?.response) {
    list.push({ key: 'response', label: 'Response', html: highlightJson(prettyJson(props.span.response)) })
  }
  return list
})

function toggleCollapse(index: number) {
  collapsed.value[index] = !collapsed.value[index]
}

function togglePayload(index: number) {
  payloadCollapsed.value[index] = !payloadCollapsed.value[index]
}

// Reset collapsed on span change
watch(
  () => props.span,
  () => {
    collapsed.value = []
    payloadCollapsed.value = []
  },
  { immediate: true }
)
</script>

<style>
.json-payload .key {
  color: #d63384;
  font-weight: 500;
}
.json-payload .string {
  color: #0a8754;
}
.json-payload .number {
  color: #0d6efd;
  font-weight: 500;
}
.json-payload .boolean {
  color: #e35d00;
  font-weight: 600;
}
.json-payload .null {
  color: #e35d00;
  font-style: italic;
  font-weight: 600;
}
.json-payload .punctuation {
  color: #6c757d;
}
</style>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e1e4e8;
}
.section-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #6e7681;
}
.section-meta {
  font-size: 11px;
  font-weight: 500;
  color: #8c959f;
  background-color: #f1f3f5;
  border-radius: 999px;
  padding: 1px 8px;
  line-height: 1.4;
}
.message-label {
  font-weight: 500;
  color: #24292f;
}
.json-payload {
  margin: 0;
  padding: 12px;
  width: 100%;
  font-size: 13px;
  font-family:
    'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Cascadia Mono', 'Segoe UI Mono', 'Liberation Mono', Menlo, Monaco, Consolas, monospace;
  line-height: 1.5;
  color: #24292f;
  background-color: #ffffff;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
}
</style>
