<script setup lang="ts">
/**
 * `<km-file-picker>` — drag-and-drop file picker. Drop-in for the legacy
 * FilePicker. Internally uses native `<input type="file">` plus drop-zone
 * styling; no Quasar dependency.
 */

import { computed, ref, useTemplateRef, watch } from 'vue'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'

const props = withDefaults(
  defineProps<{
    modelValue?: File | File[] | null
    accept?: string
    multiple?: boolean
    maxFiles?: number | string
    /** Size limit per file in bytes. */
    maxSize?: number
    clearable?: boolean
    loading?: boolean
    loadingText?: string
    hint?: string
    disabled?: boolean
  }>(),
  {
    multiple: false,
    clearable: true,
    loading: false,
    hint: 'Click or drag files here',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: File | File[] | null]
  pick: [files: File[]]
  rejected: [reason: 'too-many' | 'too-large']
  clear: []
}>()

const fileInputRef = useTemplateRef<HTMLInputElement>('fileInput')
const isDragover = ref(false)
const internalFiles = ref<File[]>([])

watch(
  () => props.modelValue,
  (next) => {
    if (Array.isArray(next)) internalFiles.value = next
    else if (next instanceof File) internalFiles.value = [next]
    else internalFiles.value = []
  },
  { immediate: true },
)

const hasFiles = computed(() => internalFiles.value.length > 0)
const displayFiles = computed(() => internalFiles.value.slice(0, 3))

function commit(files: File[]) {
  internalFiles.value = files
  emit('pick', files)
  emit('update:modelValue', props.multiple ? files : (files[0] ?? null))
}

function applyConstraints(files: File[]): File[] | null {
  const limit = props.maxFiles ? Number(props.maxFiles) : Infinity
  if (props.multiple && files.length > limit) {
    emit('rejected', 'too-many')
    return null
  }
  if (props.maxSize) {
    const tooBig = files.some((f) => f.size > (props.maxSize as number))
    if (tooBig) {
      emit('rejected', 'too-large')
      return null
    }
  }
  return files
}

function triggerPick() {
  if (props.disabled || props.loading) return
  fileInputRef.value?.click()
}

function onInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files ?? [])
  const next = applyConstraints(files)
  if (next) commit(next)
  // Reset to allow picking the same file again.
  target.value = ''
}

function onDrop(event: DragEvent) {
  isDragover.value = false
  if (props.disabled || props.loading) return
  const files = Array.from(event.dataTransfer?.files ?? [])
  const next = applyConstraints(files)
  if (next) commit(next)
}

function clear() {
  internalFiles.value = []
  emit('update:modelValue', props.multiple ? [] : null)
  emit('clear')
}
</script>

<template>
  <div class="km-file-picker">
    <button
      type="button"
      class="km-file-picker__zone"
      :data-dragover="isDragover ? 'true' : undefined"
      :data-has-files="hasFiles ? 'true' : undefined"
      :data-loading="loading ? 'true' : undefined"
      :data-disabled="disabled ? 'true' : undefined"
      data-test="km-file-picker"
      @click="triggerPick"
      @dragover.prevent="isDragover = true"
      @dragleave.prevent="isDragover = false"
      @drop.prevent="onDrop"
    >
      <template v-if="loading">
        <span class="km-file-picker__spinner" aria-hidden="true" />
        <span v-if="loadingText" class="km-file-picker__hint">{{ loadingText }}</span>
      </template>

      <template v-else-if="hasFiles">
        <ul class="km-file-picker__files">
          <li
            v-for="(f, i) in displayFiles"
            :key="i"
            class="km-file-picker__file"
          >
            <KmGlyph name="file" size="18px" tone="subtle" />
            <span class="km-file-picker__filename">{{ f.name }}</span>
          </li>
        </ul>
        <span v-if="multiple && internalFiles.length" class="km-file-picker__hint">
          {{ internalFiles.length }} file(s) selected
        </span>
        <KmBtn
          v-if="clearable"
          flat
          size="xs"
          icon="close"
          icon-size="12px"
          @click.stop="clear"
        />
      </template>

      <template v-else>
        <KmGlyph name="cloud-upload" size="32px" tone="brand" />
        <span class="km-file-picker__hint">{{ hint }}</span>
      </template>
    </button>

    <input
      ref="fileInput"
      type="file"
      class="km-file-picker__input"
      :accept="accept"
      :multiple="multiple"
      @change="onInputChange"
    />
  </div>
</template>

<style>
.km-file-picker { position: relative; display: block; }
.km-file-picker__input { display: none; }

.km-file-picker__zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-sm);
  inline-size: 100%;
  min-block-size: 9rem;
  padding: var(--ds-space-lg);
  background: var(--ds-color-control-bg);
  border: 2px dashed var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  cursor: pointer;
  text-align: center;
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-file-picker__zone:hover { border-color: var(--ds-color-primary); background: var(--ds-color-primary-bg); }
.km-file-picker__zone[data-dragover='true'] { border-color: var(--ds-color-primary); background: var(--ds-color-primary-bg); }
.km-file-picker__zone[data-has-files='true'] { border-style: solid; }
.km-file-picker__zone[data-disabled='true'] { opacity: 0.6; pointer-events: none; }

.km-file-picker__hint {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
}

.km-file-picker__files {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-xs);
  list-style: "";
  margin: 0;
  padding: 0;
}
.km-file-picker__file {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
}
.km-file-picker__filename { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.km-file-picker__spinner {
  inline-size: 32px;
  block-size: 32px;
  border: 3px solid var(--ds-color-border);
  border-block-start-color: var(--ds-color-primary);
  border-radius: 50%;
  animation: ds-spin 0.9s var(--ds-ease-linear) infinite;
}
</style>
