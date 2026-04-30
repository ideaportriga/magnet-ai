<script setup lang="ts">
import type { MenubarRootEmits, MenubarRootProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  MenubarRoot,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<MenubarRootProps>()
const emits = defineEmits<MenubarRootEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <MenubarRoot
    v-slot="slotProps"
    class="ds-menubar"
    data-test="ds-menubar"
    v-bind="forwarded"
  >
    <slot v-bind="slotProps" />
  </MenubarRoot>
</template>

<style>
.ds-menubar {
  display: flex;
  block-size: 2.25rem;
  align-items: center;
  gap: var(--ds-space-2xs);
  padding: var(--ds-space-2xs);
  background: var(--ds-color-background, var(--ds-color-white));
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-sm);
}

.ds-menubar-trigger {
  display: inline-flex;
  align-items: center;
  padding-block: var(--ds-space-2xs);
  padding-inline: var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-sm);
  cursor: default;
  user-select: none;
  outline: none;
}
.ds-menubar-trigger[data-highlighted],
.ds-menubar-trigger[data-state='open'] {
  background: var(--ds-color-accent-bg, var(--ds-color-light));
  color: var(--ds-color-accent, var(--ds-color-black));
}
</style>
