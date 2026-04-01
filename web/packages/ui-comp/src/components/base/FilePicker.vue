<template lang="pug">
.file-picker
  .file-picker__zone(
    :class='{ "file-picker__zone--dragover": isDragover, "file-picker__zone--has-files": hasFiles, "file-picker__zone--loading": loading }',
    @click='triggerPick',
    @dragover.prevent='isDragover = true',
    @dragleave.prevent='isDragover = false',
    @drop.prevent='onDrop'
  )
    template(v-if='loading')
      .column.justify-center.items-center.full-width
        q-spinner(color='primary', size='32px')
        .file-picker__hint.q-mt-sm(v-if='loadingText') {{ loadingText }}
    template(v-else-if='hasFiles')
      .file-picker__files
        .file-picker__file(v-for='(f, i) in displayFiles', :key='i')
          q-icon(name='fas fa-file', size='18px', class='q-mr-sm text-secondary-text')
          span.file-picker__filename {{ f.name }}
        .file-picker__hint(v-if='multiple && internalFiles?.length') {{ internalFiles.length }} file(s) selected
      km-btn(
        v-if='clearable',
        flat,
        size='xs',
        icon='fas fa-times',
        iconSize='12px',
        @click.stop='clear'
      )
    template(v-else)
      q-icon.file-picker__icon(name='fas fa-cloud-arrow-up', size='32px')
      .file-picker__hint {{ hint }}
  input.file-picker__input(
    ref='fileInput',
    type='file',
    :accept='accept',
    :multiple='multiple',
    @change='onInputChange'
  )
</template>

<script>
import { defineComponent, ref, computed, watch } from 'vue'

export default defineComponent({
  name: 'FilePicker',
  props: {
    modelValue: {
      type: [Array, Object, File],
      default: null,
    },
    accept: {
      type: String,
      default: undefined,
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    maxFiles: {
      type: [Number, String],
      default: undefined,
    },
    clearable: {
      type: Boolean,
      default: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    loadingText: {
      type: String,
      default: undefined,
    },
    disable: {
      type: Boolean,
      default: false,
    },
    hint: {
      type: String,
      default: 'Drop files here or click to browse',
    },
  },
  emits: ['update:modelValue', 'rejected'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const isDragover = ref(false)
    const internalFiles = ref(normalizeFiles(props.modelValue))

    watch(
      () => props.modelValue,
      (val) => {
        internalFiles.value = normalizeFiles(val)
      }
    )

    function normalizeFiles(val) {
      if (val == null || val === '') return props.multiple ? [] : null
      if (Array.isArray(val)) return val
      if (val instanceof File) return props.multiple ? [val] : val
      return props.multiple ? [] : null
    }

    const hasFiles = computed(() => {
      const v = internalFiles.value
      if (Array.isArray(v)) return v.length > 0
      return v != null
    })

    const displayFiles = computed(() => {
      const v = internalFiles.value
      if (Array.isArray(v)) return v.slice(0, 5)
      if (v instanceof File) return [v]
      return []
    })

    function triggerPick() {
      if (props.disable || props.loading) return
      fileInput.value?.click()
    }

    function onInputChange(e) {
      const input = e.target
      const files = input?.files
      if (!files?.length) return
      const arr = Array.from(files)
      internalFiles.value = props.multiple ? arr : arr[0]
      emit('update:modelValue', internalFiles.value)
      input.value = ''
    }

    function onDrop(e) {
      isDragover.value = false
      if (props.disable || props.loading) return
      const dt = e.dataTransfer
      if (!dt?.files?.length) return
      const files = Array.from(dt.files)
      if (props.multiple) {
        const existing = Array.isArray(internalFiles.value) ? internalFiles.value : []
        internalFiles.value = [...existing, ...files]
      } else {
        internalFiles.value = files[0]
      }
      emit('update:modelValue', internalFiles.value)
    }

    function clear() {
      internalFiles.value = props.multiple ? [] : null
      emit('update:modelValue', internalFiles.value)
    }

    return {
      fileInput,
      isDragover,
      internalFiles,
      hasFiles,
      displayFiles,
      triggerPick,
      onInputChange,
      onDrop,
      clear,
    }
  },
})
</script>

<style lang="stylus" scoped>
.file-picker
  width: 100%

.file-picker__zone
  display: flex
  flex-direction: column
  align-items: center
  justify-content: center
  min-height: 120px
  padding: 24px 16px
  border: 2px dashed rgba(0, 0, 0, 0.2)
  border-radius: 12px
  background: rgba(0, 0, 0, 0.02)
  cursor: pointer
  transition: border-color 0.2s, background 0.2s

  &:hover:not(.file-picker__zone--loading)
    border-color: rgba(0, 0, 0, 0.3)
    background: rgba(0, 0, 0, 0.04)

  &--dragover
    border-color: var(--q-primary)
    background: rgba(0, 0, 0, 0.06)

  &--has-files
    flex-direction: row
    flex-wrap: wrap
    justify-content: flex-start
    gap: 8px
    align-items: center

  &--loading
    cursor: default

.file-picker__icon
  color: rgba(0, 0, 0, 0.35)
  margin-bottom: 8px

.file-picker__hint
  font-size: var(--km-font-size-label)
  color: rgba(0, 0, 0, 0.5)
  text-align: center

.file-picker__files
  display: flex
  flex-wrap: wrap
  gap: 8px
  flex: 1
  min-width: 0

.file-picker__file
  display: flex
  align-items: center
  padding: 6px 10px
  background: rgba(0, 0, 0, 0.06)
  border-radius: 8px
  font-size: var(--km-font-size-label)
  max-width: 180px

.file-picker__filename
  overflow: hidden
  text-overflow: ellipsis
  white-space: nowrap

.file-picker__input
  position: absolute
  width: 0
  height: 0
  opacity: 0
  pointer-events: none
</style>
