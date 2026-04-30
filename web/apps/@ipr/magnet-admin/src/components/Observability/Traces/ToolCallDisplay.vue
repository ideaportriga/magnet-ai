<template>
  <div class="stack full-width" data-gap="0">
    <div v-for="(toolCall, toolIdx) in toolCalls" :key="toolIdx" class="cluster no-wrap tool-call-row km-body-sm">
      <div class="tool-call-index km-caption">
        {{ toolIdx + 1 }}
      </div>
      <div class="tool-call-content">
        <div class="tool-call-line">
          <span class="function-name">{{ toolCall.function?.name }}</span>
          <span v-if="getArgLines(toolCall.function?.arguments).length" v-html="getArgLines(toolCall.function?.arguments)[0].html" />
        </div>
        <div
          v-for="(line, lineIdx) in getArgLines(toolCall.function?.arguments).slice(1)"
          :key="lineIdx"
          class="tool-call-line"
          :style="{ paddingLeft: line.indent + 'ch' }"
          v-html="line.html"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { m } from '@/paraglide/messages'
type ToolFunction = {
  name?: string
  arguments?: string
  [key: string]: unknown
}

type ToolCall = {
  function?: ToolFunction
  [key: string]: unknown
}

defineProps<{
  toolCalls: ToolCall[]
}>()

type ArgLine = { html: string; indent: number }

const argsCache = new Map<string, ArgLine[]>()

function getArgLines(args?: string): ArgLine[] {
  if (!args) return []
  const cached = argsCache.get(args)
  if (cached) return cached

  let lines: ArgLine[]
  try {
    const parsed = JSON.parse(args)
    const formatted = '(' + JSON.stringify(parsed, null, 2) + ')'
    lines = formatted.split('\n').map((line) => {
      const indent = line.search(/\S|$/)
      const trimmed = line.substring(indent)
      return { html: highlightJson(trimmed), indent }
    })
  } catch {
    lines = [{ html: args, indent: 0 }]
  }

  argsCache.set(args, lines)
  return lines
}

function highlightJson(json: string): string {
  if (!json) return ''
  // Escape HTML first
  const escaped = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  return escaped.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?|[\[\]\{\},])/g,
    (match) => {
      let cls = 'number'
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'key'
          // Separate key and colon
          // match ends with colon, potentially preceded by whitespace
          const colonIndex = match.lastIndexOf(':')
          const keyPart = match.substring(0, colonIndex)
          const colonPart = match.substring(colonIndex)
          return `<span class="${cls}">${keyPart}</span><span class="punctuation">${colonPart}</span>`
        } else {
          cls = 'string'
        }
      } else if (/true|false/.test(match)) {
        cls = 'boolean'
      } else if (/null/.test(match)) {
        cls = 'null'
      } else if (/[\[\]\{\},]/.test(match)) {
        cls = 'punctuation'
      }
      return `<span class="${cls}">${match}</span>`
    }
  )
}
</script>

<style>
/* Syntax Highlighting Colors - Vibrant Theme */
.tool-call-row .key {
  color: var(--ds-color-error);
  font-weight: 500;
}
.tool-call-row .string {
  color: var(--ds-color-success-text);
}
.tool-call-row .number {
  color: var(--ds-color-primary);
  font-weight: 500;
}
.tool-call-row .boolean {
  color: var(--ds-color-warning);
  font-weight: 600;
}
.tool-call-row .null {
  color: var(--ds-color-warning);
  font-style: italic;
  font-weight: 600;
}
.tool-call-row .punctuation {
  color: var(--ds-color-icon);
}
.tool-call-row .function-name {
  color: var(--ds-color-primary);
  font-weight: 700;
}
</style>

<style scoped>
.tool-call-row {
  font-family:
    'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Cascadia Mono', 'Segoe UI Mono', 'Liberation Mono', Menlo, Monaco, Consolas, monospace;
  border-block-end: 1px solid var(--ds-color-border);
  background-color: var(--ds-color-white);
}

.tool-call-row:last-child {
  border-block-end: none;
}

.tool-call-index {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 12px 8px;
  min-inline-size: 36px;
  background-color: var(--ds-color-light);
  color: var(--ds-color-icon);
  border-inline-end: 1px solid var(--ds-color-border);
  user-select: none;
}

.tool-call-content {
  flex: 1;
  padding: 12px;
  line-height: 1.5;
  color: var(--ds-color-black);
}

.tool-call-line {
  overflow-wrap: break-word;
}
</style>
