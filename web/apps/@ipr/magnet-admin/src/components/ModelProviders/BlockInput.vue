<script setup lang="ts" generic="T">
/**
 * `<model-providers-block-input>` — a large field that collects square blocks, the way
 * `<km-chips-input type="add">` collects chips.
 *
 *   - Pasting into the empty draft (or dropping anything onto the field)
 *     emits `transfer` with the clipboard / drag payload instead of inserting
 *     text; the caller turns it into an item. A short single-line paste
 *     (under `captureMinLength`) and any paste while typing go into the draft.
 *   - Enter in the draft emits `commit-text`; Shift+Enter is a new line. The
 *     draft is `v-model:draft`, so the caller clears it once it took the text.
 *   - Backspace / ← on an empty draft moves focus to the last block; on a
 *     focused block Backspace / Delete removes it, ← / → move between blocks,
 *     Enter / Space emit `activate`, Esc returns to the draft.
 *
 * The component owns the frame, focus and keyboard model; what a block shows
 * is the caller's `#block` slot (`{ item, index, focused, remove }`).
 */

import { computed, nextTick, onBeforeUpdate, ref, useTemplateRef } from 'vue'

export interface KmBlockTransfer {
  html: string
  text: string
  files: File[]
}

const props = withDefaults(
  defineProps<{
    modelValue?: T[]
    /** Stable key per item; defaults to the index. */
    itemKey?: (item: T, index: number) => string | number
    /** Big empty-state line; also the draft's accessible name. */
    placeholder?: string
    /** Smaller line under the placeholder in the empty state. */
    hint?: string
    /** Draft placeholder once there are blocks. */
    draftPlaceholder?: string
    /** Accessible name of the block list. */
    listLabel?: string
    /** Plain-text pastes shorter than this (without line breaks) stay in the draft. */
    captureMinLength?: number
    minHeight?: string
    maxHeight?: string
    /** Side of a square block. */
    blockSize?: string
    errorMessage?: string
    disabled?: boolean
  }>(),
  {
    modelValue: () => [],
    itemKey: undefined,
    placeholder: '',
    hint: '',
    draftPlaceholder: '',
    listLabel: undefined,
    captureMinLength: 1,
    minHeight: '9rem',
    maxHeight: '26rem',
    blockSize: '8rem',
    errorMessage: undefined,
    disabled: false,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: T[]]
  'commit-text': [text: string]
  transfer: [payload: KmBlockTransfer]
  activate: [item: T, index: number]
  remove: [item: T, index: number]
}>()

const draft = defineModel<string>('draft', { default: '' })

const draftRef = useTemplateRef<HTMLTextAreaElement>('draftField')
const blockRefs = ref<HTMLElement[]>([])
const focusedIndex = ref(-1)
const dragging = ref(false)

onBeforeUpdate(() => {
  blockRefs.value = []
})

const isEmpty = computed(() => props.modelValue.length === 0)
const showEmptyState = computed(() => isEmpty.value && !draft.value)

function keyOf(item: T, index: number): string | number {
  return props.itemKey ? props.itemKey(item, index) : index
}

function focusDraft() {
  if (props.disabled) return
  focusedIndex.value = -1
  draftRef.value?.focus()
}

function focusBlock(index: number) {
  if (index < 0 || index >= props.modelValue.length) {
    focusDraft()
    return
  }
  focusedIndex.value = index
  blockRefs.value[index]?.focus()
}

function removeAt(index: number) {
  const item = props.modelValue[index]
  if (item === undefined) return
  const next = props.modelValue.slice()
  next.splice(index, 1)
  emit('update:modelValue', next)
  emit('remove', item, index)
  nextTick(() => (next.length ? focusBlock(Math.min(index, next.length - 1)) : focusDraft()))
}

function autosize() {
  const field = draftRef.value
  if (!field) return
  field.style.height = 'auto'
  field.style.height = `${field.scrollHeight}px`
}

function onDraftInput(event: Event) {
  draft.value = (event.target as HTMLTextAreaElement).value
  autosize()
}

