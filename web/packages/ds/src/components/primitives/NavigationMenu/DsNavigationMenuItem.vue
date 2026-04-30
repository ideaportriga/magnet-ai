<script setup lang="ts">
import type { NavigationMenuItemProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { NavigationMenuItem } from 'reka-ui'

const props = defineProps<NavigationMenuItemProps>()
const delegatedProps = reactiveOmit(props, 'class' as never)
</script>

<template>
  <NavigationMenuItem
    class="ds-nav-menu__item"
    data-test="ds-navigation-menu-item"
    v-bind="delegatedProps"
  >
    <slot />
  </NavigationMenuItem>
</template>
