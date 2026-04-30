<script setup lang="ts">
/**
 * `<km-glyph>` — internal helper that renders product icons through the DS
 * icon contract. Phosphor is the primary renderer for canonical names, with
 * Material Icons and FontAwesome kept as migration fallbacks. Used by domain
 * components (`KmBtn`, `KmIconBtn`, `KmInput`, …) whose API today accepts a
 * Quasar-style `name` prop like:
 *
 *   <km-btn icon="copy" />                 // Phosphor canonical name
 *   <km-btn icon="ph:thumbs-up" />         // explicit Phosphor namespace
 *   <km-btn icon="check_circle" />          // material symbol name
 *   <km-btn icon="fas fa-times" />          // FontAwesome class string
 *
 * Rendering rules:
 *   1. Known canonical names / `ph:*` ⇒ render a Phosphor Vue component.
 *   2. Whitespace in `name` ⇒ render `<i :class="name">` (FontAwesome v5/6,
 *      ionicons, custom). The same way `<km-glyph name="fas fa-times">` works.
 *   3. Otherwise ⇒ render `<i class="material-symbols-outlined">{{ name }}</i>`
 *      because the material-symbols/icons font is already loaded by the
 *      legacy `@themes` boot.
 *
 * Size accepts CSS length (px/em/rem). Prefer semantic `tone`; legacy `color`
 * still accepts a token name or any CSS colour string.
 */

import { computed } from 'vue'
import { resolveDsColor } from '../../utils/resolveDsColor'
import { resolvePhosphorIcon, type KmPhosphorIconWeight } from './phosphorIcons'

export type KmGlyphTone =
  | 'default'
  | 'subtle'
  | 'muted'
  | 'weak'
  | 'brand'
  | 'brand-soft'
  | 'info'
  | 'context'
  | 'accent'
  | 'success'
  | 'warning'
  | 'danger'
  | 'inverse'
  | 'seamless'
  | 'current'

const toneColorMap: Record<KmGlyphTone, string> = {
  default: 'var(--ds-color-icon)',
  subtle: 'var(--ds-color-secondary-text)',
  muted: 'var(--ds-color-text-grey)',
  weak: 'var(--ds-color-text-weak)',
  brand: 'var(--ds-color-primary)',
  'brand-soft': 'var(--ds-color-primary-transparent)',
  info: 'var(--ds-color-info)',
  context: '#8e24aa',
  accent: '#00897b',
  success: 'var(--ds-color-success-text)',
  warning: 'var(--ds-color-warning-text)',
  danger: 'var(--ds-color-error-text)',
  inverse: 'var(--ds-color-static-white)',
  seamless: 'var(--ds-color-seemless)',
  current: 'currentColor',
}

const props = withDefaults(
  defineProps<{
    name: string
    /** Any CSS length: '20px', '1.5em'. Quasar accepts 'sm/md/lg' too. */
    size?: string
    /** Semantic icon colour. Prefer this over raw `color`. */
    tone?: KmGlyphTone
    /** Phosphor stroke/fill weight for canonical icon names. */
    weight?: KmPhosphorIconWeight
    /** Legacy token name (e.g. 'primary', 'icon') or any CSS colour. */
    color?: string
  }>(),
  {
    size: '24px',
    tone: 'default',
    weight: 'regular',
  },
)

const phosphorIcon = computed(() => resolvePhosphorIcon(props.name))
const isFontAwesome = computed(() => /\s/.test(props.name))
/** Quasar prefixes: `o_` outlined, `r_` round, `s_` sharp. We only ship the
 *  outlined font here; treat any prefix as outlined for now. */
const isOutlined = computed(() => /^[ors]_/.test(props.name))
const ligature = computed(() => (isOutlined.value ? props.name.slice(2) : props.name))
const fontClass = computed(() => (isOutlined.value ? 'material-icons-outlined' : 'material-icons'))

const resolvedColor = computed(() => {
  if (props.color) return resolveDsColor(props.color) ?? props.color
  return toneColorMap[props.tone]
})

/**
 * Indirected through `--km-glyph-color` so an ancestor (e.g. a destructive
 * menu item) can force `currentColor` cascade by setting the variable on
 * the surrounding scope, without fighting the inline style.
 */
const colorStyle = computed(() => {
  if (!resolvedColor.value) return undefined
  return `var(--km-glyph-color, var(--km-glyph-fallback-color, ${resolvedColor.value}))`
})
</script>

<template>
  <component
    :is="phosphorIcon"
    v-if="phosphorIcon"
    class="km-glyph km-glyph--phosphor"
    :size="size"
    :weight="weight"
    :data-tone="tone"
    :style="{ color: colorStyle, width: size, height: size }"
    aria-hidden="true"
    data-test="km-glyph"
  />
  <i
    v-else-if="isFontAwesome"
    class="km-glyph"
    :class="name"
    :data-tone="tone"
    :style="{ fontSize: size, color: colorStyle, width: size, height: size }"
    aria-hidden="true"
    data-test="km-glyph"
  />
  <i
    v-else
    class="km-glyph"
    :class="fontClass"
    :data-tone="tone"
    :style="{ fontSize: size, color: colorStyle, width: size, height: size }"
    aria-hidden="true"
    data-test="km-glyph"
  >{{ ligature }}</i>
</template>

<style>
.km-glyph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-style: normal;
  line-height: 1;
  vertical-align: middle;
  flex: none;
}
</style>
