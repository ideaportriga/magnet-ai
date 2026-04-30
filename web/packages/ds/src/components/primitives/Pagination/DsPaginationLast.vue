<script setup lang="ts">
/**
 * PaginationLast — jump to the last page.
 */

import { reactiveOmit } from '@vueuse/core'
import { PaginationLast, type PaginationLastProps, useForwardProps } from 'reka-ui'
import type { DsButtonSize } from '../Button/DsButton.vue'

const props = withDefaults(
  defineProps<
    PaginationLastProps & {
      size?: DsButtonSize
    }
  >(),
  {
    size: 'md',
  },
)

const delegatedProps = reactiveOmit(props, 'size')
const forwarded = useForwardProps(delegatedProps)
</script>

<template>
  <PaginationLast
    v-bind="forwarded"
    class="ds-pagination__nav"
    :data-size="size"
    data-test="ds-pagination-last"
  >
    <slot>
      <span class="ds-pagination__nav-label">Last</span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M13 17l5-5-5-5M6 17l5-5-5-5"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </slot>
  </PaginationLast>
</template>