function onDraftKeydown(event: KeyboardEvent) {
  if (event.isComposing) return
  const field = event.target as HTMLTextAreaElement
  const atStart = field.selectionStart === 0 && field.selectionEnd === 0
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    if (draft.value.trim()) emit('commit-text', draft.value)
    nextTick(autosize)
    return
  }
  if ((event.key === 'Backspace' && !draft.value) || (event.key === 'ArrowLeft' && atStart)) {
    if (props.modelValue.length) {
      event.preventDefault()
      focusBlock(props.modelValue.length - 1)
    }
  }
}

function onBlockKeydown(event: KeyboardEvent, index: number) {
  switch (event.key) {
    case 'Backspace':
    case 'Delete':
      event.preventDefault()
      removeAt(index)
      break
    case 'ArrowLeft':
    case 'ArrowUp':
      event.preventDefault()
      focusBlock(Math.max(index - 1, 0))
      break
    case 'ArrowRight':
    case 'ArrowDown':
      event.preventDefault()
      focusBlock(index + 1)
      break
    case 'Escape':
      event.preventDefault()
      focusDraft()
      break
    case 'Enter':
    case ' ':
      // Let buttons inside the block handle their own keys.
      if (event.target !== event.currentTarget) return
      event.preventDefault()
      emit('activate', props.modelValue[index], index)
      break
  }
}

function payloadOf(data: DataTransfer | null): KmBlockTransfer {
  return {
    html: data?.getData('text/html') ?? '',
    text: data?.getData('text/plain') ?? '',
    files: Array.from(data?.files ?? []),
  }
}

function onPaste(event: ClipboardEvent) {
  if (props.disabled || draft.value) return
  const payload = payloadOf(event.clipboardData)
  const long = payload.text.includes('\n') || payload.text.trim().length >= props.captureMinLength
  if (!payload.files.length && !long && !/<table[\s>]/i.test(payload.html)) return
  event.preventDefault()
  emit('transfer', payload)
}

function onDragOver(event: DragEvent) {
  if (props.disabled) return
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
  dragging.value = true
}

function onDragLeave(event: DragEvent) {
  const next = event.relatedTarget as Node | null
  if (next && (event.currentTarget as HTMLElement).contains(next)) return
  dragging.value = false
}

function onDrop(event: DragEvent) {
  dragging.value = false
  if (props.disabled) return
  event.preventDefault()
  const payload = payloadOf(event.dataTransfer)
  if (payload.files.length || payload.html.trim() || payload.text.trim()) emit('transfer', payload)
  focusDraft()
}

function onControlClick(event: MouseEvent) {
  // Clicks on a block (or inside it) are the block's own.
  if ((event.target as HTMLElement).closest('.km-block-input__block')) return
  focusDraft()
}

defineExpose({ focus: focusDraft })
</script>

<template>
  <div
    class="km-block-input"
    :data-state="errorMessage ? 'error' : dragging ? 'drag-over' : undefined"
    :data-disabled="disabled ? 'true' : undefined"
    :data-empty="showEmptyState ? 'true' : undefined"
    :style="{ '--km-block-min-height': minHeight, '--km-block-max-height': maxHeight, '--km-block-size': blockSize }"
    data-test="km-block-input"
  >
    <div class="km-block-input__control" @click="onControlClick" @dragover="onDragOver" @dragleave="onDragLeave" @drop="onDrop">
      <div v-if="!isEmpty" class="km-block-input__blocks" role="list" :aria-label="listLabel">
        <div
          v-for="(item, index) in modelValue"
          :key="keyOf(item, index)"
          :ref="
            (el) => {
              if (el) blockRefs[index] = el as HTMLElement
            }
          "
          class="km-block-input__block"
          role="listitem"
          :tabindex="focusedIndex === index ? 0 : -1"
          :data-focused="focusedIndex === index ? 'true' : undefined"
          data-test="km-block-input-block"
          @focus="focusedIndex = index"
          @blur="focusedIndex === index && (focusedIndex = -1)"
          @keydown="onBlockKeydown($event, index)"
          @click="emit('activate', item, index)"
        >
          <slot name="block" :item="item" :index="index" :focused="focusedIndex === index" :remove="() => removeAt(index)" />
        </div>
      </div>

      <textarea
        ref="draftField"
        class="km-block-input__draft"
        rows="1"
        :value="draft"
        :disabled="disabled"
        :placeholder="isEmpty ? '' : draftPlaceholder"
        :aria-label="placeholder || draftPlaceholder"
        data-test="km-block-input-draft"
        @input="onDraftInput"
        @keydown="onDraftKeydown"
        @paste="onPaste"
      />

      <div v-if="showEmptyState" class="km-block-input__empty" aria-hidden="true">
        <slot name="empty">
          <q-icon name="o_content_paste" size="28px" color="secondary-text" />
          <span class="km-block-input__placeholder">{{ placeholder }}</span>
          <span v-if="hint" class="km-block-input__hint">{{ hint }}</span>
        </slot>
      </div>
    </div>

    <p v-if="errorMessage" class="km-block-input__error">{{ errorMessage }}</p>
  </div>
