<script setup lang="ts">
/**
 * `<km-filter-bar>` — filter strip used in admin lists.
 *
 * Stores user selections as a flat map of *raw* values (not full option
 * objects) keyed by `config[key].key`, and emits them via
 * `update:filterObject`. Consumers that need MongoDB-style or
 * camelCase-flat query strings transform on their side.
 *
 * Built-in features:
 *  - `default` seeding from each config entry on mount, so consumers
 *    that key a fetch off `update:filterObject` see the initial set
 *    without user interaction
 *  - `setFilter` / `setFilters` / `clearFilter` exposed via `defineExpose`
 *    for ref-based drill-down from KPI cards. They accept either raw
 *    values or `{label, value}` option objects (auto-unwrapped).
 *  - `persistent` + `persistent-key` — round-trip the filter via
 *    sessionStorage so navigation preserves the bar state.
 *  - `timePeriod` filter type with built-in ISO duration presets.
 */

import { computed, onMounted, watch } from 'vue'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'
import KmSelect from './KmSelect.vue'
import KmSelectFlat from './KmSelectFlat.vue'

interface FilterOption {
  label: string
  value: unknown
}

interface FilterConf {
  key: string
  label: string
  type?: 'timePeriod' | 'search' | 'component' | string
  field?: string
  multiple?: boolean
  search?: boolean
  is_hidden?: boolean
  is_hideable?: boolean
  default?: unknown
  customLogic?: (value: unknown) => unknown
  options?: FilterOption[] | (() => FilterOption[])
}

const props = withDefaults(
  defineProps<{
    config: Record<string, FilterConf>
    filterObject?: Record<string, unknown>
    filterPlaceholder?: string
    persistent?: boolean
    persistentKey?: string
    /** Reserved — transformation happens on the consumer side. */
    outputFormat?: 'raw' | 'mongodb' | 'sql'
  }>(),
  {
    filterObject: () => ({}),
    filterPlaceholder: 'Add filter',
    persistent: false,
    persistentKey: '',
    outputFormat: 'raw',
  },
)

const emit = defineEmits<{
  'update:filterObject': [value: Record<string, unknown>]
  'update:config': [value: Record<string, FilterConf>]
}>()

const PRESET_TIME_PERIODS: FilterOption[] = [
  { label: 'Last 15 minutes', value: 'PT15M' },
  { label: 'Last 30 minutes', value: 'PT30M' },
  { label: 'Last 1 hour', value: 'PT1H' },
  { label: 'Last 6 hours', value: 'PT6H' },
  { label: 'Last 12 hours', value: 'PT12H' },
  { label: 'Last 24 hours', value: 'P1D' },
  { label: 'Last 3 days', value: 'P3D' },
  { label: 'Last 5 days', value: 'P5D' },
  { label: 'Last 7 days', value: 'P7D' },
]

function resolveOptions(conf: FilterConf): FilterOption[] {
  if (conf.type === 'timePeriod' && !conf.options) return PRESET_TIME_PERIODS
  if (typeof conf.options === 'function') return conf.options()
  return (conf.options as FilterOption[] | undefined) ?? []
}

const processedConfigs = computed<FilterConf[]>(() =>
  Object.values(props.config).map((c) => ({
    ...c,
    options: resolveOptions(c),
  })),
)

const visibleConfigs = computed<FilterConf[]>(() =>
  processedConfigs.value.filter((c) => !c.is_hidden),
)

const hiddenFilters = computed(() =>
  processedConfigs.value
    .filter((c) => c.is_hidden && c.is_hideable !== false)
    .map((c) => ({ label: c.label, value: c.key })),
)

const showClearAll = computed(() =>
  Object.values(props.filterObject ?? {}).some((v) => {
    if (v == null) return false
    if (Array.isArray(v)) return v.length > 0
    if (typeof v === 'object') return Object.keys(v as object).length > 0
    return true
  }),
)

function unwrap(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((v) => unwrap(v))
  }
  if (
    value
    && typeof value === 'object'
    && 'value' in (value as Record<string, unknown>)
    && 'label' in (value as Record<string, unknown>)
  ) {
    return (value as { value: unknown }).value
  }
  return value
}

function emitFilter(next: Record<string, unknown>) {
  emit('update:filterObject', next)
  if (props.persistent && props.persistentKey) {
    try {
      sessionStorage.setItem(props.persistentKey, JSON.stringify(next))
    } catch {
      // ignore quota / serialization errors
    }
  }
}

function setFilter(key: string, value: unknown) {
  emitFilter({ ...props.filterObject, [key]: unwrap(value) })
}

function setFilters(values: Record<string, unknown>) {
  const next: Record<string, unknown> = { ...props.filterObject }
  for (const [k, v] of Object.entries(values)) {
    next[k] = unwrap(v)
  }
  emitFilter(next)
}

function clearFilter(keys?: string | string[]) {
  if (keys == null || (Array.isArray(keys) && keys.length === 0)) {
    emitFilter({})
    return
  }
  const list = Array.isArray(keys) ? keys : [keys]
  const next: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(props.filterObject ?? {})) {
    if (!list.includes(k)) next[k] = v
  }
  emitFilter(next)
}

function hideFilter(key: string) {
  emit('update:config', {
    ...props.config,
    [key]: { ...props.config[key], is_hidden: true },
  })
  setFilter(key, undefined)
}

function updateVisibleFilters(option: { value: string }) {
  emit('update:config', {
    ...props.config,
    [option.value]: { ...props.config[option.value], is_hidden: false },
  })
}

function clearAll() {
  emitFilter({})
}

watch(
  () => props.filterObject,
  (val) => {
    if (props.persistent && props.persistentKey) {
      try {
        sessionStorage.setItem(props.persistentKey, JSON.stringify(val ?? {}))
      } catch {
        // ignore
      }
    }
  },
  { deep: true },
)

onMounted(() => {
  let restored = false
  if (props.persistent && props.persistentKey) {
    try {
      const stored = sessionStorage.getItem(props.persistentKey)
      if (stored) {
        emit('update:filterObject', JSON.parse(stored) as Record<string, unknown>)
        restored = true
      }
    } catch {
      // ignore — fall through to defaults
    }
  }
  if (restored) return

  const seeded: Record<string, unknown> = { ...(props.filterObject ?? {}) }
  let hasSeed = false
  for (const conf of Object.values(props.config)) {
    if (conf.is_hidden) continue
    if (seeded[conf.key] !== undefined && seeded[conf.key] !== null) continue
    if (conf.default === undefined) continue
    seeded[conf.key] = conf.default
    hasSeed = true
  }

  // Always emit at least once so consumers' watchers see the initial set
  // (defaults included). Emitting an empty `{}` still gives the parent a
  // fresh reference, so a deep watch on `filterObject` can fire.
  if (hasSeed) emitFilter(seeded)
  else emit('update:filterObject', { ...(props.filterObject ?? {}) })
})

defineExpose({ setFilter, setFilters, clearFilter })
</script>

<template>
  <div class="km-filter-bar cluster gap-md" data-align="center" data-test="km-filter-bar">
    <KmGlyph name="filter" size="24px" />

    <div
      v-for="conf in visibleConfigs"
      :key="conf.key"
      class="km-filter-bar__filter cluster gap-2xs"
      data-align="center"
    >
      <KmSelect
        :model-value="filterObject?.[conf.key]"
        :options="(conf.options as FilterOption[])"
        :multiple="conf.multiple"
        :has-dropdown-search="conf.search"
        :permanent-placeholder="conf.label"
        emit-value
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
