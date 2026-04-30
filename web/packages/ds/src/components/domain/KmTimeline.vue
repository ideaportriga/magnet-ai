<script setup lang="ts">
/**
 * `<km-timeline>` — vertical list of `<km-timeline-entry>` items connected
 * by a leading rail. Replaces Quasar's `<q-timeline>`.
 */
withDefaults(
  defineProps<{
    color?: string
    layout?: 'dense' | 'comfortable' | 'loose'
  }>(),
  {
    color: 'var(--ds-color-primary)',
    layout: 'comfortable',
  },
)
</script>

<template>
  <ul
    class="km-timeline"
    :data-layout="layout"
    :style="{ '--km-timeline-color': color }"
    data-test="km-timeline"
  >
    <slot />
  </ul>
</template>

<style>
.km-timeline {
  list-style: "";
  margin: 0;
  padding: 0;
  position: relative;
  display: flex;
  flex-direction: column;
}
.km-timeline::before {
  content: '';
  position: absolute;
  inset-block: 0;
  inset-inline-start: 11px;
  inline-size: 2px;
  background: var(--km-timeline-color);
  opacity: 0.25;
}
.km-timeline[data-layout='dense']       { gap: var(--ds-space-sm, 8px); }
.km-timeline[data-layout='comfortable'] { gap: var(--ds-space-md, 12px); }
.km-timeline[data-layout='loose']       { gap: var(--ds-space-lg, 16px); }
</style>