</template>

<style>
.km-block-input {
  display: flex;
  flex-direction: column;
  gap: 4px;
  inline-size: 100%;
}

/* A large surface, so focus is the border colour alone — the 3px ring of a
 * one-line input reads as a heavy frame here — and hover changes nothing.
 * The draft always takes a row of its own under the blocks. */
.km-block-input__control {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-block-size: var(--km-block-min-height);
  max-block-size: var(--km-block-max-height);
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 8px;
  background: var(--q-control-bg);
  border: 1px solid var(--q-control-border);
  border-radius: 4px;
  cursor: text;
}
.km-block-input__control:focus-within {
  border-color: var(--q-primary);
}
.km-block-input[data-state='drag-over'] .km-block-input__control {
  border-style: dashed;
  border-color: var(--q-primary);
  background: var(--q-primary-bg);
}
.km-block-input[data-state='error'] .km-block-input__control {
  border-color: var(--q-error);
}
.km-block-input[data-disabled='true'] .km-block-input__control {
  cursor: not-allowed;
  opacity: 0.6;
}

/* Fixed squares, as many per row as fit. */
.km-block-input__blocks {
  display: grid;
  grid-template-columns: repeat(auto-fill, var(--km-block-size));
  gap: 8px;
}

/* Blocks sit inside the field's own border, so a fill (not a second
 * outline) sets them apart; focus is the ring alone. */
.km-block-input__block {
  position: relative;
  display: flex;
  flex-direction: column;
  inline-size: var(--km-block-size);
  block-size: var(--km-block-size);
  min-inline-size: 0;
  overflow: hidden;
  padding: 8px;
  background: var(--q-light);
  border-radius: 6px;
  cursor: default;
  transition:
    background-color 0.15s ease-out,
    box-shadow 0.15s ease-out;
}
.km-block-input__block:hover {
  background: var(--q-primary-bg);
}
.km-block-input__block:focus-visible,
.km-block-input__block[data-focused='true'] {
  outline: none;
  box-shadow: 0 0 0 2px var(--q-primary);
}

.km-block-input__draft {
  inline-size: 100%;
  min-block-size: 24px;
  max-block-size: 8rem;
  padding: 4px 6px;
  border: 0;
  outline: none;
  resize: none;
  overflow-y: auto;
  background: transparent;
  font: inherit;
  font-size: 13px;
  line-height: 1.5;
  color: inherit;
}
.km-block-input__draft::placeholder {
  color: var(--q-secondary-text);
}
/* Empty: the draft fills the field so a click anywhere lands in it. */
.km-block-input[data-empty='true'] .km-block-input__draft {
  flex: 1;
}

.km-block-input__empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 24px;
  text-align: center;
  pointer-events: none;
}
.km-block-input__placeholder {
  font-size: 14px;
  font-weight: 500;
  color: var(--q-secondary-text);
}
.km-block-input__hint {
  font-size: 12px;
  color: var(--q-secondary-text);
}

.km-block-input__error {
  font-size: 11px;
  color: var(--q-error-text);
  padding: 4px 8px;
  margin: 0;
}
</style>
