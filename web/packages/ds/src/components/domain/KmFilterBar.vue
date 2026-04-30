<script setup lang="ts">
/**
 * `<km-filter-bar>` — filter strip used in admin lists.
 *
 * Public surface kept stable: `config` (filter definitions object),
 * `filterObject` (current values), `filterPlaceholder`. Emits
 * `update:filterObject`. The legacy implementation drove a row of
 * `km-select` controls plus a hideable "Add filter" affordance —
 * this rebuild keeps the same UX with `KmSelect` + `KmSelectFlat`.
 */

import { computed, ref } from 'vue'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'
import KmSelect from './KmSelect.vue'
import KmSelectFlat from './KmSelectFlat.vue'

interface FilterConf {
  key: string
  label: string
  multiple?: boolean
  search?: boolean
  is_hidden?: boolean
  is_hideable?: boolean
  options?: Array<{ label: string; value: unknown }> | (() => Array<{ label: string; value: unknown }>)
}

const props = withDefaults(
  defineProps<{
    config: Record<string, FilterConf>
    filterObject?: Record<string, unknown>
    filterPlaceholder?: string
  }>(),
  {
    filterObject: () => ({}),
    filterPlaceholder: 'Add filter',
  },
)

const emit = defineEmits<{
  'update:filterObject': [value: Record<string, unknown>]
}>()

const localHidden = ref<string[]>([])

const processedConfigs = computed<FilterConf[]>(() =>
  Object.values(props.config).filter((c) => !localHidden.value.includes(c.key)),
)

const hiddenFilters = computed(() =>
  Object.values(props.config)
    .filter((c) => localHidden.value.includes(c.key))
    .map((c) => ({ label: c.label, value: c.key })),
)

const showClearAll = computed(() =>
  Object.values(props.filterObject ?? {}).some((v) => v != null && (Array.isArray(v) ? v.length : true)),
)

function setFilter(key: string, value: unknown) {
  emit('update:filterObject', { ...props.filterObject, [key]: value })
}

function hideFilter(key: string) {
  if (!localHidden.value.includes(key)) localHidden.value.push(key)
  setFilter(key, undefined)
}

function updateVisibleFilters(option: { value: string }) {
  localHidden.value = localHidden.value.filter((k) => k !== option.value)
}

function clearAll() {
  emit('update:filterObject', {})
}

function resolveOptions(conf: FilterConf) {
  return typeof conf.options === 'function' ? conf.options() : (conf.options ?? [])
}
</script>

<template>
  <div class="km-filter-bar cluster gap-md" data-align="center" data-test="km-filter-bar">
    <KmGlyph name="filter" size="24px" />

    <div
      v-for="conf in processedConfigs"
      :key="conf.key"
      class="km-filter-bar__filter cluster gap-2xs"
      data-align="center"
    >
      <KmSelect
        :model-value="filterObject?.[conf.key]"
        :options="resolveOptions(conf)"
        :multiple="conf.multiple"
        :has-dropdown-search="conf.search"
        :permanent-placeholder="conf.label"
        use-chips
        @update:model-value="setFilter(conf.key, $event)"
      />
      <KmBtn
        v-if="conf.is_hideable"
        flat
        icon="close"
        icon-tone="muted"
        icon-size="14px"
        @click.stop.prevent="hideFilter(conf.key)"
      />
    </div>

    <KmSelectFlat
      v-if="hiddenFilters.length"
      :placeholder="filterPlaceholder"
      :options="hiddenFilters"
      :model-value="''"
      @update:model-value="updateVisibleFilters"
    />

    <KmBtn
      v-if="showClearAll"
      flat
      label="Clear all filters"
      @click="clearAll"
    />
  </div>
</template>
