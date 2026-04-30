<script setup lang="ts">
/**
 * `<km-markdown>` — drop-in for the legacy Markdown component.
 *
 * Renders a markdown string through `markdown-it` with the same plugin
 * stack as before (abbr, anchor, footnote, highlight, sub/sup, task lists,
 * TOC). The only behavioural change is the styling: legacy used scoped
 * Stylus tied to `--km-font-size-*`; we use `--ds-*` tokens (which alias to
 * `--km-*` during the migration).
 */

import MarkdownIt from 'markdown-it'
import MarkdownItAbbr from 'markdown-it-abbr'
import MarkdownItAnchor from 'markdown-it-anchor'
import MarkdownItFootnote from 'markdown-it-footnote'
import MarkdownItHighlightjs from 'markdown-it-highlightjs'
import MarkdownItSub from 'markdown-it-sub'
import MarkdownItSup from 'markdown-it-sup'
import MarkdownItTasklists from 'markdown-it-task-lists'
import MarkdownItTOC from 'markdown-it-toc-done-right'
import { computed } from 'vue'

const md = new MarkdownIt()
  .use(MarkdownItAbbr)
  .use(MarkdownItAnchor)
  .use(MarkdownItFootnote)
  .use(MarkdownItHighlightjs)
  .use(MarkdownItSub)
  .use(MarkdownItSup)
  .use(MarkdownItTasklists)
  .use(MarkdownItTOC)

const defaultLinkRenderer =
  md.renderer.rules.link_open ||
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  if (token) {
    token.attrPush(['target', '_blank'])
    token.attrPush(['rel', 'noopener noreferrer'])
  }
  return defaultLinkRenderer(tokens, idx, options, env, self)
}

const props = defineProps<{
  source?: string
}>()

const cleaned = computed(() => {
  if (typeof props.source !== 'string') return ''
  return props.source.replace(/^```markdown\s*|```$/g, '')
})

const rendered = computed(() => md.render(cleaned.value))
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div class="km-markdown" data-test="km-markdown" v-html="rendered" />
</template>

<style>
.km-markdown {
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-black);
  line-height: var(--ds-line-height-normal);
}

.km-markdown :deep(p) {
  margin: 0 0 var(--ds-space-lg);
  white-space: pre-wrap;
}
.km-markdown :deep(h1),
.km-markdown :deep(h2),
.km-markdown :deep(h3),
.km-markdown :deep(h4),
.km-markdown :deep(h5),
.km-markdown :deep(h6) {
  font-family: var(--ds-font-default);
  font-weight: var(--ds-font-weight-semibold);
  margin: 0 0 var(--ds-space-md);
}
.km-markdown :deep(h1) { font-size: 22px; line-height: 1.2; }
.km-markdown :deep(h2) { font-size: var(--ds-font-size-h1); line-height: 1.2; }
.km-markdown :deep(h3) { font-size: var(--ds-font-size-h2); line-height: 1.3; }
.km-markdown :deep(h4) { font-size: var(--ds-font-size-body-lg); line-height: 1.3; }
.km-markdown :deep(h5) { font-size: var(--ds-font-size-body); line-height: 1.4; }
.km-markdown :deep(h6) { font-size: var(--ds-font-size-label); line-height: 1.4; }

.km-markdown :deep(a) {
  color: var(--ds-color-primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.km-markdown :deep(ul),
.km-markdown :deep(ol) {
  padding-inline-start: var(--ds-space-xl);
  margin: 0 0 var(--ds-space-lg);
}
.km-markdown :deep(li) { margin-block-end: var(--ds-space-xs); }

.km-markdown :deep(code) {
  background: var(--ds-color-light);
  padding: 2px var(--ds-space-2xs);
  border-radius: var(--ds-radius-xs);
  font-family: var(--ds-font-mono);
  font-size: 0.92em;
}

.km-markdown :deep(pre) {
  background: var(--ds-color-light);
  padding: var(--ds-space-md);
  border-radius: var(--ds-radius-md);
  overflow: auto;
  margin: 0 0 var(--ds-space-lg);
}
.km-markdown :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: var(--ds-font-size-caption);
}

.km-markdown :deep(blockquote) {
  margin: 0 0 var(--ds-space-lg);
  padding-inline-start: var(--ds-space-md);
  border-inline-start: 3px solid var(--ds-color-border-2);
  color: var(--ds-color-text-grey);
}

.km-markdown :deep(table) {
  border-collapse: collapse;
  margin: 0 0 var(--ds-space-lg);
  inline-size: 100%;
}
.km-markdown :deep(th),
.km-markdown :deep(td) {
  padding: var(--ds-space-xs) var(--ds-space-sm);
  border: 1px solid var(--ds-color-border);
  text-align: start;
}
.km-markdown :deep(th) {
  background: var(--ds-color-table-header);
  font-weight: var(--ds-font-weight-semibold);
}
</style>
