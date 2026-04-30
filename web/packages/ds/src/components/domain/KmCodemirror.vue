<script setup lang="ts">
/**
 * `<km-codemirror>` — drop-in over `vue-codemirror`. Same public surface as
 * the legacy: `modelValue, readonly, language, indentWithTab, tabSize,
 * style, rules`.
 */

import { computed, toRefs } from 'vue'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from '@codemirror/view'
import { json } from '@codemirror/lang-json'
import { python } from '@codemirror/lang-python'
import useValidation from '@shared/composables/useValidation'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    readonly?: boolean
    language?: 'json' | 'python'
    indentWithTab?: boolean
    tabSize?: number
    style?: Record<string, string>
    rules?: unknown
  }>(),
  {
    readonly: false,
    language: 'json',
    indentWithTab: true,
    tabSize: 2,
    style: () => ({}),
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { modelValue, rules } = toRefs(props)
const { errorMessage } = useValidation(modelValue, rules)

const extensions = computed(() => {
  const base = [EditorView.lineWrapping]
  switch (props.language.toLowerCase()) {
    case 'python':
      return [...base, python()]
    case 'json':
    default:
      return [...base, json()]
  }
})

const selectedLineColor = computed(() => (props.readonly ? 'transparent' : '#cceeff44'))
</script>

<template>
  <span class="km-codemirror" :data-readonly="readonly ? 'true' : undefined">
    <Codemirror
      :indent-with-tab="indentWithTab"
      :tab-size="tabSize"
      :model-value="modelValue"
      :extensions="extensions"
      :disabled="readonly"
      :autofocus="false"
      :style="{ minHeight: '200px', ...style }"
      class="km-codemirror__editor"
      data-test="km-codemirror"
      @update:model-value="(value) => emit('update:modelValue', value as string)"
      @change="(value) => emit('update:modelValue', value as string)"
    />
    <span v-if="errorMessage" class="km-codemirror__error">{{ errorMessage }}</span>
  </span>
</template>

<style>
.km-codemirror {
  display: inline-flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  inline-size: 100%;
}
.km-codemirror[data-readonly='true'] .km-codemirror__editor :deep(.cm-editor) {
  background: var(--ds-color-light);
}
.km-codemirror :deep(.cm-gutters) {
  display: none;
}
.km-codemirror :deep(.cm-editor) {
  margin: 1px;
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-sm);
  padding: var(--ds-space-2xs);
  background: inherit;
}
.km-codemirror :deep(.cm-line) {
  background: v-bind(selectedLineColor) !important;
}
.km-codemirror__error {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-error-text);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
}
</style>
