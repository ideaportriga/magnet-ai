<script setup lang="ts">
/**
 * FieldError — accessible inline error message. Pass either a slot, a single
 * string, or an `errors` array (deduped by message). Renders nothing when
 * empty.
 */

import { computed } from 'vue'

const props = defineProps<{
  errors?: Array<string | { message: string | undefined } | undefined>
}>()

const content = computed<string | string[] | null>(() => {
  if (!props.errors || props.errors.length === 0) return null

  const uniqueErrors = [
    ...new Map(
      props.errors
        .filter(Boolean)
        .map((error) => {
          const message = typeof error === 'string' ? error : error?.message
          return [message, error]
        }),
    ).values(),
  ]

  if (uniqueErrors.length === 1 && uniqueErrors[0]) {
    const single = uniqueErrors[0]
    return typeof single === 'string' ? single : single.message ?? null
  }

  return uniqueErrors
    .map((error) => (typeof error === 'string' ? error : error?.message))
    .filter((m): m is string => !!m)
})
</script>

<template>
  <div
    v-if="$slots.default || content"
    role="alert"
    class="ds-field-error"
    data-test="ds-field-error"
  >
    <slot v-if="$slots.default" />

    <template v-else-if="typeof content === 'string'">
      {{ content }}
    </template>

    <ul v-else-if="Array.isArray(content)" class="ds-field-error__list">
      <li v-for="(error, index) in content" :key="index">
        {{ error }}
      </li>
    </ul>
  </div>
</template>

<style>
.ds-field-error {
  color: var(--ds-color-error-text);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-regular);
}
.ds-field-error__list {
  margin: 0;
  padding-inline-start: var(--ds-space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  list-style: disc;
}
</style>
