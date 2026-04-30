<script setup lang="ts">
/**
 * `<km-stepper>` — simple visual stepper. The legacy used `<km-stepper>` with
 * `<km-step>` children; the public surface is just `steps`, `stepper`
 * (active index), `vertical`. We render a flat, accessible nav.
 */

import { computed } from 'vue'
import KmGlyph from './KmGlyph.vue'

interface KmStep {
  description?: string
  label?: string
  /** Optional icon override; default chooses based on completion state. */
  icon?: string
}

const props = withDefaults(
  defineProps<{
    steps: KmStep[]
    /** Index of the active step (zero-based). */
    stepper?: number
    vertical?: boolean
  }>(),
  {
    stepper: 0,
    vertical: false,
  },
)

defineEmits<{
  'update:stepper': [value: number]
  click: [index: number]
}>()

function iconFor(index: number): string {
  if (props.steps[index]?.icon) return props.steps[index]!.icon!
  if (index === props.stepper) return 'edit'
  if (index < props.stepper) return 'check'
  return 'circle'
}

const isComplete = (index: number) => index < props.stepper
const isActive = (index: number) => index === props.stepper
</script>

<template>
  <ol
    class="km-stepper"
    :data-orientation="vertical ? 'vertical' : 'horizontal'"
    data-test="km-stepper"
  >
    <li
      v-for="(step, index) in steps"
      :key="index"
      class="km-stepper__step"
      :data-state="isComplete(index) ? 'done' : isActive(index) ? 'active' : 'todo'"
      @click="$emit('click', index)"
    >
      <span class="km-stepper__indicator" aria-hidden="true">
        <KmGlyph :name="iconFor(index)" size="16px" />
      </span>
      <span class="km-stepper__label">
        {{ step.label ?? step.description }}
      </span>
      <span v-if="index < steps.length - 1" class="km-stepper__connector" aria-hidden="true" />
    </li>
  </ol>
</template>

<style>
.km-stepper {
  list-style: "";
  margin: 0;
  padding: 0;
  display: flex;
  gap: var(--ds-space-md);
}
.km-stepper[data-orientation='vertical'] { flex-direction: column; }

.km-stepper__step {
  position: relative;
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  cursor: pointer;
}

.km-stepper__indicator {
  inline-size: 28px;
  block-size: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1.5px solid var(--ds-color-border-2);
  color: var(--ds-color-text-grey);
  background: var(--ds-color-white);
}
.km-stepper__step[data-state='active'] .km-stepper__indicator {
  border-color: var(--ds-color-primary);
  color: var(--ds-color-primary);
}
.km-stepper__step[data-state='done'] .km-stepper__indicator {
  background: var(--ds-color-primary);
  border-color: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}

.km-stepper__label { color: var(--ds-color-text-grey); }
.km-stepper__step[data-state='active'] .km-stepper__label { color: var(--ds-color-black); font-weight: var(--ds-font-weight-medium); }
.km-stepper__step[data-state='done'] .km-stepper__label { color: var(--ds-color-secondary-text); }

.km-stepper__connector {
  flex: 1 1 auto;
  block-size: 1px;
  background: var(--ds-color-border);
}
.km-stepper[data-orientation='vertical'] .km-stepper__connector {
  position: absolute;
  inset-inline-start: 14px;
  inset-block-start: 100%;
  inline-size: 1px;
  block-size: var(--ds-space-md);
}
</style>
