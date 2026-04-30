<script setup lang="ts">
/**
 * `<km-chip>` — drop-in for the legacy Chip. Renders over `<DsBadge>`
 * (chip-styled — `DsBadge` supports the `secondary`/`outline` variants we
 * need) plus a thin wrapper for legacy chip-only features that DsBadge
 * doesn't expose: a `removable` × close button.
 *
 * Target API:
 *   `display, tone, shape, dense, clickable, removable`.
 * Legacy API (preserved):
 *   `size, iconSize, iconColor, iconMarginRight, icon, label, tooltip,
 *    labelClass, clickable, round, square, dense, color, textColor,
 *    flatColor, removable` + default slot. Emits: `click`, `remove`.
 */

import { computed } from 'vue'
import DsBadge, { type DsBadgeDisplay, type DsBadgeShape, type DsBadgeTone } from '../primitives/Badge/DsBadge.vue'
import KmGlyph from './KmGlyph.vue'
import KmTooltip from './KmTooltip.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'
import type { KmGlyphTone } from './KmGlyph.vue'

export type KmChipDisplay = Extract<DsBadgeDisplay, 'status' | 'tag' | 'filter' | 'input-token' | 'counter'>
export type KmChipTone = DsBadgeTone
export type KmChipShape = DsBadgeShape

const props = withDefaults(
  defineProps<{
    /** Target display role. Prefer this over raw color tokens. */
    display?: KmChipDisplay
    /** Semantic tone. Prefer this over raw color tokens. */
    tone?: KmChipTone
    /** Closed shape set. `square` replaces legacy ad hoc square chips. */
    shape?: KmChipShape
    size?: string
    iconSize?: string
    iconColor?: string
    iconMarginRight?: string
    icon?: string
    label?: string
    tooltip?: string
    labelClass?: string
    clickable?: boolean
    /** Pill (rounded) shape. */
    round?: boolean
    /** Square corners (overrides `round`). */
    square?: boolean
    /** Compact padding/font. */
    dense?: boolean
    color?: string
    textColor?: string
    /** When true, `color` paints only the background (text stays current). */
    flatColor?: boolean
    /** Render an inline × close button and emit `remove`. */
    removable?: boolean
  }>(),
  {
    display: 'tag',
    tone: 'neutral',
    size: '24px',
    iconSize: '20px',
    iconColor: '',
    iconMarginRight: '12px',
    icon: '',
    label: '',
    tooltip: '',
    labelClass: 'km-chip__heading',
    clickable: false,
    round: false,
    square: false,
    dense: false,
    color: '',
    textColor: '',
    flatColor: false,
    removable: false,
  },
)

defineEmits<{
  click: [event: Event]
  remove: [event: Event]
}>()

const chipStyle = computed(() => {
  const style: Record<string, string | undefined> = {
    blockSize: props.size,
  }
  if (props.color) {
    style.background = resolveDsColor(props.color) ?? props.color
  }
  if (props.textColor) {
    style.color = resolveDsColor(props.textColor) ?? props.textColor
  }
  return style
})

const resolvedShape = computed<KmChipShape>(() => {
  if (props.shape) return props.shape
  if (props.square) return 'square'
  return 'pill'
})

const usesLegacyTint = computed(() => Boolean(props.color || props.textColor))

const iconStyle = computed(() => {
  const style: Record<string, string> = {
    marginInlineEnd: props.iconMarginRight,
  }
  if (props.iconColor) style['--km-glyph-fallback-color'] = resolveDsColor(props.iconColor) ?? props.iconColor
  return style
})

const iconTone = computed<KmGlyphTone>(() => (props.iconColor ? 'default' : 'current'))
</script>

<template>
  <DsBadge
    as="span"
    variant="secondary"
    class="km-chip"
    :display="display"
    :tone="usesLegacyTint ? undefined : tone"
    :shape="resolvedShape"
    :data-clickable="clickable ? 'true' : undefined"
    :data-round="round && !square ? 'true' : undefined"
    :data-square="square ? 'true' : undefined"
    :data-display="display"
    :data-shape="resolvedShape"
    :data-dense="dense ? 'true' : undefined"
    :data-removable="removable ? 'true' : undefined"
    :data-tinted="color ? 'true' : undefined"
    :style="chipStyle"
    data-test="km-chip"
    @click="$emit('click', $event)"
  >
    <KmGlyph
      v-if="icon"
      :name="icon"
      :size="iconSize"
      :tone="iconTone"
      :style="iconStyle"
    />
    <span v-if="$slots.default" class="km-chip__slot">
      <slot />
    </span>
    <span v-if="label" class="km-chip__label" :class="labelClass">{{ label }}</span>

    <button
      v-if="removable"
      type="button"
      class="km-chip__remove"
      aria-label="Remove"
      @click.stop="$emit('remove', $event)"
    >
      <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
        <path d="M2 2 L8 8 M8 2 L2 8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
    </button>

    <KmTooltip v-if="tooltip" :label="tooltip" />
  </DsBadge>
</template>

<style>
/* `.km-chip` extends `.ds-badge` (which provides the secondary-variant
 * grey background by default). When the call-site passes `color="…"` we
 * mark the chip as tinted, and the inline `style.background` from the
 * wrapper takes over — the secondary-variant fallback never paints. */
.km-chip {
  user-select: none;
  gap: var(--ds-space-sm);
  vertical-align: middle;
}
.km-chip[data-shape='pill'] { border-radius: var(--ds-radius-full); }
.km-chip[data-shape='square'] { border-radius: var(--ds-radius-sm); }
.km-chip[data-round='true']  { border-radius: var(--ds-radius-full); }
.km-chip[data-square='true'] { border-radius: var(--ds-radius-sm); }

.km-chip[data-display='filter'],
.km-chip[data-display='input-token'] {
  border-radius: var(--ds-radius-md);
}

.km-chip[data-shape='square'][data-display] {
  border-radius: var(--ds-radius-sm);
}

.km-chip[data-dense='true'] {
  padding-block: 0;
  padding-inline: var(--ds-space-xs);
  font-size: var(--ds-font-size-xs);
}

.km-chip[data-clickable='true'] {
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-chip[data-clickable='true']:not([data-tinted='true']):hover {
  background: var(--ds-color-light);
}

.km-chip__heading {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}
.km-chip__label {
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
/* Pass slot children straight into the chip's flex line. Without this, a
 * slot that renders no inline DOM (e.g. `<km-tooltip>`, which uses
 * `display: contents` for its anchor and portals the popup) still
 * produces a zero-width flex item — the chip's `gap` then pushes the
 * label off-centre, making horizontal padding look asymmetric. */
.km-chip__slot { display: contents; }
.km-chip__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 14px;
  block-size: 14px;
  padding: 0;
  margin-inline-start: var(--ds-space-2xs);
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  border-radius: 50%;
  opacity: 0.6;
  transition: opacity var(--ds-duration-fast) var(--ds-ease-out), background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-chip__remove:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.08);
}
</style>
