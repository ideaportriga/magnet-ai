<script setup lang="ts">
/**
 * `<km-btn-dropdown>` — a button that opens a dropdown menu of slot
 * content on click. Replaces Quasar's `<q-btn-dropdown>`. Built on Reka's
 * Popover.
 */
import { ref } from 'vue'
import { PopoverContent, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui'
import KmBtn from './KmBtn.vue'
import type { KmBtnTone } from './KmBtn.vue'

withDefaults(
  defineProps<{
    label?: string
    icon?: string
    size?: 'xs' | 'sm' | 'md' | 'lg'
    tone?: KmBtnTone
    flat?: boolean
    disable?: boolean
  }>(),
  {
    label: '',
    icon: '',
    size: 'md',
    tone: undefined,
    flat: false,
    disable: false,
  },
)

defineEmits<{ click: [] }>()

const open = ref(false)
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <KmBtn
        class="km-btn-dropdown"
        :label="label"
        :icon="icon"
        :size="size"
        :tone="tone"
        :flat="flat"
        :disable="disable"
        :aria-expanded="open ? 'true' : 'false'"
      >
        <slot name="label">{{ label }}</slot>
        <span class="km-btn-dropdown__chevron" aria-hidden="true">▾</span>
      </KmBtn>
    </PopoverTrigger>
    <PopoverPortal>
      <PopoverContent
        class="km-btn-dropdown__menu"
        side="bottom"
        align="start"
        :side-offset="4"
        @click="open = false"
      >
        <slot />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style>
.km-btn-dropdown__chevron {
  margin-inline-start: var(--ds-space-2xs, 4px);
  font-size: 0.8em;
  opacity: 0.7;
}
.km-btn-dropdown__menu {
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md, 8px);
  box-shadow: var(--ds-shadow-lg);
  padding: var(--ds-space-2xs, 4px);
  min-inline-size: 160px;
  z-index: var(--ds-z-overlay, 2000);
}
</style>
