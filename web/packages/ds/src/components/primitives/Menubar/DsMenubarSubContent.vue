<script setup lang="ts">
import type { MenubarSubContentEmits, MenubarSubContentProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  MenubarPortal,
  MenubarSubContent,
  useForwardPropsEmits,
} from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps<MenubarSubContentProps>()
const emits = defineEmits<MenubarSubContentEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <MenubarPortal>
    <MenubarSubContent
      class="ds-menu-content"
      data-test="ds-menubar-sub-content"
      v-bind="{ ...$attrs, ...forwarded }"
    >
      <slot />
    </MenubarSubContent>
  </MenubarPortal>
</template>
