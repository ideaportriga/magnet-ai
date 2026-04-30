<script setup lang="ts">
/**
 * Textarea — multi-line input. Visual states mirror `<DsInput>`.
 * Use `field-sizing: content` (where supported) so the textarea grows with
 * its content automatically.
 *
 *   <DsTextarea v-model="notes" placeholder="Add notes…" />
 */

import { useVModel } from '@vueuse/core'
import { useTemplateRef } from 'vue'

const props = defineProps<{
  modelValue?: string | number
  defaultValue?: string | number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const model = useVModel(props, 'modelValue', emit, {
  passive: true,
  defaultValue: props.defaultValue,
})

const textareaEl = useTemplateRef<HTMLTextAreaElement>('textareaEl')

defineExpose({
  focus: (options?: FocusOptions) => textareaEl.value?.focus(options),
  blur: () => textareaEl.value?.blur(),
  select: () => textareaEl.value?.select(),
  el: textareaEl,
})
</script>

<template>
  <textarea
    ref="textareaEl"
    v-model="model"
    class="ds-textarea"
    data-test="ds-textarea"
  />
</template>

<style>
.ds-textarea {
  display: block;
  inline-size: 100%;
  min-block-size: 64px;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-body);
  line-height: var(--ds-line-height-normal);
  color: var(--ds-color-black);
  background: var(--ds-color-control-bg);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  padding: var(--ds-space-sm) var(--ds-space-md);
  outline: none;
  resize: block;
  field-sizing: content;
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}

.ds-textarea::placeholder { color: var(--ds-color-placeholder-fg); }

.ds-textarea:hover:not(:disabled, [aria-invalid='true'], [readonly]) {
  border-color: var(--ds-color-control-hover-border);
}

.ds-textarea:focus-visible {
  border-color: var(--ds-color-focus-border);
  box-shadow: 0 0 0 3px var(--ds-color-focus-ring);
}

.ds-textarea[aria-invalid='true'] { border-color: var(--ds-color-invalid-border); }
.ds-textarea[aria-invalid='true']:focus-visible {
  box-shadow: 0 0 0 3px var(--ds-color-invalid-ring);
}

.ds-textarea[readonly] {
  background: var(--ds-color-readonly-bg);
  color: var(--ds-color-readonly-fg);
  border-color: var(--ds-color-readonly-border);
  cursor: default;
}

.ds-textarea:disabled {
  background: var(--ds-color-disabled-bg);
  color: var(--ds-color-disabled-fg);
  border-color: var(--ds-color-disabled-border);
  cursor: not-allowed;
}
</style>
