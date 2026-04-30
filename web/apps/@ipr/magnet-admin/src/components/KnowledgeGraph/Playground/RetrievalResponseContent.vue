<template>
  <div v-if="format === 'plain'" class="markdown-content markdown-content--plain">{{ content }}</div>
  <div v-else class="markdown-content" v-html="rendered" />
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { m } from '@/paraglide/messages'
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
  font-size: var(--ds-font-size-label);
  line-height: 1.65;
  color: var(--ds-color-black);
  overflow-wrap: break-word;
  font-family: var(--ds-font-default), sans-serif;
}

.markdown-content--plain {
  white-space: pre-wrap;
}

.markdown-content :deep(p) {
  margin: 0 0 12px;
}

.markdown-content :deep(p:last-child) {
  margin-block-end: 0;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: var(--ds-color-primary-text);
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
  color: var(--ds-color-primary-text);
  margin: 20px 0 8px;
  line-height: 1.4;
}

.markdown-content :deep(h1) {
  font-size: 1.25em;
  border-block-end: 1px solid var(--ds-color-border);
  padding-block-end: 6px;
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
  color: var(--ds-color-black);
}

.markdown-content :deep(h1:first-child),
.markdown-content :deep(h2:first-child),
.markdown-content :deep(h3:first-child),
.markdown-content :deep(h4:first-child) {
  margin-block-start: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-inline-start: 20px;
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
  background: var(--ds-color-background);
  border-inline-start: 3px solid var(--ds-color-border-2);
  border-radius: 0 var(--ds-radius-sm) var(--ds-radius-sm) 0;
  color: var(--ds-color-label);
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

.markdown-content :deep(blockquote blockquote) {
  margin: 8px 0 0;
  border-inline-start-color: var(--ds-color-border);
}

.markdown-content :deep(code) {
  background: var(--ds-color-light);
  padding: 2px 6px;
  border-radius: var(--ds-radius-sm);
  font-family: var(--ds-font-mono);
  font-size: 0.85em;
  color: var(--ds-color-error);
}

.markdown-content :deep(pre) {
  margin: 12px 0;
  padding: 12px 14px;
  background: var(--ds-color-black);
  border-radius: var(--ds-radius-md);
  overflow-inline: auto;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: var(--ds-color-border);
  font-size: 0.8em;
  line-height: 1.5;
}

.markdown-content :deep(a) {
  color: var(--ds-color-primary);
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(hr) {
  border: none;
  block-size: 1px;
  background: var(--ds-color-border);
  margin: 16px 0;
}

.markdown-content :deep(table) {
  inline-size: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 0.9em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 8px 12px;
  text-align: start;
  border: 1px solid var(--ds-color-border);
}

.markdown-content :deep(th) {
  background: var(--ds-color-background);
  font-weight: 600;
  color: var(--ds-color-black);
}

.markdown-content :deep(tr:nth-child(even)) {
  background: var(--ds-color-background);
}

.markdown-content :deep(img) {
  max-inline-size: 100%;
  border-radius: var(--ds-radius-md);
  margin: 10px 0;
}
</style>
