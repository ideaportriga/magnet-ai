<script setup lang="ts">
/**
 * `<km-btn>` — drop-in for the legacy Btn component.
 *
 * Public API (preserved for ~520 call-sites):
 *   label, secondary, flat, simple, dropdown, loading, size, disable,
 *   labelClass, tooltip, optionsClass, selected, color, bg, hoverColor, hoverBg,
 *   tone, interactionTone, icon, iconColor, iconTone, iconSize, svgIcon, iconAfter, contentStyle,
 *   contentClass, options, link, inputLike, variant, dense, round
 *
 * Quasar semantics for `color`/`bg`:
 *   - on FILLED buttons (default / unelevated / secondary), `color` tints
 *     the text/icon and `bg` tints the background;
 *   - on FLAT / SIMPLE / LINK buttons, `color` tints the text/icon,
 *     leaving the (transparent) background as the variant defines it.
 *
 * Internally renders `<DsButton>` with each override applied individually
 * via a per-prop data attribute, so unset overrides do NOT collapse the
 * background to a primary fallback.
 */

import { computed, ref } from 'vue'
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuTrigger,
} from 'reka-ui'
import DsButton from '../primitives/Button/DsButton.vue'
import DsSpinner from '../primitives/Spinner/DsSpinner.vue'
import KmGlyph from './KmGlyph.vue'
import type { KmGlyphTone } from './KmGlyph.vue'
import KmIcon from './KmIcon.vue'
import KmTooltip from './KmTooltip.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

export type KmBtnVariant =
  | 'primary'
  | 'secondary'
  | 'tertiary'
  | 'outline'
  | 'danger'
  | 'ghost'
  | 'flat'
  | 'simple'
  | 'link'

export type KmBtnTone =
  | 'brand'
  | 'accent'
  | 'danger'
  | 'neutral'
  | 'subtle'
  | 'muted'
  | 'weak'
  | 'inverse'
  | 'current'

export type KmBtnInteractionTone = 'brand' | 'danger'

interface KmBtnOption {
  label: string
  svgIcon?: string
  icon?: string
  [key: string]: unknown
}

const props = withDefaults(
  defineProps<{
    label?: string
    secondary?: boolean
    flat?: boolean
    simple?: boolean
    link?: boolean
    /** Explicit semantic variant (preferred). */
    variant?: KmBtnVariant
    dropdown?: boolean
    loading?: boolean
    size?: string
    disable?: boolean
    labelClass?: string
    tooltip?: string
    optionsClass?: string
    /** Semantic colour intent for the button's rest state. Legacy `color` wins when present. */
    tone?: KmBtnTone
    /** Semantic colour intent for hover/focus/active affordances without changing rest state. */
    interactionTone?: KmBtnInteractionTone
    /** Selected navigation/filter state. Prefer this over raw active bg/color recipes. */
    selected?: boolean
    color?: string
    bg?: string
    hoverColor?: string
    hoverBg?: string
    icon?: string
    iconColor?: string
    /** Semantic glyph tone. Legacy `iconColor` wins when present. */
    iconTone?: KmGlyphTone
    iconSize?: string
    svgIcon?: string
    iconAfter?: string
    contentStyle?: string
    contentClass?: string
    options?: KmBtnOption[]
    inputLike?: boolean
    /** Quasar legacy: smaller, tighter button. */
    dense?: boolean
    /** Quasar legacy: fully circular for icon-only buttons. */
    round?: boolean
    /** CUBE modifier — content alignment along the inline axis. */
    justify?: 'start' | 'center' | 'end' | 'between'
    /** CUBE modifier — fill container inline-size. */
    block?: boolean
  }>(),
  {
    iconSize: '22px',
    options: () => [],
  },
)

defineEmits<{
  click: [event: Event]
  'click-option': [option: KmBtnOption]
}>()

/** Map legacy adjective props (or `variant`) to `<DsButton>` variants. */
const dsVariant = computed<'primary' | 'secondary' | 'ghost' | 'link' | 'outline' | 'destructive'>(() => {
  const v = props.variant
    ?? (props.link ? 'link'
      : props.flat ? 'flat'
        : props.simple ? 'simple'
          : props.secondary ? 'secondary'
            : 'primary')
  if (v === 'tertiary') return 'ghost'
  if (v === 'danger') return 'destructive'
  if (v === 'flat') return 'ghost'
  if (v === 'simple') return 'secondary'
  return v
})

const isIconOnly = computed(() =>
  Boolean((props.icon || props.svgIcon) && !props.label?.length && !props.dropdown),
)

/** Map legacy `size` + `dense` to `<DsButton>` sizes. */
const dsSize = computed<'sm' | 'md' | 'lg' | 'icon' | 'icon-xs' | 'icon-sm' | 'icon-lg'>(() => {
  const s = props.size
  if (s === 'icon-xs' || s === 'icon-sm' || s === 'icon-lg') return s
  // Pre-resolve text-side modifier first, then upgrade to an icon-* variant
  // when the button has only an icon child.
  const textSide: 'sm' | 'md' | 'lg' = props.dense
    ? 'sm'
    : (s === 'sm' || s === 'xs')
        ? 'sm'
        : (s === 'lg' || s === 'xl') ? 'lg' : 'md'
  if (!isIconOnly.value) return textSide
  return textSide === 'sm' ? 'icon-sm' : textSide === 'lg' ? 'icon-lg' : 'icon'
})

