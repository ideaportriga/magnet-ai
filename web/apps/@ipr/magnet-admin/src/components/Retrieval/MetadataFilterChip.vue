<script setup lang="ts">
/**
 * Single filter chip — clickable summary of one metadata filter's
 * conditions. Migrated to admin in Phase 4c, rewritten without Quasar.
 */

import { computed } from 'vue'
import type { Filter } from '@shared/types'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'

const filter = defineModel<Filter>({ required: true })
defineProps<{ readonly?: boolean }>()
const emit = defineEmits<{
  click: [filter: Filter]
  remove: [filter: Filter]
}>()

const values = computed(() => {
  const seen = new Set<string>()
  const conditions: string[] = []

  for (const c of (filter.value.conditions ?? []).filter((c) => c.type === 'value')) {
    const key = `${c.value}::${c.operator}`
    const value = c.value?.toLowerCase()
    if (value && !seen.has(key)) {
      seen.add(key)
      conditions.push(c.operator === 'equal' ? `<span>${value}</span>` : `<i>not</i> <span>${value}</span>`)
    }
  }

  const emptyCondition = filter.value.conditions?.find((c) => c.type === 'empty')
  if (emptyCondition) {
    const word = emptyCondition.operator === 'equal' ? 'is empty' : 'is not empty'
    conditions.push(`<i>${filter.value.field?.toLocaleLowerCase()} ${word}</i>`)
  }

  const existsCondition = filter.value.conditions?.find((c) => c.type === 'exists')
  if (existsCondition) {
    const word = existsCondition.operator === 'equal' ? 'exists' : 'does not exist'
    conditions.push(`<i>${filter.value.field?.toLocaleLowerCase()} ${word}</i>`)
  }

  return conditions.join(' | ')
})
</script>

<template>
  <button
    type="button"
    class="filter-chip"
    @click="emit('click', filter)"
  >
    <span class="cluster gap-xs" data-align="baseline">
      <!-- eslint-disable-next-line vue/no-v-html -->
      <span class="filter-chip__values" v-html="values" />
      <span
        v-if="!readonly"
        class="filter-chip__remove"
        role="button"
        tabindex="0"
        aria-label="Remove filter"
        @click.stop="emit('remove', filter)"
        @keydown.enter.prevent="emit('remove', filter)"
      >
        <KmGlyph name="close" size="12px" tone="brand" />
      </span>
    </span>
  </button>
</template>

<style scoped>
.filter-chip {
  background: var(--ds-color-primary-light);
  color: var(--ds-color-primary);
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-medium);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  border-radius: var(--ds-radius-sm);
  border: 0;
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.filter-chip:hover { background: color-mix(in srgb, var(--ds-color-primary-light) 80%, var(--ds-color-primary)); }
.filter-chip:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: 2px; box-shadow: none; }

.filter-chip__values {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-inline-size: 180px;
}
.filter-chip__remove { display: inline-flex; align-items: center; cursor: pointer; }
</style>
