<template lang="pug">
.row.q-gap-16.items-center.q-pb-16
  q-icon(name='filter_list', size='24px', color='secondary')
  template(v-for='filter in filter')
    .row.items-center.q-gap-4(v-if='!filter.hide')
      km-select(
        :modelValue='activeFilters[filter.key]',
        @update:modelValue='setFilter(filter.key, $event)',
        :hasDropdownSearch='filter.search',
        :options='filter.options',
        useChips,
        mapOption,
        optionLabel='label',
        optionValue='value',
        :permanentPlaceholder='filter.label',
        :multiple='filter.multiple',
        :placeholder='m.common_all()'
      )
      q-icon.q-my-auto.cursor-pointer(v-if='filter.hidden', color='secondary', name='fa fa-times', @click.stop.prevent='hideFilter(filter.key)')

  km-select-flat(
    v-if='hiddenFilters.length',
    :placeholder='m.common_addFilter()',
    @update:modelValue='updateVisibleFilters',
    :options='hiddenFilters',
    modelValue=''
  )
  km-btn(:label='m.common_clearAllFilters()', @click='clearAll', flat, v-if='showClearAll')
</template>
<script>
import { m } from '@/paraglide/messages'
export default {
  props: {
    filter: {
      type: Array,
      required: true,
    },
    activeFilters: {
      type: Object,
      required: true,
    },
  },
  emits: ['updateVisibleFilters', 'updateActiveFilters'],
  setup() {
    return { m }
  },
  computed: {
    showClearAll() {
      return Object.values(this.activeFilters).filter((v) => !!v).length
    },
    hiddenFilters() {
      return Object.values(this.filter)
        .filter((f) => f.hide)
        .map((f) => {
          return {
            label: f.label,
            value: f.key,
          }
        })
    },
  },
  methods: {
    updateVisibleFilters({ value }) {
      this.$emit('updateVisibleFilters', value, false)
    },
    hideFilter(key) {
      this.$emit('updateVisibleFilters', key, true)
      this.$emit('updateActiveFilters', { key, value: null })
    },
    setFilter(key, value) {
      this.$emit('updateActiveFilters', { key, value })
    },
    clearAll() {
      this.$emit('updateActiveFilters')
    },
  },
}
</script>
