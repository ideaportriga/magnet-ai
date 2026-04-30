<script setup lang="ts">
/**
 * PaginationNext — jump forward one page.
 */

import { reactiveOmit } from '@vueuse/core'
import { PaginationNext, type PaginationNextProps, useForwardProps } from 'reka-ui'
import type { DsButtonSize } from '../Button/DsButton.vue'

const props = withDefaults(
  defineProps<
    PaginationNextProps & {
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
  <PaginationNext
    v-bind="forwarded"
    class="ds-pagination__nav"
    :data-size="size"
    data-test="ds-pagination-next"
  >
    <slot>
      <span class="ds-pagination__nav-label">Next</span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M9 18l6-6-6-6"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </slot>
  </PaginationNext>
</template>
