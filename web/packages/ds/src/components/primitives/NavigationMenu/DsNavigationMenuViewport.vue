<script setup lang="ts">
import type { NavigationMenuViewportProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  NavigationMenuViewport,
  useForwardProps,
} from 'reka-ui'

const props = defineProps<NavigationMenuViewportProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <div class="ds-nav-menu__viewport-host">
    <NavigationMenuViewport
      class="ds-nav-menu__viewport"
      data-test="ds-navigation-menu-viewport"
      v-bind="forwardedProps"
    />
  </div>
</template>
