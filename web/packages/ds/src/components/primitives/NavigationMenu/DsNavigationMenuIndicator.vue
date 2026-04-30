<script setup lang="ts">
import type { NavigationMenuIndicatorProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { NavigationMenuIndicator, useForwardProps } from 'reka-ui'

const props = defineProps<NavigationMenuIndicatorProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <NavigationMenuIndicator
    class="ds-nav-menu__indicator"
    data-test="ds-navigation-menu-indicator"
    v-bind="forwardedProps"
  >
    <div class="ds-nav-menu__indicator-arrow" />
  </NavigationMenuIndicator>
</template>
