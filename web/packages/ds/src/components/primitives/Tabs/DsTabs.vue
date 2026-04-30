<script lang="ts">
export default {
  name: 'DsTabs',
}
</script>

<script setup lang="ts">
/**
 * Tabs — accessible tabs with keyboard navigation.
 *
 *   <DsTabs v-model="active" :items="[{ value: 'a', label: 'A' }, …]">
 *     <template #panel-a>...</template>
 *     <template #panel-b>...</template>
 *   </DsTabs>
 *
 * Each panel slot is named `panel-<value>`.
 *
 * Triggers always render on a single row. When their combined width exceeds
 * the strip, the viewport scrolls horizontally and overlay chevron buttons
 * appear on the leading / trailing edges so the user can pan without a
 * trackpad. The native scrollbar is hidden — the chevrons are the affordance.
 */

import { TabsContent, TabsIndicator, TabsList, TabsRoot, TabsTrigger } from 'reka-ui'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

export interface DsTabItem {
  value: string
  label: string
  disabled?: boolean
}

const props = withDefaults(
  defineProps<{
    modelValue?: string
    items: DsTabItem[]
    orientation?: 'horizontal' | 'vertical'
    /** Visual variant. */
    variant?: 'underline' | 'pill' | 'segmented'
    renderPanels?: boolean
  }>(),
  {
    orientation: 'horizontal',
    variant: 'underline',
    renderPanels: true,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function handleModelUpdate(value: unknown) {
  emit('update:modelValue', String(value))
}

const viewportEl = ref<HTMLElement | null>(null)
const canScrollStart = ref(false)
const canScrollEnd = ref(false)
let resizeObserver: ResizeObserver | null = null

function updateScrollState() {
  const el = viewportEl.value
  if (!el || props.orientation === 'vertical') {
    canScrollStart.value = false
    canScrollEnd.value = false
    return
  }
  const overflow = el.scrollWidth - el.clientWidth
  if (overflow <= 1) {
    canScrollStart.value = false
    canScrollEnd.value = false
    return
  }
  canScrollStart.value = el.scrollLeft > 1
  canScrollEnd.value = el.scrollLeft < overflow - 1
}

function scrollByAmount(direction: -1 | 1) {
  const el = viewportEl.value
  if (!el) return
  const amount = Math.max(120, el.clientWidth * 0.6)
  el.scrollBy({ left: direction * amount, behavior: 'smooth' })
}

function attachObservers(el: HTMLElement) {
  el.addEventListener('scroll', updateScrollState, { passive: true })
  resizeObserver = new ResizeObserver(() => updateScrollState())
  resizeObserver.observe(el)
  for (const child of Array.from(el.querySelectorAll('[data-test="ds-tabs-trigger"]'))) {
    resizeObserver.observe(child)
  }
}

onMounted(async () => {
  await nextTick()
  if (viewportEl.value) {
    attachObservers(viewportEl.value)
    updateScrollState()
  }
})

onBeforeUnmount(() => {
  if (viewportEl.value) viewportEl.value.removeEventListener('scroll', updateScrollState)
  resizeObserver?.disconnect()
  resizeObserver = null
})

watch(
  () => props.items,
  async () => {
    await nextTick()
    if (viewportEl.value) {
      resizeObserver?.disconnect()
      attachObservers(viewportEl.value)
    }
    updateScrollState()
  },
  { deep: true },
)
</script>

<template>
  <!-- No tabs to render → no strip, no underline ghost-indicator, no border. -->
  <TabsRoot
    v-if="items.length > 0"
    :model-value="modelValue"
    :orientation="orientation"
    class="ds-tabs"
    :data-orientation="orientation"
    :data-variant="variant"
    data-test="ds-tabs"
    @update:model-value="handleModelUpdate"
  >
    <div
      class="ds-tabs__strip"
      data-test="ds-tabs-strip"
      :data-overflow-start="canScrollStart || undefined"
      :data-overflow-end="canScrollEnd || undefined"
    >
      <button
        v-show="canScrollStart"
        type="button"
        class="ds-tabs__scroll-btn"
        data-edge="start"
        data-test="ds-tabs-scroll-start"
        aria-label="Scroll tabs backward"
        tabindex="-1"
        @click="scrollByAmount(-1)"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" width="16" height="16"><path fill="currentColor" d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z" /></svg>
      </button>

      <div ref="viewportEl" class="ds-tabs__viewport">
        <TabsList class="ds-tabs__list">
          <TabsTrigger
            v-for="item in items"
            :key="item.value"
            :value="item.value"
            :disabled="item.disabled"
            class="ds-tabs__trigger"
            data-test="ds-tabs-trigger"
          >
            {{ item.label }}
          </TabsTrigger>
          <TabsIndicator v-if="variant === 'underline'" class="ds-tabs__indicator" />
        </TabsList>
      </div>

      <button
        v-show="canScrollEnd"
        type="button"
        class="ds-tabs__scroll-btn"
        data-edge="end"
        data-test="ds-tabs-scroll-end"
        aria-label="Scroll tabs forward"
        tabindex="-1"
        @click="scrollByAmount(1)"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" width="16" height="16"><path fill="currentColor" d="m8.59 16.59 1.41 1.41 6-6-6-6L8.59 7.41 13.17 12z" /></svg>
      </button>
    </div>

    <template v-if="renderPanels">
      <TabsContent
        v-for="item in items"
        :key="item.value"
        :value="item.value"
        class="ds-tabs__panel"
        data-test="ds-tabs-panel"
      >
        <slot :name="`panel-${item.value}`" :item="item" />
      </TabsContent>
    </template>
  </TabsRoot>
</template>

<style>
.ds-tabs { display: flex; flex-direction: column; gap: var(--ds-space-md); }
.ds-tabs[data-orientation='vertical'] { flex-direction: row; }

.ds-tabs__strip {
  position: relative;
  display: flex;
  align-items: stretch;
  min-inline-size: 0;
}
.ds-tabs[data-variant='underline'] .ds-tabs__strip {
  border-block-end: 1px solid var(--ds-color-border);
}

/* Horizontal scroll viewport: the list is wider than the strip, so we
 * scroll it. The native scrollbar is hidden because we render dedicated
 * chevron buttons instead — without that, the horizontal scrollbar steals
 * vertical space below the strip and pushes the indicator out of view. */
.ds-tabs__viewport {
  flex: 1 1 auto;
  min-inline-size: 0;
  overflow-block: hidden;
  overflow-inline: auto;
  overscroll-behavior: contain;
  scrollbar-width: none;
  scroll-behavior: smooth;
}
.ds-tabs__viewport::-webkit-scrollbar { display: none; }
.ds-tabs[data-orientation='vertical'] .ds-tabs__viewport {
  overflow-block: auto;
  overflow-inline: hidden;
  overscroll-behavior: contain;
}

.ds-tabs__list {
  position: relative;
  display: flex;
  gap: var(--ds-space-xs);
  align-items: center;
  flex-wrap: nowrap;
  inline-size: max-content;
  min-inline-size: 100%;
}
.ds-tabs[data-orientation='vertical'] .ds-tabs__list {
  flex-direction: column;
  inline-size: auto;
}
.ds-tabs[data-variant='segmented'] .ds-tabs__list {
  background: var(--ds-color-light);
  padding: var(--ds-space-2xs);
  border-radius: var(--ds-radius-md);
}

.ds-tabs__trigger {
  position: relative;
  flex: 0 0 auto;
  white-space: nowrap;
  padding: var(--ds-space-sm) var(--ds-space-md);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-text-grey);
  background: transparent;
  border: 0;
  cursor: pointer;
  border-radius: var(--ds-radius-sm);
  transition: color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-tabs__trigger:hover { color: var(--ds-color-black); }
.ds-tabs__trigger[data-state='active'] { color: var(--ds-color-primary); }
.ds-tabs__trigger:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: 2px; }
.ds-tabs__trigger[data-disabled] { color: var(--ds-color-placeholder); cursor: not-allowed; }

.ds-tabs[data-variant='pill'] .ds-tabs__trigger[data-state='active'] {
  background: var(--ds-color-primary-bg);
}
.ds-tabs[data-variant='segmented'] .ds-tabs__trigger[data-state='active'] {
  background: var(--ds-color-white);
  box-shadow: var(--ds-shadow-sm);
  color: var(--ds-color-black);
}

/* Reka's `<TabsIndicator>` measures the active trigger and writes its size
 * and offset into the two CSS variables below. The viewport clips vertical
 * overflow, so the indicator sits flush at the list's bottom edge (instead
 * of the historical -1px to overlap a now-removed list-level border). */
.ds-tabs__indicator {
  position: absolute;
  inset-block-end: 0;
  block-size: 2px;
  inline-size: var(--reka-tabs-indicator-size, 0);
  transform: translateX(var(--reka-tabs-indicator-position, 0));
  background: var(--ds-color-primary);
  border-radius: var(--ds-radius-full);
  transition:
    inline-size var(--ds-duration-base) var(--ds-ease-out),
    transform var(--ds-duration-base) var(--ds-ease-out);
}

/* Edge chevrons. Painted opaque with a soft shadow so triggers fade
 * underneath instead of showing through them mid-scroll. */
.ds-tabs__scroll-btn {
  position: absolute;
  inset-block: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 28px;
  background: var(--ds-color-panel-main-bg);
  border: 0;
  cursor: pointer;
  color: var(--ds-color-text-grey);
  z-index: 1;
  transition: color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-tabs__scroll-btn:hover { color: var(--ds-color-black); }
.ds-tabs__scroll-btn:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: -2px;
}
.ds-tabs__scroll-btn[data-edge='start'] {
  inset-inline-start: 0;
  box-shadow: 4px 0 6px -4px rgb(0 0 0 / 12%);
}
.ds-tabs__scroll-btn[data-edge='end'] {
  inset-inline-end: 0;
  box-shadow: -4px 0 6px -4px rgb(0 0 0 / 12%);
}

.ds-tabs__panel {
  outline: none;
  flex: 1 1 auto;
  min-block-size: 0;
}
</style>
