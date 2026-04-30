<script setup lang="ts">
import type { NavigationMenuLinkEmits, NavigationMenuLinkProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  NavigationMenuLink,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<NavigationMenuLinkProps>()
const emits = defineEmits<NavigationMenuLinkEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <NavigationMenuLink
    class="ds-nav-menu__link"
    data-test="ds-navigation-menu-link"
    v-bind="forwarded"
  >
    <slot />
  </NavigationMenuLink>
</template>
