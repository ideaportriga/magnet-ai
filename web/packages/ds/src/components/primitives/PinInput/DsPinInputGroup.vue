<script setup lang="ts">
/**
 * PinInputGroup — visually groups consecutive PinInputInput slots so they
 * read as one continuous control (rounded corners merge across the group).
 */
import type { PrimitiveProps } from 'reka-ui'
import { Primitive, useForwardProps } from 'reka-ui'

const props = defineProps<PrimitiveProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <Primitive
    v-bind="forwarded"
    class="ds-pin-input__group"
    data-test="ds-pin-input-group"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-pin-input__group {
  display: flex;
  align-items: center;
}
</style>
