<template lang="pug">
.column.q-gap-12
  .col-auto.ba-border.border-radius-8.overflow-hidden(v-for='(message, index) in messages')
    .row.q-pa-sm.bg-light.justify-between.items-center.cursor-pointer(style='font-size: 13px', @click='toggleCollapse(index)')
      span {{ formatRole(message?.label) }}
      q-icon(:name='collapsed[index] ? "expand_less" : "expand_more"', size='16px')
    .row.bt-border(v-if='collapsed[index]')
      template(v-if='message?.type == "text"')
        .row.q-pa-sm(style='min-height: 30px; font-size: 13px; white-space: pre-wrap; word-break: break-all') {{ message?.content }}
      template(v-else-if='message?.type == "tools"')
        .row.no-wrap(v-for='(toolCall, index) in message?.content')
          .row.q-pa-sm.bg-secondary.text-white.justify-center.items-center(
            style='width: 30px; font-size: 13px; font-family: Cascadia Mono, Segoe UI Mono, Liberation Mono, Menlo, Monaco, Consolas, monospace'
          ) {{ index + 1 }}
          .row.q-pa-sm.q-gap-4(
            style='min-height: 30px; font-size: 13px; font-family: Cascadia Mono, Segoe UI Mono, Liberation Mono, Menlo, Monaco, Consolas, monospace; white-space: pre-wrap; word-break: break-word'
          )
            span {{ toolCall.function.name }}
            span ({{ toolCall.function.arguments }})
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    span: {
      type: Object,
      default: () => null,
    },
  },
  setup() {
    const collapsed = ref([])
    return {
      collapsed,
    }
  },
  computed: {
    messages() {
      const formatMessage = (message) => {
        if (message?.content) {
          return { type: 'text', label: message.label ?? message.role, content: message.content }
        } else if (message?.tool_calls) {
          return { type: 'tools', label: 'Tool Calls', content: message.tool_calls }
        }
        return ''
      }
      const inputMessages = this.span?.input ?? []
      const outputMessage = this.getOutputMessage()
      return [...inputMessages, outputMessage].map(formatMessage)
    },
  },
  watch: {
    span: {
      handler() {
        this.collapsed = []
      },
    },
  },
  methods: {
    formatRole(value) {
      if (!value) return ''
      return value.charAt(0).toUpperCase() + value.slice(1)
    },
    getOutputMessage() {
      // Maintain backward compatibility, when output is a string
      if (typeof this.span?.output === 'string') {
        return { label: 'Generated Text', content: this.span?.output ?? '' }
      }
      return { ...this.span?.output, label: 'Generated Text' }
    },
    toggleCollapse(index) {
      this.collapsed[index] = !this.collapsed[index]
    },
  },
}
</script>
