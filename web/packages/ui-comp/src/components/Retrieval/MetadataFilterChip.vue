<template>
  <q-chip class="filter-chip" text-color="primary" color="primary-light" clickable square size="12px" @click="emit('click', filter)">
    <div class="row items-baseline">
      <span class="ellipsis" style="max-width: 180px" v-html="values" />
      <q-icon v-if="!readonly" class="q-ml-xs" name="fa fa-times" @click="emit('remove', filter)" />
    </div>
  </q-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Filter } from '@shared/types'

// Models & Props
const filter = defineModel<Filter>({ required: true })
defineProps<{
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'click', filter: Filter): void
  (e: 'remove', filter: Filter): void
}>()

const values = computed(() => {
  const seen = new Set()
  const conditions = []
  for (const c of filter.value.conditions.filter((c) => c.type === 'value')) {
    const key = `${c.value}::${c.operator}`
    const value = c.value?.toLowerCase()
    if (value && !seen.has(key)) {
      seen.add(key)
      if (c.operator === 'equal') {
        conditions.push(`<span>${value}</span>`)
      } else {
        conditions.push(`<i>not</i> <span>${value}</span>`)
      }
    }
  }

  const emptyCondition = filter.value.conditions.find((c) => c.type === 'empty')
  if (emptyCondition) {
    const value = emptyCondition.operator === 'equal' ? 'is empty' : 'is not empty'
    conditions.push(`<i>${filter.value.field?.toLocaleLowerCase()} ${value}</i>`)
  }

  const existsCondition = filter.value.conditions.find((c) => c.type === 'exists')
  if (existsCondition) {
    const value = existsCondition.operator === 'equal' ? 'exists' : 'does not exist'
    conditions.push(`<i>${filter.value.field?.toLocaleLowerCase()} ${value}</i>`)
  }

  return conditions.join(' | ')
})
</script>

<style lang="stylus" scoped>
.filter-chip
  &:focus
    box-shadow: none !important
</style>
