<script setup lang="ts">
/**
 * Scroll area — accessible custom scrollbars. Replaces Quasar's
 * `<km-scroll-area>`.
 */

import { ScrollAreaCorner, ScrollAreaRoot, ScrollAreaScrollbar, ScrollAreaThumb, ScrollAreaViewport } from 'reka-ui'

withDefaults(
  defineProps<{
    /** When the scrollbar appears: 'hover' (default), 'auto', 'always', 'scroll'. */
    type?: 'hover' | 'auto' | 'always' | 'scroll'
    /** Hover-out delay before the scrollbar fades, in ms. */
    scrollHideDelay?: number
  }>(),
  {
    type: 'hover',
    scrollHideDelay: 600,
  },
)
</script>

<template>
  <ScrollAreaRoot :type="type" :scroll-hide-delay="scrollHideDelay" class="ds-scroll-area">
    <ScrollAreaViewport class="ds-scroll-area__viewport">
      <slot />
    </ScrollAreaViewport>

    <ScrollAreaScrollbar class="ds-scroll-area__bar" orientation="vertical">
      <ScrollAreaThumb class="ds-scroll-area__thumb" />
    </ScrollAreaScrollbar>
    <ScrollAreaScrollbar class="ds-scroll-area__bar" orientation="horizontal">
      <ScrollAreaThumb class="ds-scroll-area__thumb" />
    </ScrollAreaScrollbar>
    <ScrollAreaCorner class="ds-scroll-area__corner" />
  </ScrollAreaRoot>
</template>

<style>
.ds-scroll-area {
  position: relative;
  inline-size: 100%;
  block-size: 100%;
  overflow: hidden;
}
.ds-scroll-area__viewport {
  inline-size: 100%;
  block-size: 100%;
  border-radius: inherit;
}
.ds-scroll-area__bar {
  display: flex;
  user-select: none;
  touch-action: none;
  padding: 2px;
  background: transparent;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-scroll-area__bar:hover { background: rgba(0, 0, 0, 0.05); }
.ds-scroll-area__bar[data-orientation='vertical']   { inline-size: 10px; }
.ds-scroll-area__bar[data-orientation='horizontal'] { flex-direction: column; block-size: 10px; }

.ds-scroll-area__thumb {
  flex: 1;
  position: relative;
  background: var(--ds-color-border-2);
  border-radius: var(--ds-radius-full);
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-scroll-area__thumb:hover { background: var(--ds-color-secondary); }
.ds-scroll-area__corner { background: var(--ds-color-light); }
</style>