const resolveColor = (name: string) => resolveDsColor(name) ?? name

const toneColorMap: Record<KmBtnTone, string> = {
  brand: 'var(--ds-color-primary)',
  accent: '#00897b',
  danger: 'var(--ds-color-error)',
  neutral: 'var(--ds-color-text-primary)',
  subtle: 'var(--ds-color-secondary-text)',
  muted: 'var(--ds-color-secondary)',
  weak: 'var(--ds-color-text-grey)',
  inverse: 'var(--ds-color-white)',
  current: 'currentColor',
}

const toneBgMap: Partial<Record<KmBtnTone, string>> = {
  brand: 'var(--ds-color-primary)',
  accent: '#00897b',
  danger: 'var(--ds-color-error)',
  neutral: 'var(--ds-color-control-bg)',
  subtle: 'var(--ds-color-secondary-bg)',
  muted: 'var(--ds-color-control-bg)',
  inverse: 'var(--ds-color-white)',
}

const interactionToneMap: Record<KmBtnInteractionTone, { color: string; bg: string }> = {
  brand: {
    color: 'var(--ds-color-primary)',
    bg: 'var(--ds-color-primary-bg)',
  },
  danger: {
    color: 'var(--ds-color-error)',
    bg: 'var(--ds-color-error-bg)',
  },
}

/** Quasar's `color` prop on a SOLID button (default / unelevated / a11y
 * destructive) tints the BACKGROUND, not the text. On every other variant
 * (ghost / link / outline / secondary) it tints the foreground. */
const colorTintsBackground = computed(() =>
  dsVariant.value === 'primary' || dsVariant.value === 'destructive',
)

const resolvedBg = computed(() => {
  if (props.bg) return resolveColor(props.bg)
  if (props.color && colorTintsBackground.value) return resolveColor(props.color)
  if (props.tone && colorTintsBackground.value) return toneBgMap[props.tone]
  return undefined
})
const resolvedColor = computed(() =>
  props.color && !colorTintsBackground.value
    ? resolveColor(props.color)
    : props.tone && !colorTintsBackground.value
      ? toneColorMap[props.tone]
      : undefined,
)
const resolvedHoverBg = computed(() => {
  if (props.hoverBg) return resolveColor(props.hoverBg)
  if (props.interactionTone) return interactionToneMap[props.interactionTone].bg
  if (props.hoverColor && colorTintsBackground.value) return resolveColor(props.hoverColor)
  return undefined
})
const resolvedHoverColor = computed(() =>
  props.hoverColor && !colorTintsBackground.value
    ? resolveColor(props.hoverColor)
    : props.interactionTone && !colorTintsBackground.value
      ? interactionToneMap[props.interactionTone].color
      : undefined,
)

const overrideStyle = computed(() => {
  const style: Record<string, string> = {}
  if (resolvedColor.value) style['--km-btn-color-override'] = resolvedColor.value
  if (resolvedBg.value) style['--km-btn-bg-override'] = resolvedBg.value
  if (resolvedHoverColor.value) style['--km-btn-hover-color-override'] = resolvedHoverColor.value
  if (resolvedHoverBg.value) style['--km-btn-hover-bg-override'] = resolvedHoverBg.value
  return style
})

const iconFallbackStyle = computed(() => (
  props.iconColor
    ? { '--km-glyph-fallback-color': resolveColor(props.iconColor) }
    : undefined
))

const menuOpen = ref(false)
</script>

