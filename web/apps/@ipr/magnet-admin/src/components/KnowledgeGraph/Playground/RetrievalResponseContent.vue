<template>
  <div v-if="format === 'plain'" class="markdown-content markdown-content--plain">{{ content }}</div>
  <div v-else-if="format === 'html'" class="markdown-content" v-html="content" />
  <div v-else class="markdown-content" v-html="rendered" />
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    content: string
    format?: 'plain' | 'markdown' | 'html'
  }>(),
  {
    format: 'markdown',
  }
)

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
})

const rendered = computed(() => {
  if (!props.content) return ''
  return md.render(props.content)
})
</script>

<style scoped>
.markdown-content {
  font-size: 13px;
  line-height: 1.65;
  color: #374151;
  word-wrap: break-word;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.markdown-content--plain {
  white-space: pre-wrap;
}

.markdown-content :deep(p) {
  margin: 0 0 12px 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: #111827;
}

.markdown-content :deep(em) {
  font-style: italic;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-weight: 600;
  color: #111827;
  margin: 20px 0 8px 0;
  line-height: 1.4;
}

.markdown-content :deep(h1) {
  font-size: 1.25em;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 6px;
}

.markdown-content :deep(h2) {
  font-size: 1.125em;
}

.markdown-content :deep(h3) {
  font-size: 1em;
}

.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-size: 0.925em;
  color: #374151;
}

.markdown-content :deep(h1:first-child),
.markdown-content :deep(h2:first-child),
.markdown-content :deep(h3:first-child),
.markdown-content :deep(h4:first-child) {
  margin-top: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(li::marker) {
  color: inherit;
}

.markdown-content :deep(ul > li) {
  list-style-type: disc;
}

.markdown-content :deep(ul > ul > li) {
  list-style-type: circle;
}

.markdown-content :deep(ol > li) {
  list-style-type: decimal;
}

.markdown-content :deep(blockquote) {
  margin: 12px 0;
  padding: 10px 14px;
  background: #f9fafb;
  border-left: 3px solid #d1d5db;
  border-radius: 0 4px 4px 0;
  color: #6b7280;
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

.markdown-content :deep(blockquote blockquote) {
  margin: 8px 0 0 0;
  border-left-color: #e5e7eb;
}

.markdown-content :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
  font-size: 0.85em;
  color: #be185d;
}

.markdown-content :deep(pre) {
  margin: 12px 0;
  padding: 12px 14px;
  background: #1f2937;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: #e5e7eb;
  font-size: 0.8em;
  line-height: 1.5;
}

.markdown-content :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(hr) {
  border: none;
  height: 1px;
  background: #e5e7eb;
  margin: 16px 0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 0.9em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 8px 12px;
  text-align: left;
  border: 1px solid #e5e7eb;
}

.markdown-content :deep(th) {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.markdown-content :deep(tr:nth-child(even)) {
  background: #f9fafb;
}

.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: 6px;
  margin: 10px 0;
}
</style>
