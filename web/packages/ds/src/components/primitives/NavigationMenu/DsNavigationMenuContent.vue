<script setup lang="ts">
import type { NavigationMenuContentEmits, NavigationMenuContentProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  NavigationMenuContent,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<NavigationMenuContentProps>()
const emits = defineEmits<NavigationMenuContentEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <NavigationMenuContent
    class="ds-nav-menu__content"
    data-test="ds-navigation-menu-content"
    v-bind="forwarded"
  >
    <slot />
  </NavigationMenuContent>
</template>
