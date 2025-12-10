<template>
  <div class="column q-gap-12">
    <div v-for="(message, msgIdx) in messages" :key="msgIdx" class="col-auto ba-border border-radius-8 overflow-hidden">
      <div class="row q-pa-sm bg-light justify-between items-center cursor-pointer" style="font-size: 13px" @click="toggleCollapse(msgIdx)">
        <span>{{ formatRole(message?.label) }}</span>
        <q-icon :name="collapsed[msgIdx] ? 'expand_less' : 'expand_more'" size="16px" />
      </div>
      <div v-if="collapsed[msgIdx]" class="row bt-border">
        <template v-if="message?.type === 'text'">
          <div class="row q-pa-sm" style="min-height: 30px; font-size: 13px; white-space: pre-wrap; word-break: break-all">
            {{ message?.content }}
          </div>
        </template>
        <template v-else-if="message?.type === 'tools'">
          <div
            v-for="(toolCall, toolIdx) in message?.content"
            :key="toolIdx"
            class="row no-wrap"
            style="
              font-size: 13px;
              font-family:
                Cascadia Mono,
                Segoe UI Mono,
                Liberation Mono,
                Menlo,
                Monaco,
                Consolas,
                monospace;
            "
          >
            <div class="row q-pa-sm bg-secondary text-white justify-center items-center" style="width: 30px">
              {{ toolIdx + 1 }}
            </div>
            <div class="row q-pa-sm q-gap-4" style="min-height: 30px; white-space: pre-wrap; word-break: break-word">
              <span>{{ toolCall.function?.name }}</span>
              <span>({{ toolCall.function?.arguments }})</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue'

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
  [key: string]: unknown
}

const props = defineProps<{
  span: Span | null
}>()

const collapsed = ref<boolean[]>([])

const getOutputMessage = () => {
  // Maintain backward compatibility, when output is a string
  if (typeof props.span?.output === 'string') {
    return { label: 'Generated Text', content: props.span?.output ?? '' }
  }
  return { ...(props.span?.output ?? {}), label: 'Generated Text' }
}

// Helper for role formatting
function formatRole(value?: string) {
  if (!value) return ''
  return value.charAt(0).toUpperCase() + value.slice(1)
}

// Format message
function formatMessage(message: any): any {
  if (message?.role === 'assistant' && message?.tool_calls) {
    return { type: 'tools', label: 'Tool Calls', content: message.tool_calls }
  } else if (message?.role === 'tool') {
    return { type: 'text', label: 'Call Results', content: message.content }
  } else if (message?.content) {
    return { type: 'text', label: message.label ?? message.role, content: message.content }
  }
  return ''
}

const messages = computed(() => {
  const inputMessages = props.span?.input ?? []
  const outputMessage = getOutputMessage()
  return [...inputMessages, outputMessage].map(formatMessage)
})

function toggleCollapse(index: number) {
  collapsed.value[index] = !collapsed.value[index]
}

// Reset collapsed on span change
watch(
  () => props.span,
  () => {
    collapsed.value = []
  },
  { immediate: true }
)
</script>
