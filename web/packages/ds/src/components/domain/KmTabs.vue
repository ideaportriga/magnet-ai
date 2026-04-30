<script setup lang="ts">
/**
 * `<km-tabs>` — tabs strip rendered via `<DsTabs>`.
 *
 * Public API preserved for ~342 admin call-sites:
 *   modelValue (v-model), variant — and any of the legacy Quasar layout
 *   props (align, dense, narrowIndicator, activeColor, indicatorColor,
 *   activeBgColor, noCaps, contentClass) which we accept and silently
 *   ignore so existing markup type-checks without changes.
 *
 * Two ways to specify items:
 *   1. New (preferred): `<km-tabs :items="..." />`
 *   2. Legacy slot: `<km-tabs><km-tab name="x" label="Y"/></km-tabs>`
 *      `<km-tab>` registers via provide/inject (see kmTabsContext.ts).
 *
 * Panels live in a sibling `<km-tab-panels>` block — `<km-tabs>` only
 * renders the trigger strip.
 */

import { computed, provide, ref, useSlots, watchEffect } from 'vue'
import DsTabs, { type DsTabItem } from '../primitives/Tabs/DsTabs.vue'
import { TabsContextKey } from './kmTabsContext'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    items?: DsTabItem[]
    variant?: 'underline' | 'pill' | 'segmented'
    /** Legacy Quasar surface — accepted, ignored. */
    align?: string
    dense?: boolean
    narrowIndicator?: boolean
    activeColor?: string
    indicatorColor?: string
    activeBgColor?: string
    noCaps?: boolean
    contentClass?: string
  }>(),
  {
    items: () => [],
    variant: 'underline',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

defineSlots<{
  default?: () => unknown
  [key: `panel-${string}`]: (props: { item: DsTabItem }) => unknown
}>()

/**
 * Forward call-site `class` / `style` / `data-*` to the visible DsTabs root.
 * Without this, Vue drops the attributes (KmTabs is a fragment with two
 * roots — DsTabs and the hidden registration span) and warns:
 *   "Extraneous non-props attributes (class) … could not be automatically
 *    inherited because component renders fragment …"
 *
 * Many legacy admin templates pass `class="bb-border full-width …"` to the
 * tab strip; that needs to land on DsTabs, not on the invisible span.
 */
defineOptions({ inheritAttrs: false })

const slotItems = ref<DsTabItem[]>([])
const slots = useSlots()

const allItems = computed<DsTabItem[]>(() => {
  if (props.items.length) return props.items
  return slotItems.value
})

const active = computed({
  get: () => props.modelValue ?? allItems.value[0]?.value,
  set: (next) => next != null && emit('update:modelValue', next),
})

provide(TabsContextKey, {
  active: computed(() => props.modelValue),
  registerTab: (item) => {
    if (!slotItems.value.find((i) => i.value === item.value)) slotItems.value.push(item)
  },
  unregisterTab: (value) => {
    slotItems.value = slotItems.value.filter((i) => i.value !== value)
  },
})

// When using legacy slot syntax, the actual panel content lives in named
// slots (`panel-<value>`). Forward them to DsTabs.
const panelSlotNames = computed(() => allItems.value.map((i) => `panel-${i.value}` as const))
const hasPanelSlots = computed(() => panelSlotNames.value.some((name) => Boolean(slots[name])))

watchEffect(() => {
  if (!active.value && allItems.value[0]?.value) {
    emit('update:modelValue', allItems.value[0]!.value)
  }
})
</script>

<template>
  <div class="km-tabs__root">
    <DsTabs
      v-bind="$attrs"
      :model-value="active"
      :items="allItems"
      :variant="variant"
      :render-panels="hasPanelSlots"
      :class="['km-tabs', $attrs.class]"
      data-test="km-tabs"
      @update:model-value="(value) => active = value"
    >
      <template
        v-for="name in panelSlotNames"
        #[name]="slotProps"
      >
        <slot :name="name" v-bind="slotProps" />
      </template>
    </DsTabs>

    <!-- Legacy slot path: register tabs via <km-tab> children. The slot itself
         is invisible — only its children's onMounted side-effect (registerTab)
         matters. -->
    <span style="display: none" aria-hidden="true">
      <slot />
    </span>
  </div>
</template>

<style>
.km-tabs__root {
  display: contents;
}

/* Legacy admin code expects the tabs strip to fill its row (it sits inside
 * a flex container with `bb-border full-width` siblings). DsTabs uses
 * column flex by default; relax it so the strip behaves like a horizontal
 * bar in either layout. Tabs that don't fit the row no longer wrap — DsTabs
 * scrolls horizontally and surfaces edge chevrons. */
.km-tabs {
  inline-size: 100%;
}
</style>
