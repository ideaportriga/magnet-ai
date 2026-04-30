<script setup lang="ts">
/**
 * `<km-drawer>` — static side panel that collapses by inline-size. Used as
 * the admin shell's left sidebar. When `modelValue` flips to false the
 * drawer animates to `inline-size: 0`. Inner content keeps its full width
 * so the icons / text don't reflow during the collapse transition.
 *
 * For modal/slide-in drawers, use Reka `<DialogContent>` directly.
 */

import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    width?: string | number
    /** When false the drawer collapses to width 0. */
    modelValue?: boolean
    bordered?: boolean
  }>(),
  {
    width: 240,
    modelValue: true,
    bordered: false,
  },
)

defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const widthCss = computed(() => (typeof props.width === 'number' ? `${props.width}px` : props.width))
const inlineSize = computed(() => (props.modelValue ? widthCss.value : '0'))
</script>

<template>
  <aside
    class="km-drawer"
    :data-open="modelValue ? 'true' : undefined"
    :data-bordered="bordered ? 'true' : undefined"
    :style="{ '--km-drawer-width': widthCss, inlineSize }"
    data-test="km-drawer"
  >
    <div class="km-drawer__inner">
      <slot />
    </div>
  </aside>
</template>

<style>
.km-drawer {
  block-size: 100%;
  overflow: hidden;
  background: var(--ds-color-panel-main-bg, var(--ds-color-white));
  transition: inline-size var(--ds-duration-base, 200ms) var(--ds-ease-out);
}
.km-drawer[data-bordered='true'] {
  border-inline-end: 1px solid var(--ds-color-border);
}
.km-drawer__inner {
  inline-size: var(--km-drawer-width, 240px);
  block-size: 100%;
  overflow: auto;
}
</style>
