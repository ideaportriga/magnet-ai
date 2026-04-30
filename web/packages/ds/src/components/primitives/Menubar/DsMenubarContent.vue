<script setup lang="ts">
import type { MenubarContentProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  MenubarContent,
  MenubarPortal,
  useForwardProps,
} from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<MenubarContentProps>(),
  {
    align: 'start',
    alignOffset: -4,
    sideOffset: 8,
  },
)

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <MenubarPortal>
    <MenubarContent
      class="ds-menu-content"
      data-test="ds-menubar-content"
      v-bind="{ ...$attrs, ...forwardedProps }"
    >
      <slot />
    </MenubarContent>
  </MenubarPortal>
</template>
