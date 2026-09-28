<template lang="pug">
.column.q-gap-4(data-test='model-source-blocks')
  block-input(
    ref='field',
    v-model:draft='draft',
    :model-value='modelValue',
    :item-key='blockKey',
    placeholder='Paste a model card or pricing page',
    hint='Paste as many pages as you need, or type a note for the extraction and press Enter',
    draft-placeholder='Paste another page, or type a note and press Enter',
    list-label='Pasted pages and notes',
    :capture-min-length='CAPTURE_MIN_LENGTH',
    :error-message='limitError',
    @update:model-value='emit("update:modelValue", $event)',
    @transfer='onTransfer',
    @commit-text='onCommitText',
    @activate='onActivate'
  )
    template(#block='{ item, index }')
      source-block-tile(:block='item', @remove='removeBlock(index)')
  .km-description.text-secondary-text(v-if='nearLimit', data-test='model-source-blocks-near-limit')
    | {{ formatNumber(totalChars) }} of {{ formatNumber(SOURCE_CHAR_LIMIT) }} characters used.
</template>

<script setup lang="ts">
/**
 * Pasted pages and typed notes for "fill from text" (#466).
 *
 * One big field that fills up with blocks: paste (or drop) a model card or a
 * pricing page and it becomes a block showing where it came from, never the
 * text; type a line and press Enter and it becomes a note for the extraction
 * ("use EU Data Zone prices"). Any number of pages from any number of sites —
 * the review then lets the user pick between their pricing options.
 */
import { computed, ref, useTemplateRef } from 'vue'

import BlockInput from './BlockInput.vue'
import SourceBlockTile from './SourceBlockTile.vue'
import { useModelNotify } from './notifyModels'
import {
  blockFromTransfer,
  MAX_NOTES,
  MAX_SOURCES,
  noteBlock,
  noteBlocksOf,
  SOURCE_CHAR_LIMIT,
  SOURCE_CHAR_WARNING,
  sourceBlocksOf,
  totalSourceChars,
  type SourceBlock,
} from './sourceBlocks'

/** Single-line pastes shorter than this stay in the draft (a model name, a URL). */
const CAPTURE_MIN_LENGTH = 160
const TEXT_FILE_RE = /\.(?:txt|md|markdown|html?|csv|tsv)$/i

/** `<block-input>`'s `transfer` payload. */
interface BlockTransfer {
  html: string
  text: string
  files: File[]
}

const props = defineProps<{
  modelValue: SourceBlock[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', blocks: SourceBlock[]): void
}>()

const notify = useModelNotify()
const draft = ref('')
const field = useTemplateRef<{ focus: () => void }>('field')

const blockKey = (block: SourceBlock) => block.id
const totalChars = computed(() => totalSourceChars(props.modelValue))
const formatNumber = (value: number) => value.toLocaleString()
const limitError = computed(() =>
  totalChars.value > SOURCE_CHAR_LIMIT
    ? `The pasted pages are too long (${formatNumber(totalChars.value)} of ${formatNumber(SOURCE_CHAR_LIMIT)} characters). Remove a page or paste a smaller part of it.`
    : undefined
)
const nearLimit = computed(() => !limitError.value && totalChars.value >= SOURCE_CHAR_WARNING)

function addSources(blocks: SourceBlock[]) {
  if (!blocks.length) return
  const room = MAX_SOURCES - sourceBlocksOf(props.modelValue).length
  if (blocks.length > room) notify('warning', `You can paste up to ${MAX_SOURCES} pages.`)
  if (room <= 0) return
  emit('update:modelValue', [...props.modelValue, ...blocks.slice(0, room)])
}

function isTextFile(file: File): boolean {
  return file.type.startsWith('text/') || TEXT_FILE_RE.test(file.name)
}

async function blockFromFile(file: File): Promise<SourceBlock | null> {
  const content = await file.text()
  const isHtml = file.type === 'text/html' || /\.html?$/i.test(file.name)
  const block = blockFromTransfer(isHtml ? { html: content } : { text: content })
  if (block && !block.title) block.title = file.name
  return block
}

async function onTransfer(payload: BlockTransfer) {
  if (payload.files.length) {
    const files = payload.files.filter(isTextFile)
    if (files.length < payload.files.length) notify('warning', 'Only text, Markdown and HTML files can be dropped here.')
    const blocks = await Promise.all(files.map(blockFromFile))
    addSources(blocks.filter((block): block is SourceBlock => block !== null))
    return
  }
  const block = blockFromTransfer(payload)
  if (!block) {
    notify('warning', 'There is no text in what you pasted.')
    return
  }
  addSources([block])
}

function onCommitText(text: string) {
  const note = noteBlock(text)
  if (!note) return
  if (noteBlocksOf(props.modelValue).length >= MAX_NOTES) {
    // Keep what was typed; the user decides which note to drop.
    notify('warning', `You can add up to ${MAX_NOTES} notes.`)
    return
  }
  emit('update:modelValue', [...props.modelValue, note])
  draft.value = ''
}

function removeBlock(index: number) {
  emit(
    'update:modelValue',
    props.modelValue.filter((_, i) => i !== index)
  )
}

/** Clicking a note puts it back into the draft for editing. */
function onActivate(block: SourceBlock, index: number) {
  if (block.kind !== 'note' || draft.value.trim()) return
  removeBlock(index)
  draft.value = block.text
  field.value?.focus()
}
</script>
