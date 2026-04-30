<script setup lang="ts">
/**
 * `<km-avatar>` — drop-in over `<DsAvatar>`. Accepts `src` and falls back
 * to initials derived from `name` (or to the slot/`fallback` text).
 *
 * Public API (preserved): `src, alt, name, size, tone, color, textColor, icon,
 * fontSize, square, fallback`. Quasar-style legacy props that don't map
 * cleanly are forwarded as inline-style overrides so callers stay
 * binary-compatible.
 */

import { computed } from 'vue'
import DsAvatar from '../primitives/Avatar/DsAvatar.vue'
import KmGlyph from './KmGlyph.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

export type KmAvatarTone = 'brand' | 'brand-soft' | 'danger-soft' | 'neutral'

const toneMap: Record<KmAvatarTone, { bg: string; color: string }> = {
  brand: {
    bg: 'var(--ds-color-primary-bg)',
    color: 'var(--ds-color-white)',
  },
  'brand-soft': {
    bg: 'var(--ds-color-primary-light)',
    color: 'var(--ds-color-primary)',
  },
  'danger-soft': {
    bg: 'var(--ds-color-error-bg)',
    color: 'var(--ds-color-error-text)',
  },
  neutral: {
    bg: 'var(--ds-color-secondary-bg)',
    color: 'var(--ds-color-secondary-text)',
  },
}

const props = withDefaults(
  defineProps<{
    src?: string
    /** Image alt text. */
    alt?: string
    /** Used to derive initials when no image / icon / fallback is given. */
    name?: string
    /** Either a Ds size preset (`sm/md/lg/xl`) or a CSS length. */
    size?: string
    /** Semantic colour intent. Legacy `color` / `textColor` win when present. */
    tone?: KmAvatarTone
    /** Background colour token (legacy). */
    color?: string
    /** Text colour token (legacy). */
    textColor?: string
    /** Optional Material/Glyph icon name. */
    icon?: string
    /** Inline override for the inner text/icon font size. */
    fontSize?: string
    /** Render with sharp corners instead of a circle. */
    square?: boolean
    /** Explicit fallback text (overrides initials). */
    fallback?: string
  }>(),
  {
    size: '32px',
  },
)

const dsSize = computed<'sm' | 'md' | 'lg' | 'xl' | undefined>(() => {
  switch (props.size) {
    case 'sm':
    case 'md':
    case 'lg':
    case 'xl':
      return props.size
    default:
      return undefined
  }
})

const dsStyle = computed(() => {
  const style: Record<string, string | undefined> = {}
  if (!dsSize.value) {
    style.inlineSize = props.size
    style.blockSize = props.size
  }
  if (props.color) {
    style.backgroundColor = resolveDsColor(props.color)
  } else if (props.tone) {
    style.backgroundColor = toneMap[props.tone].bg
  }
  if (props.textColor) {
    style.color = resolveDsColor(props.textColor)
  } else if (props.tone) {
    style.color = toneMap[props.tone].color
  }
  if (props.fontSize) style.fontSize = props.fontSize
  if (props.square) style.borderRadius = 'var(--ds-radius-md)'
  return style
})
</script>

<template>
  <DsAvatar
    :src="src"
    :name="fallback || name"
    :alt="alt"
    :size="dsSize"
    :style="dsStyle"
    class="km-avatar"
    :data-tone="tone"
    :data-square="square ? 'true' : undefined"
    data-test="km-avatar"
  >
    <slot>
      <KmGlyph v-if="icon" :name="icon" :size="fontSize || '60%'" />
    </slot>
  </DsAvatar>
</template>

<style>
.km-avatar[data-square='true'] {
  border-radius: var(--ds-radius-md);
}
</style>
