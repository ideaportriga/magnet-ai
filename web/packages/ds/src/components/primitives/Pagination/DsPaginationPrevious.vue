<script setup lang="ts">
/**
 * PaginationPrevious — jump back one page.
 */

import { reactiveOmit } from '@vueuse/core'
import { PaginationPrev, type PaginationPrevProps, useForwardProps } from 'reka-ui'
import type { DsButtonSize } from '../Button/DsButton.vue'

const props = withDefaults(
  defineProps<
    PaginationPrevProps & {
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
  <PaginationPrev
    v-bind="forwarded"
    class="ds-pagination__nav"
    :data-size="size"
    data-test="ds-pagination-previous"
  >
    <slot>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M15 18l-6-6 6-6"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <span class="ds-pagination__nav-label">Previous</span>
    </slot>
  </PaginationPrev>
</template>
