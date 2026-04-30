<script setup lang="ts">
/**
 * `<km-expansion-item>` — single collapsible panel. Drop-in for the legacy
 * Quasar `<q-expansion-item>`. We render Reka UI's `AccordionRoot`/
 * `AccordionItem` directly with the `.ds-accordion*` classes from
 * `<DsAccordion>` — using `<DsAccordion>` itself would force the contents
 * through a named slot keyed on `value` and would lose access to the
 * legacy `headerClass` / `headerStyle` / `expandIcon` knobs.
 *
 * Public API (preserved): `label, icon, expandIcon, headerClass,
 * headerStyle, modelValue, defaultOpened, dense`. Slots: `header` (custom
 * header content), default (body).
 */

import {
  AccordionContent,
  AccordionHeader,
  AccordionItem,
  AccordionRoot,
  AccordionTrigger,
} from 'reka-ui'
import { computed, ref, watchEffect } from 'vue'
import KmGlyph from './KmGlyph.vue'

const props = withDefaults(
  defineProps<{
    label?: string
    icon?: string
    /** Icon shown on the expand toggle (replaces the default chevron). */
    expandIcon?: string
    /** Class applied to the header trigger. */
    headerClass?: string
    /** Inline style applied to the header trigger. */
    headerStyle?: string | Record<string, string>
    modelValue?: boolean
    defaultOpened?: boolean
    dense?: boolean
  }>(),
  {
    label: '',
    icon: '',
    expandIcon: '',
    headerClass: '',
    modelValue: undefined,
    defaultOpened: false,
    dense: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const VALUE = 'item'
const internal = ref<string | undefined>(props.defaultOpened ? VALUE : undefined)
watchEffect(() => {
  if (props.modelValue !== undefined) internal.value = props.modelValue ? VALUE : undefined
})

const value = computed<string | undefined>({
  get: () => internal.value,
  set: (v) => {
    internal.value = v
    if (props.modelValue !== undefined) emit('update:modelValue', v === VALUE)
  },
})
</script>

<template>
  <AccordionRoot
    type="single"
    collapsible
    :model-value="value"
    class="ds-accordion km-expansion-item"
    :data-dense="dense ? 'true' : undefined"
    data-test="km-expansion-item"
    @update:model-value="value = ($event as string | undefined)"
  >
    <AccordionItem :value="VALUE" class="ds-accordion__item km-expansion-item__item">
      <AccordionHeader class="ds-accordion__header km-expansion-item__header">
        <AccordionTrigger
          :class="['ds-accordion__trigger', 'km-expansion-item__trigger', headerClass]"
          :style="headerStyle"
          data-test="km-expansion-item-trigger"
        >
          <slot name="header">
            <KmGlyph v-if="icon" :name="icon" size="18px" />
            <span class="km-expansion-item__label">{{ label }}</span>
          </slot>
          <KmGlyph
            v-if="expandIcon"
            :name="expandIcon"
            size="14px"
            class="ds-accordion__chevron km-expansion-item__chevron"
          />
          <svg
            v-else
            class="ds-accordion__chevron km-expansion-item__chevron"
            width="14"
            height="14"
            viewBox="0 0 14 14"
            aria-hidden="true"
          >
            <path d="M3 5 L7 9 L11 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </AccordionTrigger>
      </AccordionHeader>
      <AccordionContent class="ds-accordion__content km-expansion-item__content">
        <div class="km-expansion-item__content-inner">
          <slot />
        </div>
      </AccordionContent>
    </AccordionItem>
  </AccordionRoot>
</template>

<style>
/* Override the default DsAccordion item border so KmExpansionItem can be
 * embedded inside surfaces that paint their own border. */
.km-expansion-item .ds-accordion__item { border: 0; border-radius: 0; }

.km-expansion-item__trigger {
  flex: 1 1 auto;
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm, 8px);
  inline-size: 100%;
  background: transparent;
  border: 0;
  cursor: pointer;
  text-align: start;
  font: inherit;
  color: inherit;
}
.km-expansion-item__trigger:hover { background: var(--ds-color-light); }
.km-expansion-item[data-dense='true'] .km-expansion-item__trigger {
  padding: var(--ds-space-xs, 4px) var(--ds-space-sm, 8px);
}

.km-expansion-item__label { flex: 1 1 auto; min-inline-size: 0; }
.km-expansion-item__chevron { flex: none; }

.km-expansion-item__content-inner { padding: var(--ds-space-md, 12px); border-block-start: 0; }
.km-expansion-item .ds-accordion__content-inner { border-block-start: 0; padding: 0; }
</style>
