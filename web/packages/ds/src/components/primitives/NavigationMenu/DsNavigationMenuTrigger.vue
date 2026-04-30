<script setup lang="ts">
import type { NavigationMenuTriggerProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  NavigationMenuTrigger,
  useForwardProps,
} from 'reka-ui'

const props = defineProps<NavigationMenuTriggerProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <NavigationMenuTrigger
    class="ds-nav-menu__trigger"
    data-test="ds-navigation-menu-trigger"
    v-bind="forwardedProps"
  >
    <slot />
    <svg
      class="ds-nav-menu__chevron"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  </NavigationMenuTrigger>
</template>
