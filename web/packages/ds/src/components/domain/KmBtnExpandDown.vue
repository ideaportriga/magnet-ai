<script setup lang="ts">
/**
 * `<km-btn-expand-down>` — small chevron button used in dropdown triggers
 * and disclosure sections. Same shape as the legacy implementation but
 * built on inline SVG instead of `<km-glyph name="chevron-down">`.
 */

import { resolveDsColor } from '../../utils/resolveDsColor'

const props = withDefaults(
  defineProps<{
    /** Whether the panel is currently expanded — controls chevron rotation. */
    expanded?: boolean
    size?: string
    color?: string
    disabled?: boolean
  }>(),
  {
    expanded: false,
    size: '24px',
    color: 'icon',
    disabled: false,
  },
)

defineEmits<{
  toggle: [boolean]
  click: [Event]
}>()

function handleClick(event: Event) {
  if (props.disabled) return
  event.stopPropagation?.()
}
</script>

<template>
  <button
    class="km-btn-expand-down"
    type="button"
    :data-expanded="expanded ? 'true' : undefined"
    :disabled="disabled"
    :aria-expanded="expanded"
    :style="{
      inlineSize: size,
      blockSize: size,
      color: resolveDsColor(color),
    }"
    data-test="km-btn-expand-down"
    @click="(e) => { handleClick(e); $emit('toggle', !expanded); $emit('click', e) }"
  >
    <svg viewBox="0 0 14 14" :width="size" :height="size" aria-hidden="true">
      <path
        d="M3.5 5.5 L7 9 L10.5 5.5"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  </button>
</template>

<style>
.km-btn-expand-down {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 0;
  cursor: pointer;
  border-radius: var(--ds-radius-sm);
  transition:
    background var(--ds-duration-fast) var(--ds-ease-out),
    transform var(--ds-duration-fast) var(--ds-ease-out);
}
.km-btn-expand-down:hover { background: var(--ds-color-light); }
.km-btn-expand-down:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: 2px; }
.km-btn-expand-down[data-expanded='true'] svg { transform: rotate(180deg); transition: transform var(--ds-duration-fast) var(--ds-ease-out); }
.km-btn-expand-down[disabled] { opacity: 0.5; pointer-events: none; }
</style>
