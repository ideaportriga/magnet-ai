<template>
  <div
    class="no-wrap full-height justify-center q-pa-16 q-pr-8 bg-white fit relative-position bl-border"
    style="max-width: 500px; min-width: 500px !important"
  >
    <div class="column full-height">
      <div class="col-auto km-heading-7 q-mb-xs">
        <div class="row">
          <div class="col">Chunk Details</div>
          <div class="col-auto">
            <q-btn flat round dense icon="close" @click="$emit('close')" />
          </div>
        </div>
      </div>
      <q-separator class="q-mb-md" />

      <div class="col q-pr-8 scroll">
        <div class="ba-border border-radius-6">
          <div class="bg-secondary-bg q-pa-8 border-radius-top-6">
            <div class="row items-center no-wrap border-radius-top-6">
              <div class="col">
                <div class="km-heading-8 text-weight-medium">{{ chunk.title || 'Untitled Chunk' }}</div>
              </div>
              <div v-if="chunk.page" class="col-auto q-ml-md q-mr-sm">
                <q-badge color="secondary" text-color="white" outline class="q-py-4">Page {{ chunk.page }}</q-badge>
              </div>
            </div>
          </div>
          <div class="bg-grey-1 q-pa-md border-radius-6">
            <div class="col scroll q-pr-8">
              <div class="markdown-content text-body2" v-html="renderedContent" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
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
import { Chunk } from './models'

const props = defineProps<{
  chunk: Chunk
}>()

defineEmits<{
  close: []
}>()

const markdown = new MarkdownIt()
  .use(MarkdownItAbbr)
  .use(MarkdownItAnchor)
  .use(MarkdownItFootnote)
  .use(MarkdownItHighlightjs)
  .use(MarkdownItSub)
  .use(MarkdownItSup)
  .use(MarkdownItTasklists)
  .use(MarkdownItTOC)

const renderedContent = computed(() => {
  if (!props.chunk.content) return ''
  if (props.chunk.content_format === 'html') {
    return props.chunk.content
  }
  // fallback is markdown, or any other format
  return markdown.render(props.chunk.content)
})
</script>

<style scoped>
.markdown-content {
  line-height: 1.7;
  color: #333;
  font-size: 14px;
}

/* Headings - smaller and more refined */
.markdown-content :deep(h1) {
  font-size: 20px;
  font-weight: 700;
  margin: 16px 0 12px 0;
  line-height: 1.3;
  color: #1a1a1a;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 18px;
  font-weight: 700;
  margin: 14px 0 10px 0;
  line-height: 1.3;
  color: #222;
}

.markdown-content :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 12px 0 8px 0;
  line-height: 1.3;
  color: #333;
}

.markdown-content :deep(h4) {
  font-size: 15px;
  font-weight: 600;
  margin: 10px 0 6px 0;
  line-height: 1.3;
  color: #444;
}

.markdown-content :deep(h5) {
  font-size: 14px;
  font-weight: 600;
  margin: 8px 0 4px 0;
  color: #555;
}

.markdown-content :deep(h6) {
  font-size: 13px;
  font-weight: 600;
  margin: 6px 0 3px 0;
  color: #666;
}

/* Paragraphs */
.markdown-content :deep(p) {
  margin: 0 0 10px 0;
  line-height: 1.7;
  color: #444;
}

/* Lists */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0 10px 0;
  padding-left: 24px;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
}

.markdown-content :deep(ol) {
  list-style-type: decimal;
}

.markdown-content :deep(li) {
  margin-bottom: 6px;
  line-height: 1.6;
  color: #444;
}

.markdown-content :deep(ul ul),
.markdown-content :deep(ol ol) {
  margin: 4px 0 4px 0;
}

/* Inline code */
.markdown-content :deep(code) {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #d63384;
  line-height: 1;
}

.markdown-content :deep(pre) {
  background-color: #f8f8f8;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
  margin: 10px 0;
  line-height: 1.5;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  color: #333;
  padding: 0;
  font-size: 12px;
}

/* Blockquotes */
.markdown-content :deep(blockquote) {
  border-left: 4px solid #e0e0e0;
  padding: 0 0 0 12px;
  margin: 10px 0;
  color: #666;
  font-style: italic;
}

/* Links */
.markdown-content :deep(a) {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}

.markdown-content :deep(a:hover) {
  color: #1565c0;
  text-decoration: underline;
}

/* Emphasis */
.markdown-content :deep(strong) {
  font-weight: 600;
  color: #1a1a1a;
}

.markdown-content :deep(em) {
  font-style: italic;
  color: #333;
}

/* Horizontal rule */
.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 16px 0;
}

/* Tables */
.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
  font-size: 13px;
}

.markdown-content :deep(th) {
  background-color: #f5f5f5;
  padding: 8px;
  border: 1px solid #e0e0e0;
  font-weight: 600;
  text-align: left;
}

.markdown-content :deep(td) {
  padding: 8px;
  border: 1px solid #e0e0e0;
}

/* Images */
.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 8px 0;
}

/* Task lists */
.markdown-content :deep(.task-list-item) {
  list-style-type: none;
  padding-left: 24px;
}

.markdown-content :deep(.task-list-item-checkbox) {
  margin-right: 8px;
}
</style>
