<script setup lang="ts">
/**
 * `<km-icon-btn>` — drop-in for the legacy IconBtn (icon-only button with
 * tooltip-quality aria-label). Pure CSS hover effects; no Quasar.
 */

import { computed } from 'vue'
import KmGlyph, { type KmGlyphTone } from './KmGlyph.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

const props = withDefaults(
  defineProps<{
    color?: string
    tone?: KmGlyphTone
    icon?: string
    height?: string
    width?: string
    bg?: string
    disabled?: boolean
    iconSize?: string
    ariaLabel?: string
  }>(),
  {
    icon: 'autorenew',
    height: '32px',
    width: undefined,
    bg: 'transparent',
    iconSize: '24px',
    ariaLabel: '',
  },
)

defineEmits<{ click: [Event] }>()

const glyphStyle = computed(() => (
  props.color
    ? { '--km-glyph-fallback-color': resolveDsColor(props.color) ?? props.color }
    : undefined
))
</script>

<template>
  <button
    class="km-icon-btn"
    type="button"
    :tabindex="disabled ? -1 : 0"
    :aria-label="ariaLabel || icon"
    :aria-disabled="disabled ? 'true' : 'false'"
    :disabled="disabled"
    :style="{ inlineSize: width ?? height, blockSize: height, background: bg }"
    data-test="km-icon-btn"
    @click="$emit('click', $event)"
  >
    <KmGlyph :name="icon" :size="iconSize" :tone="tone" :style="glyphStyle" />
  </button>
</template>

<style>
.km-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
  transition:
    transform var(--ds-duration-fast) var(--ds-ease-out),
    background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-icon-btn:hover {
  transform: translateY(-1px);
}
.km-icon-btn:hover .km-glyph {
  color: var(--ds-color-primary) !important;
  transition: color var(--ds-duration-fast) var(--ds-ease-out);
}
.km-icon-btn:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: 2px; }
.km-icon-btn[disabled],
.km-icon-btn[aria-disabled='true'] {
  pointer-events: none;
  opacity: 0.5;
}
</style>
