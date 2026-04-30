<script setup lang="ts">
import type { NavigationMenuListProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { NavigationMenuList, useForwardProps } from 'reka-ui'

const props = defineProps<NavigationMenuListProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <NavigationMenuList
    class="ds-nav-menu__list"
    data-test="ds-navigation-menu-list"
    v-bind="forwardedProps"
  >
    <slot />
  </NavigationMenuList>
</template>
