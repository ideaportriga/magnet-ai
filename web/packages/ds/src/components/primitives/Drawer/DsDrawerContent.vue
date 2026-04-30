<script setup lang="ts">
import type { DialogContentEmits, DialogContentProps } from 'reka-ui'
import { useForwardPropsEmits } from 'reka-ui'
import { DrawerContent, DrawerPortal } from 'vaul-vue'
import DsDrawerOverlay from './DsDrawerOverlay.vue'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps<DialogContentProps>()
const emits = defineEmits<DialogContentEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <DrawerPortal>
    <DsDrawerOverlay />
    <DrawerContent
      class="ds-drawer__content"
      data-test="ds-drawer-content"
      :aria-describedby="undefined"
      v-bind="{ ...$attrs, ...forwarded }"
    >
      <div class="ds-drawer__handle" aria-hidden="true" />
      <slot />
    </DrawerContent>
  </DrawerPortal>
</template>

<style>
.ds-drawer__content {
  position: fixed;
  inset-inline: 0;
  z-index: var(--ds-z-modal);
  display: flex;
  flex-direction: column;
  block-size: auto;
  background: var(--ds-color-background);
  color: var(--ds-color-black);
}
.ds-drawer__content[data-vaul-drawer-direction='top'] {
  inset-block-start: 0;
  margin-block-end: var(--ds-space-6xl);
  max-block-size: 80vb;
  border-end-start-radius: var(--ds-radius-lg);
  border-end-end-radius: var(--ds-radius-lg);
}
.ds-drawer__content[data-vaul-drawer-direction='bottom'] {
  inset-block-end: 0;
  margin-block-start: var(--ds-space-6xl);
  max-block-size: 80vb;
  border-start-start-radius: var(--ds-radius-lg);
  border-start-end-radius: var(--ds-radius-lg);
}
.ds-drawer__content[data-vaul-drawer-direction='right'] {
  inset-block: 0;
  inset-inline: auto 0;
  inline-size: 75%;
  max-inline-size: 24rem;
}
.ds-drawer__content[data-vaul-drawer-direction='left'] {
  inset-block: 0;
  inset-inline: 0 auto;
  inline-size: 75%;
  max-inline-size: 24rem;
}

.ds-drawer__handle {
  display: none;
  flex: none;
  inline-size: 100px;
  block-size: 8px;
  margin-inline: auto;
  margin-block-start: var(--ds-space-md);
  border-radius: var(--ds-radius-full);
  background: var(--ds-color-light);
}
.ds-drawer__content[data-vaul-drawer-direction='bottom'] .ds-drawer__handle {
  display: block;
}
</style>
