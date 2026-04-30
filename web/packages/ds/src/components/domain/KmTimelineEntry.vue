<script setup lang="ts">
/**
 * `<km-timeline-entry>` — single entry inside `<km-timeline>`. Renders an
 * icon node on the rail plus a title / subtitle / body block.
 */
import { computed } from 'vue'

export type KmTimelineEntryTone = 'brand' | 'success'

const toneColorMap: Record<KmTimelineEntryTone, string> = {
  brand: 'var(--ds-color-primary)',
  success: 'var(--ds-color-success-text)',
}

const props = withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    icon?: string
    tone?: KmTimelineEntryTone
    color?: string
  }>(),
  { title: '', subtitle: '', icon: '', color: '' },
)

const entryStyle = computed(() => {
  const color = props.color || (props.tone ? toneColorMap[props.tone] : '')
  return color ? { '--km-timeline-entry-color': color } : undefined
})
</script>

<template>
  <li
    class="km-timeline-entry"
    :style="entryStyle"
    data-test="km-timeline-entry"
  >
    <span class="km-timeline-entry__bullet">
      <i v-if="icon" :class="icon" />
    </span>
    <div class="km-timeline-entry__body">
      <header v-if="title || subtitle" class="km-timeline-entry__head">
        <h4 v-if="title" class="km-timeline-entry__title">{{ title }}</h4>
        <p v-if="subtitle" class="km-timeline-entry__subtitle">{{ subtitle }}</p>
      </header>
      <div class="km-timeline-entry__content">
        <slot />
      </div>
    </div>
  </li>
</template>

<style>
.km-timeline-entry {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: var(--ds-space-sm, 8px);
  align-items: start;
  position: relative;
}
.km-timeline-entry__bullet {
  inline-size: 24px;
  block-size: 24px;
  border-radius: 50%;
  background: var(--km-timeline-entry-color, var(--km-timeline-color, var(--ds-color-primary)));
  color: var(--ds-color-static-white);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex: none;
  z-index: 1;
}
.km-timeline-entry__body { min-inline-size: 0; }
.km-timeline-entry__head { margin-block-end: var(--ds-space-xs, 4px); }
.km-timeline-entry__title  { margin: 0; font-size: var(--ds-font-size-h4, 16px); font-weight: var(--ds-font-weight-medium, 500); }
.km-timeline-entry__subtitle { margin: 0; font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); }
</style>
