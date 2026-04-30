<script setup lang="ts">
/**
 * `<km-json-editor>` — drop-in over `vanilla-jsoneditor`.
 *
 * The legacy used `JSONEditor` from `vanilla-jsoneditor` and forwarded a
 * fixed prop list. We accept the same prop names plus `modelValue` for the
 * standard Vue v-model contract, but `content` keeps working too.
 */

import { JSONEditor, type Content, type JSONEditorPropsOptional } from 'vanilla-jsoneditor'
import { onBeforeUnmount, onMounted, ref, useTemplateRef, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: unknown
    content?: Content
    mode?: 'tree' | 'text' | 'table'
    readOnly?: boolean
    indentation?: number
    tabSize?: number
    mainMenuBar?: boolean
    navigationBar?: boolean
    statusBar?: boolean
    escapeControlCharacters?: boolean
    escapeUnicodeCharacters?: boolean
  }>(),
  {
    readOnly: true,
    indentation: 2,
    tabSize: 2,
    mainMenuBar: true,
    navigationBar: true,
    statusBar: true,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
  change: [content: Content]
}>()

const editorRef = useTemplateRef<HTMLDivElement>('editor')
const editor = ref<JSONEditor | null>(null)

function buildOptions(): JSONEditorPropsOptional {
  const initialContent: Content = props.content ?? ({ json: props.modelValue } as Content)
  return {
    content: initialContent,
    mode: props.mode,
    readOnly: props.readOnly,
    indentation: props.indentation,
    tabSize: props.tabSize,
    mainMenuBar: props.mainMenuBar,
    navigationBar: props.navigationBar,
    statusBar: props.statusBar,
    escapeControlCharacters: props.escapeControlCharacters,
    escapeUnicodeCharacters: props.escapeUnicodeCharacters,
    onChange: (updatedContent: Content) => {
      emit('change', updatedContent)
      const json = (updatedContent as { json?: unknown }).json
      const text = (updatedContent as { text?: unknown }).text
      emit('update:modelValue', json !== undefined ? json : text)
    },
  }
}

onMounted(() => {
  if (!editorRef.value) return
  editor.value = new JSONEditor({ target: editorRef.value, props: buildOptions() })
})

onBeforeUnmount(() => {
  editor.value?.destroy()
  editor.value = null
})

watch(
  () => props.modelValue,
  (next) => {
    if (!editor.value) return
    editor.value.update({ json: next } as Content)
  },
)

watch(
  () => props.readOnly,
  (next) => {
    editor.value?.updateProps({ readOnly: next })
  },
)
</script>

<template>
  <div ref="editor" class="km-json-editor" data-test="km-json-editor" />
</template>

<style>
.km-json-editor {
  display: flex;
  flex: 1 1 auto;
  min-block-size: 200px;
}
</style>
