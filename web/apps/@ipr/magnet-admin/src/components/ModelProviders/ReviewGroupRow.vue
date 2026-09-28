<template lang="pug">
.review-row.column.q-gap-8.q-pa-16(:data-state='!available ? "missing" : modelValue ? "on" : "off"', data-test='review-group-row')
  .row.items-center.justify-between.q-gap-8
    q-toggle(
      dense,
      :model-value='available && modelValue',
      :disable='!available',
      :label='title',
      @update:model-value='emit("update:modelValue", $event)'
    )
    span.review-row__meta(v-if='!available') Not in the pasted text
    span.review-row__meta(v-else-if='$slots.meta')
      slot(name='meta')
  .review-row__body(v-if='available')
    slot
</template>

<script setup lang="ts">
/**
 * One group (description, capabilities, pricing) of a model in the "fill
 * from text" review (#466): a switch that says whether the group is saved,
 * then what the text said.
 *
 * A group the text didn't cover keeps its row — switch off and disabled,
 * "Not in the pasted text" on the right — so every model reads the same
 * top to bottom. A group switched off keeps its content, faded.
 */
defineProps<{
  title: string
  modelValue: boolean
  /** The text stated something for this group. */
  available: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
</script>

<style scoped>
.review-row__meta {
  font-size: 12px;
  color: var(--q-secondary-text);
}
.review-row__body {
  transition: opacity 0.15s ease-out;
}
.review-row[data-state='off'] .review-row__body {
  opacity: 0.5;
}
</style>
