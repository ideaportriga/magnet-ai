<template lang="pug">
.source-tile.column.no-wrap.q-gap-4(:data-kind='isNote ? "note" : block.contentKind', data-test='source-block')
  q-btn.source-tile__remove(
    flat,
    dense,
    round,
    size='xs',
    icon='close',
    :aria-label='`Remove ${accessibleName}`',
    data-test='source-block-remove',
    @click.stop='emit("remove")'
  )
  .source-tile__body.column.no-wrap
    template(v-if='isNote')
      span.source-tile__eyebrow Note
      span.source-tile__note {{ block.text }}
    template(v-else)
      span.source-tile__site {{ siteName }}
      span.source-tile__title {{ block.title || `${formatCharCount(block.stats.chars)} characters` }}
  q-tooltip.bg-white.block-shadow.text-secondary-text.km-description {{ details }}
  .source-tile__meta.row.items-center.no-wrap.q-gap-4(v-if='!isNote')
    q-icon(:name='kind.icon', size='14px', :color='kind.color')
    span.source-tile__meta-text {{ kind.label }}
</template>

<script setup lang="ts">
/**
 * What one block of the "fill from text" field shows (#466). Never the pasted
 * text itself — the site it was copied from, its heading, whether it reads as
 * pricing or docs. A typed note shows its own text: the user wrote it.
 */
import { computed } from 'vue'

import { formatCharCount, type SourceBlock, type SourceContentKind } from './sourceBlocks'

const props = defineProps<{
  block: SourceBlock
}>()

const emit = defineEmits<{
  (e: 'remove'): void
}>()

const KIND: Record<SourceContentKind, { label: string; icon: string; color: string }> = {
  pricing: { label: 'Pricing', icon: 'o_table_chart', color: 'positive' },
  docs: { label: 'Docs', icon: 'o_menu_book', color: 'info' },
  mixed: { label: 'Docs + Pricing', icon: 'o_layers', color: 'primary' },
  unknown: { label: 'Text', icon: 'o_notes', color: 'secondary-text' },
}

const isNote = computed(() => props.block.kind === 'note')
const kind = computed(() => KIND[props.block.contentKind])
const siteName = computed(() => props.block.site ?? 'Pasted text')

const details = computed(() =>
  isNote.value
    ? 'An instruction for the extraction. Click to edit.'
    : `${formatCharCount(props.block.stats.chars)} characters, ${props.block.stats.tables} tables, ${props.block.stats.prices} prices`
)

const accessibleName = computed(() => (isNote.value ? 'Note' : siteName.value))
</script>

<style scoped>
.source-tile {
  block-size: 100%;
  min-inline-size: 0;
}
.source-tile[data-kind='note'] {
  cursor: pointer;
}
/* Top-right corner of the block; the first line leaves room for it. */
.source-tile__remove {
  position: absolute;
  inset-block-start: 4px;
  inset-inline-end: 4px;
}
.source-tile__body {
  flex: 1;
  gap: 2px;
  min-block-size: 0;
  overflow: hidden;
}
.source-tile__body > :first-child {
  padding-inline-end: 24px;
}
.source-tile__site {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 12px;
  color: var(--q-secondary-text);
}
.source-tile__title,
.source-tile__note {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.3;
}
.source-tile__title {
  -webkit-line-clamp: 2;
  font-weight: 600;
}
.source-tile__note {
  -webkit-line-clamp: 3;
  color: var(--q-secondary-text);
}
.source-tile__eyebrow {
  font-size: 12px;
  font-weight: 600;
  color: var(--q-secondary-text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.source-tile__meta {
  min-inline-size: 0;
  font-size: 12px;
  color: var(--q-secondary-text);
}
.source-tile__meta-text {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
