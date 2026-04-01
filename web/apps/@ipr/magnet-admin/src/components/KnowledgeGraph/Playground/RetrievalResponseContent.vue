<template>
  <div v-if="format === 'plain'" class="markdown-content markdown-content--plain">{{ content }}</div>
  <div v-else class="markdown-content" v-html="rendered" />
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    content: string
    format?: 'plain' | 'markdown'
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
  font-size: var(--km-font-size-label);
  line-height: 1.65;
  color: var(--q-black);
  word-wrap: break-word;
  font-family: var(--km-font-default), sans-serif;
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
  color: var(--q-primary-text);
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
  color: var(--q-primary-text);
  margin: 20px 0 8px 0;
  line-height: 1.4;
}

.markdown-content :deep(h1) {
  font-size: 1.25em;
  border-bottom: 1px solid var(--q-border);
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
  color: var(--q-black);
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
  background: var(--q-background);
  border-left: 3px solid var(--q-border-2);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--q-label);
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

.markdown-content :deep(blockquote blockquote) {
  margin: 8px 0 0 0;
  border-left-color: var(--q-border);
}

.markdown-content :deep(code) {
  background: var(--q-light);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--km-font-mono);
  font-size: 0.85em;
  color: var(--q-error);
}

.markdown-content :deep(pre) {
  margin: 12px 0;
  padding: 12px 14px;
  background: var(--q-black);
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: var(--q-border);
  font-size: 0.8em;
  line-height: 1.5;
}

.markdown-content :deep(a) {
  color: var(--q-primary);
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(hr) {
  border: none;
  height: 1px;
  background: var(--q-border);
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
  border: 1px solid var(--q-border);
}

.markdown-content :deep(th) {
  background: var(--q-background);
  font-weight: 600;
  color: var(--q-black);
}

.markdown-content :deep(tr:nth-child(even)) {
  background: var(--q-background);
}

.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-md);
  margin: 10px 0;
}
</style>
