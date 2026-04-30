<script setup lang="ts">
/**
 * Accordion — expandable items. Replaces Quasar's `<km-expansion-item>`.
 * `type="single"` means at most one panel open at a time; `"multiple"`
 * allows several to be open.
 *
 *   <DsAccordion :items="items" type="single" :default-value="'general'">
 *     <template #content-general>...</template>
 *   </DsAccordion>
 */

import {
  AccordionContent,
  AccordionHeader,
  AccordionItem,
  AccordionRoot,
  AccordionTrigger,
} from 'reka-ui'

export interface DsAccordionItem {
  value: string
  label: string
  disabled?: boolean
}

withDefaults(
  defineProps<{
    items: DsAccordionItem[]
    /** `single` opens at most one panel; `multiple` allows several. */
    type?: 'single' | 'multiple'
    modelValue?: string | string[]
    defaultValue?: string | string[]
    collapsible?: boolean
  }>(),
  {
    type: 'single',
    collapsible: true,
  },
)

defineEmits<{
  'update:modelValue': [value: string | string[]]
}>()
</script>

<template>
  <AccordionRoot
    :type="type"
    :model-value="modelValue"
    :default-value="defaultValue"
    :collapsible="type === 'single' ? collapsible : undefined"
    class="ds-accordion stack"
    data-gap="2xs"
    data-test="ds-accordion"
    @update:model-value="$emit('update:modelValue', $event as string | string[])"
  >
    <AccordionItem
      v-for="item in items"
      :key="item.value"
      :value="item.value"
      :disabled="item.disabled"
      class="ds-accordion__item"
      data-test="ds-accordion-item"
    >
      <AccordionHeader class="ds-accordion__header">
        <AccordionTrigger class="ds-accordion__trigger" data-test="ds-accordion-trigger">
          <span>{{ item.label }}</span>
          <svg class="ds-accordion__chevron" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
            <path d="M3 5 L7 9 L11 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </AccordionTrigger>
      </AccordionHeader>

      <AccordionContent class="ds-accordion__content">
        <div class="ds-accordion__content-inner">
          <slot :name="`content-${item.value}`" :item="item" />
        </div>
      </AccordionContent>
    </AccordionItem>
  </AccordionRoot>
</template>

<style>
.ds-accordion__item {
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  overflow: hidden;
}

.ds-accordion__header { all: unset; display: flex; }
.ds-accordion__trigger {
  flex: 1 1 auto;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-md);
  padding: var(--ds-space-sm) var(--ds-space-md);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
  background: transparent;
  border: 0;
  cursor: pointer;
  text-align: start;
}
.ds-accordion__trigger:hover { background: var(--ds-color-light); }
.ds-accordion__trigger:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: -2px; }

.ds-accordion__chevron {
  flex: none;
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-accordion__trigger[data-state='open'] .ds-accordion__chevron { transform: rotate(180deg); }

.ds-accordion__content {
  overflow: hidden;
}
.ds-accordion__content[data-state='open'] {
  animation: ds-collapse-down var(--ds-duration-base) var(--ds-ease-out);
}
.ds-accordion__content[data-state='closed'] {
  animation: ds-collapse-up var(--ds-duration-fast) var(--ds-ease-in);
}
.ds-accordion__content-inner {
  padding: var(--ds-space-md);
  border-block-start: 1px solid var(--ds-color-border);
}

</style>
