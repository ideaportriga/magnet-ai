<script setup lang="ts">
/**
 * `<km-btn-toggle v-model="value" :options="…">` — segmented-control style
 * group of toggle buttons. Replaces Quasar's `<q-btn-toggle>`.
 */
import KmGlyph from './KmGlyph.vue'

export interface KmBtnToggleOption {
  label: string
  value: string | number | boolean
  /** Icon name accepted by `KmGlyph` (Material, `o_*` outlined, or FA class). */
  icon?: string
  disable?: boolean
}

const props = defineProps<{
  modelValue?: string | number | boolean | null
  options: KmBtnToggleOption[]
  spread?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | number | boolean | null]
}>()

function select(opt: KmBtnToggleOption) {
  if (opt.disable) return
  emit('update:modelValue', opt.value)
}
</script>

<template>
  <div
    class="km-btn-toggle"
    :data-spread="spread ? 'true' : undefined"
    role="group"
    data-test="km-btn-toggle"
  >
    <button
      v-for="opt in options"
      :key="String(opt.value)"
      type="button"
      class="km-btn-toggle__btn"
      :data-active="modelValue === opt.value ? 'true' : undefined"
      :disabled="opt.disable"
      @click="select(opt)"
    >
      <KmGlyph v-if="opt.icon" class="km-btn-toggle__icon" :name="opt.icon" size="1em" />
      <span>{{ opt.label }}</span>
    </button>
  </div>
</template>

<style>
.km-btn-toggle {
  display: inline-flex;
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md, 8px);
  overflow: hidden;
}
.km-btn-toggle[data-spread='true'] { display: flex; inline-size: 100%; }
.km-btn-toggle[data-spread='true'] .km-btn-toggle__btn { flex: 1 1 0; }
.km-btn-toggle__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-xs, 4px);
  padding: var(--ds-space-xs, 4px) var(--ds-space-md, 12px);
  background: transparent;
  border: 0;
  border-inline-end: 1px solid var(--ds-color-border);
  cursor: pointer;
  font: inherit;
  color: inherit;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-btn-toggle__btn:last-child { border-inline-end: 0; }
.km-btn-toggle__btn:hover:not([disabled]) { background: var(--ds-color-light); }
.km-btn-toggle__btn[data-active='true'] {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}
.km-btn-toggle__btn[disabled] { opacity: 0.5; cursor: not-allowed; }
.km-btn-toggle__icon { flex: none; }
</style>
