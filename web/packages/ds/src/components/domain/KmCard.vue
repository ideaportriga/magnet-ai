<script setup lang="ts">
/**
 * `<km-card>` — generic content card. Renders over `<DsCard>` (and its
 * sub-components) while preserving the legacy two render modes:
 *
 *   1. Slot mode (default) — `<km-card>…</km-card>` renders a card surface
 *      with the children flowing inside. Used by list cards that compose
 *      their own header/actions/footer (Agents/Mcp/etc).
 *
 *   2. Feature mode — when the legacy `icon` / `label` / `description`
 *      props are passed AND the default slot is empty, render the
 *      "Configure your X" feature card layout (used in Agents/overview).
 *
 * Public API (preserved): `icon, label, description, actionLabel, qty,
 * bordered, flat`, plus `header` and `footer` slots that map onto
 * `<DsCardHeader>` / `<DsCardFooter>`.
 */

import { computed, ref, useSlots } from 'vue'
import DsCard from '../primitives/Card/DsCard.vue'
import DsCardHeader from '../primitives/Card/DsCardHeader.vue'
import DsCardContent from '../primitives/Card/DsCardContent.vue'
import DsCardFooter from '../primitives/Card/DsCardFooter.vue'
import KmGlyph from './KmGlyph.vue'

const props = withDefaults(
  defineProps<{
    icon?: string
    label?: string
    description?: string
    actionLabel?: string
    qty?: number
    bordered?: boolean
    flat?: boolean
  }>(),
  {
    icon: '',
    label: '',
    description: '',
    actionLabel: '',
    qty: 0,
    bordered: false,
    flat: false,
  },
)

defineEmits<{
  click: []
}>()

const slots = useSlots()
const hasDefault = computed(() => !!slots.default)
const hasHeader = computed(() => !!slots.header)
const hasFooter = computed(() => !!slots.footer)
const isFeature = computed(() => !hasDefault.value && (!!props.label || !!props.icon))

const hover = ref(false)
</script>

<template>
  <DsCard
    class="km-card"
    :data-mode="isFeature ? 'feature' : 'content'"
    :data-bordered="bordered ? 'true' : undefined"
    :data-flat="flat ? 'true' : undefined"
    data-test="km-card"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
    @click="$emit('click')"
  >
    <DsCardHeader v-if="hasHeader" class="km-card__header">
      <slot name="header" />
    </DsCardHeader>

    <slot v-if="hasDefault" />

    <template v-else-if="isFeature">
      <KmGlyph v-if="icon" :name="icon" size="16px" tone="brand" />
      <div class="km-card__head">
        <span v-if="qty" class="km-card__qty">{{ qty }}</span>
        <span class="km-card__label">{{ label }}</span>
      </div>
      <p v-if="description" class="km-card__description">{{ description }}</p>
      <button
        v-if="hover && actionLabel"
        class="km-card__action"
        type="button"
      >
        {{ actionLabel }}
      </button>
    </template>

    <DsCardFooter v-if="hasFooter" class="km-card__footer">
      <slot name="footer" />
    </DsCardFooter>
  </DsCard>
</template>

<style>
/* The legacy <km-card> contract is roomier than DsCard's default surface
 * (which adds 24px vertical padding + 24px gap between children). Reset
 * the gaps for content mode and keep DsCard's nice border-radius / shadow.
 * Selector intentionally doubles `.km-card.km-card` so it has higher
 * specificity than `.ds-card` (`0,2,0` vs `0,1,0`); without that, source
 * order in the bundle decides whether DsCard's padding/gap leaks through,
 * showing up as phantom whitespace above / below `<km-card>` content. */
.km-card.km-card {
  background: var(--ds-color-panel-main-bg, var(--ds-color-white));
  border-radius: var(--ds-radius-md, 8px);
  border: 0;
  box-shadow: none;
  padding-block: 0;
  gap: 0;
  transition: background var(--ds-duration-fast, 150ms) var(--ds-ease-out);
}
.km-card.km-card[data-bordered='true'] {
  border: 1px solid var(--ds-color-border);
}
.km-card.km-card[data-flat='true'] {
  box-shadow: none;
}

.km-card[data-mode='feature'] {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ds-space-sm, 8px);
  min-block-size: 182px;
  padding: var(--ds-space-lg, 16px) var(--ds-space-md, 12px);
  text-align: center;
  cursor: pointer;
}
.km-card[data-mode='feature']:hover {
  background: var(--ds-color-primary-bg);
}

.km-card__head {
  display: inline-flex;
  gap: var(--ds-space-2xs, 4px);
  align-items: center;
  justify-content: center;
}
.km-card__qty {
  font-size: var(--ds-font-size-body);
  font-weight: var(--ds-font-weight-semibold, 600);
  color: var(--ds-color-primary);
}
.km-card__label {
  font-size: var(--ds-font-size-body);
  font-weight: var(--ds-font-weight-semibold, 600);
  color: var(--ds-color-black);
}
.km-card__description {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  margin: 0;
}
.km-card__action {
  align-self: stretch;
  padding: var(--ds-space-xs, 4px) var(--ds-space-md, 12px);
  background: var(--ds-color-btn-primary-bg, var(--ds-color-primary));
  color: var(--ds-color-btn-primary-text, var(--ds-color-static-white));
  border: 0;
  border-radius: var(--ds-radius-md, 8px);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium, 500);
  cursor: pointer;
}
.km-card__action:hover {
  background: var(--ds-color-btn-primary-hover-bg);
}
</style>
