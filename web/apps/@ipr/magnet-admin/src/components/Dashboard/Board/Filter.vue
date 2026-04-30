<template>
  <div class="cluster pb-lg" data-gap="lg">
    <km-glyph name="filter" size="24px" />
    <template v-for="filter in filter" :key="filter">
      <div v-if="!filter.hide" class="cluster" data-gap="xs">
        <km-select :model-value="activeFilters[filter.key]" :has-dropdown-search="filter.search" :options="filter.options" use-chips map-option option-label="label" option-value="value" :permanent-placeholder="filter.label" :multiple="filter.multiple" :placeholder="m.common_all()" @update:model-value="setFilter(filter.key, $event)" />
        <km-glyph v-if="filter.hidden" class="my-auto cursor-pointer" name="close" @click.stop.prevent="hideFilter(filter.key)" />
      </div>
    </template>
    <km-select-flat v-if="hiddenFilters.length" :placeholder="m.common_addFilter()" :options="hiddenFilters" model-value="" @update:model-value="updateVisibleFilters" />
    <km-btn v-if="showClearAll" :label="m.common_clearAllFilters()" flat @click="clearAll" />
  </div>
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
