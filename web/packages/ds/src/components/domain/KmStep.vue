<script setup lang="ts">
/**
 * `<km-step name="…" :title="…">` — single step inside `<KmStepper>`. The
 * stepper provides the active step name; this component shows its body
 * only when the step is active.
 */
import { computed, inject } from 'vue'

// Optional injection: KmStepper, if it provides an active key, can register
// it under this Symbol. Falls back to always-visible if no parent.
const ACTIVE_KEY: symbol = Symbol.for('km-stepper-active')

const props = defineProps<{
  name: string
  title?: string
  icon?: string
}>()

const active = inject<string | null>(ACTIVE_KEY, null)
const visible = computed(() => !active || active === props.name)
</script>

<template>
  <section v-show="visible" class="km-step" :data-name="name" data-test="km-step">
    <header v-if="title || $slots.header" class="km-step__header">
      <span v-if="icon" class="km-step__icon"><i :class="icon" /></span>
      <h3 class="km-step__title">
        <slot name="header">{{ title }}</slot>
      </h3>
    </header>
    <div class="km-step__body">
      <slot />
    </div>
  </section>
</template>

<style>
.km-step__header {
  display: flex;
  gap: var(--ds-space-sm, 8px);
  align-items: center;
  margin-block-end: var(--ds-space-md, 12px);
}
.km-step__title {
  margin: 0;
  font-size: var(--ds-font-size-h4, 16px);
  font-weight: var(--ds-font-weight-medium, 500);
}
</style>
