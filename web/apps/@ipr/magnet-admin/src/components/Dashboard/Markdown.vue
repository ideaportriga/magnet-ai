<!-- eslint-disable vue/no-v-html -->
<template>
  <div v-html="renderedMarkdown" />
  <!-- <div>
    <q-btn
      label="Copy to clipboard"
      @click="copyToClipboard2(renderedMarkdown)"
    />
  </div> -->
</template>

<script setup lang="ts">
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
// import { copyToClipboard } from 'quasar'

const markdown = new MarkdownIt()
  .use(MarkdownItAbbr)
  .use(MarkdownItAnchor)
  .use(MarkdownItFootnote)
  .use(MarkdownItHighlightjs)
  .use(MarkdownItSub)
  .use(MarkdownItSup)
  .use(MarkdownItTasklists)
  .use(MarkdownItTOC)

const defaultLinkRenderer = markdown.renderer.rules.link_open || ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))

markdown.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  tokens[idx].attrPush(['target', '_blank'])
  tokens[idx].attrPush(['rel', 'noopener noreferrer'])

  return defaultLinkRenderer(tokens, idx, options, env, self)
}

const props = defineProps<{
  source: string
}>()

// const copyToClipboard2 = (text: string) => {
//   var blob = new Blob([text], { type: 'text/html' });
//   var data = [new ClipboardItem({ 'text/html': blob })];
//   console.log(data)
//   window.navigator.clipboard.write(data)
// }

const processedSource = computed(() => {
  // Remove Markdown code block delimiters
  // check if source is a string

  const isString = (value): value is string => {
    return typeof value === 'string'
  }

  if (!isString(props?.source)) {
    return ''
  }

  return props?.source?.replace(/^```markdown\s*|```$/g, '') || ''
})

const renderedMarkdown = computed(() => {
  return markdown.render(processedSource.value)
})
</script>

<style scoped>
/* [data-theme='default'] :deep(p) {
  padding: 0;
  margin: 0 0 16px 0;
  font-family: var(--font-default);
  font-size: 14px;
  font-weight: 400;
  white-space: pre-wrap;
}

:deep(h1) {
  font-family: var(--font-default);
  font-size: 22px;
  font-weight: 600;
  padding: 0;
  margin: 0 0 16px 0;
  line-height: 22px;
}

:deep(h2) {
  font-family: var(--font-default);
  font-size: 20px;
  font-weight: 600;
  padding: 0;
  margin: 0 0 16px 0;
  line-height: 20px;
}

:deep(h3) {
  font-family: var(--font-default);
  font-size: 18px;
  font-weight: 700;
  padding: 0;
  margin: 0 0 12px 0;
  line-height: 18px;
}

:deep(h4) {
  font-family: var(--font-default);
  font-size: 16px;
  font-weight: 700;
  padding: 0;
  margin: 0 0 12px 0;
  line-height: 16px;
}

:deep(ol) {
  padding: 0;
  margin: 0;
}

:deep(ul) {
  padding-left: 2em;
  list-style-type: disc;
  margin: 0 0 16px 0;
}

:deep(li) {
  margin-bottom: 0.5em;
}

:deep(a) {
  color: #3498db;
  text-decoration: none;
}

:deep(a:hover) {
  text-decoration: underline;
} */
:deep(*) {
  font-family: var(--font-default);
  font-size: 14px !important;
  font-weight: 400 !important;
}

:deep(ol) {
  padding: 0 0 0 1em;
  margin: 0;
}
:deep(p) {
  white-space: pre-wrap;
  margin: 0 0 8px 0;
}
:deep(pre) {
  white-space: pre-wrap;
  margin: 0 0 8px 0;
}
:deep(ul) {
  padding-left: 20px;
  list-style-type: disc;
}
:deep(a) {
  color: #3498db;
  text-decoration: none;
}

:deep(a:hover) {
  text-decoration: underline;
}
:deep(h1),
:deep(h2),
:deep(h3),
:deep(h4) {
  padding: 0 !important;
  margin: 10px 0 10px 0;
  line-height: 1 !important;
}
:deep(strong) {
}
</style>