<template>
  <!-- Dropdown variant: trigger DsButton wrapped in reka-ui DropdownMenu. -->
  <DropdownMenuRoot v-if="dropdown" v-model:open="menuOpen">
    <DropdownMenuTrigger as-child>
      <DsButton
        v-bind="$attrs"
        class="km-btn"
        :class="[contentClass, labelClass, { 'km-btn--input-like': inputLike, 'km-btn--round': round }]"
        :variant="dsVariant"
        :size="dsSize"
        :justify="justify"
        :block="block"
        :data-state="disable ? 'disabled' : (loading ? 'loading' : undefined)"
        :data-km-color="resolvedColor ? '' : undefined"
        :data-km-bg="resolvedBg ? '' : undefined"
        :data-km-hover-color="resolvedHoverColor ? '' : undefined"
        :data-km-hover-bg="resolvedHoverBg ? '' : undefined"
        :data-tone="tone"
        :data-interaction-tone="interactionTone"
        :data-selected="selected ? 'true' : undefined"
        :disabled="disable"
        :style="[overrideStyle, contentStyle]"
        :data-test="$attrs['data-test'] ?? 'km-btn'"
        @click="$emit('click', $event)"
      >
        <KmGlyph v-if="icon" :name="icon" :size="iconSize" :tone="iconTone" :style="iconFallbackStyle" />
        <KmIcon v-if="svgIcon" :name="svgIcon" width="24" height="18" />
        <span v-if="label" class="km-btn__label">{{ label }}</span>
        <KmGlyph v-if="!loading" name="chevron-down" :size="iconSize" />
        <DsSpinner v-else size="sm" />
      </DsButton>
    </DropdownMenuTrigger>

    <DropdownMenuPortal>
      <DropdownMenuContent
        class="ds-menu km-btn__menu"
        :class="optionsClass"
        side="bottom"
        align="end"
        :side-offset="4"
      >
        <DropdownMenuItem
          v-for="opt in options"
          :key="opt.label"
          class="ds-menu__item km-btn__menu-item"
          @select="$emit('click-option', opt)"
        >
          <KmIcon v-if="opt.svgIcon" :name="opt.svgIcon" width="24" height="18" />
          <KmGlyph v-else-if="opt.icon" :name="opt.icon" />
          <span>{{ opt.label }}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>

  <!-- Plain button. Retain `<button>` semantics via DsButton's default `as`. -->
  <DsButton
    v-else
    v-bind="$attrs"
    class="km-btn"
    :class="[contentClass, labelClass, { 'km-btn--input-like': inputLike, 'km-btn--round': round }]"
    :variant="dsVariant"
    :size="dsSize"
    :justify="justify"
    :block="block"
    :data-state="disable ? 'disabled' : (loading ? 'loading' : undefined)"
    :data-km-color="resolvedColor ? '' : undefined"
    :data-km-bg="resolvedBg ? '' : undefined"
    :data-km-hover-color="resolvedHoverColor ? '' : undefined"
    :data-km-hover-bg="resolvedHoverBg ? '' : undefined"
    :data-tone="tone"
    :data-interaction-tone="interactionTone"
    :data-selected="selected ? 'true' : undefined"
    :disabled="disable"
    :style="[overrideStyle, contentStyle]"
    :data-test="$attrs['data-test'] ?? 'km-btn'"
    @click="$emit('click', $event)"
  >
    <slot>
      <KmGlyph v-if="icon" :name="icon" :size="iconSize" :tone="iconTone" :style="iconFallbackStyle" />
      <KmIcon v-if="svgIcon" :name="svgIcon" width="24" height="18" />
      <span v-if="label" class="km-btn__label">{{ label }}</span>
      <DsSpinner v-if="loading" size="sm" />
      <KmGlyph v-else-if="iconAfter" :name="iconAfter" :size="iconSize" />
    </slot>

    <KmTooltip v-if="tooltip || $slots.tooltip" :label="tooltip || ''">
      <slot v-if="$slots.tooltip" name="tooltip" />
    </KmTooltip>
  </DsButton>
</template>

<style>
/* Hover/focus icons follow the button's text color so a flat button whose
 * label turns primary on hover gets a primary-coloured icon too. At REST
 * the variable is unset, so KmGlyph falls back to whatever `iconColor` the
 * call-site passed (typically `--ds-color-icon`, the lighter grey).
 * Without this scoping, an explicit `icon-color="icon"` would be silently
 * overridden by the button's text color (e.g. ghost-variant grey var(--ds-color-gray-700)),
 * which is darker than the icon token. */
.km-btn:hover,
.km-btn:focus-visible,
.km-btn[aria-expanded='true'],
.km-btn[data-state='open'],
.km-btn[data-selected='true'] {
  --km-glyph-color: currentColor;
}

/* Per-prop overrides — each rule fires only when the corresponding
 * `data-km-*` attribute is set, so passing only `color` doesn't accidentally
 * collapse the background to a primary fallback. */
.km-btn[data-km-color] {
  color: var(--km-btn-color-override) !important;
}
.km-btn[data-km-bg] {
  background: var(--km-btn-bg-override) !important;
  border-color: var(--km-btn-bg-override) !important;
}
.km-btn[data-km-hover-color]:hover {
  color: var(--km-btn-hover-color-override, var(--km-btn-color-override)) !important;
}
.km-btn[data-km-hover-bg]:hover {
  background: var(--km-btn-hover-bg-override, var(--km-btn-bg-override)) !important;
  border-color: var(--km-btn-hover-bg-override, var(--km-btn-bg-override)) !important;
}
.km-btn[data-selected='true'] {
  background: var(--ds-color-primary-bg) !important;
  border-color: var(--ds-color-primary-bg) !important;
  color: var(--ds-color-primary) !important;
}

/* Input-like buttons live next to inputs (e.g. clear / submit affordances).
 * They look like a control with a border, not a primary-coloured button. */
.km-btn--input-like {
  background: var(--ds-color-control-bg) !important;
  color: var(--ds-color-black) !important;
  border-color: var(--ds-color-control-border) !important;
}

/* Round / circular icon-only button (Quasar `round` shorthand). */
.km-btn--round {
  border-radius: var(--ds-radius-full) !important;
}

.km-btn__label {
  text-align: start;
  text-overflow: ellipsis;
  overflow: hidden;
}

.km-btn__menu { z-index: var(--ds-z-popover); }
.km-btn__menu-item {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
}
</style>
