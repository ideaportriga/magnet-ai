<script setup lang="ts">
/**
 * ResizableHandle — the draggable divider between panels. Set
 * `with-handle` to render a small grip indicator.
 */
import type { SplitterResizeHandleEmits, SplitterResizeHandleProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { SplitterResizeHandle, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<SplitterResizeHandleProps & { withHandle?: boolean }>()
const emits = defineEmits<SplitterResizeHandleEmits>()

const delegatedProps = reactiveOmit(props, 'withHandle')
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <SplitterResizeHandle
    v-bind="forwarded"
    class="ds-resizable__handle"
    data-test="ds-resizable-handle"
  >
    <template v-if="props.withHandle">
      <div class="ds-resizable__grip">
        <slot>
          <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
            <circle cx="3.5" cy="2" r="0.7" fill="currentColor" />
            <circle cx="3.5" cy="5" r="0.7" fill="currentColor" />
            <circle cx="3.5" cy="8" r="0.7" fill="currentColor" />
            <circle cx="6.5" cy="2" r="0.7" fill="currentColor" />
            <circle cx="6.5" cy="5" r="0.7" fill="currentColor" />
            <circle cx="6.5" cy="8" r="0.7" fill="currentColor" />
          </svg>
        </slot>
      </div>
    </template>
  </SplitterResizeHandle>
</template>

<style>
.ds-resizable__handle {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 1px;
  background: var(--ds-color-border);
}
/* Hit area extension */
.ds-resizable__handle::after {
  content: '';
  position: absolute;
  inset-block: 0;
  inset-inline-start: 50%;
  inline-size: 4px;
  transform: translateX(-50%);
}

.ds-resizable__handle[data-orientation='vertical'] {
  block-size: 1px;
  inline-size: 100%;
}
.ds-resizable__handle[data-orientation='vertical']::after {
  inset-block-start: 50%;
  inset-inline: 0;
  inline-size: 100%;
  block-size: 4px;
  transform: translateY(-50%) translateX(0);
}

.ds-resizable__handle:focus-visible {
  outline: 1px solid var(--ds-color-primary);
  outline-offset: 1px;
}

.ds-resizable__grip {
  z-index: var(--ds-z-raised);
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 12px;
  block-size: 16px;
  background: var(--ds-color-border);
  color: var(--ds-color-text-grey);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-xs);
}
.ds-resizable__handle[data-orientation='vertical'] .ds-resizable__grip {
  transform: rotate(90deg);
}
</style>
