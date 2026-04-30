<script setup lang="ts">
/**
 * `<km-separator>` — drop-in over `<DsSeparator>`.
 *
 * Public API (preserved for legacy call-sites): `orientation`, `vertical`
 * (legacy boolean shorthand for vertical), `tone`, `color` (token name or
 * CSS colour), `dark` (legacy hint for darker borders). Internal: translates
 * the props to `DsSeparator`'s `orientation` and a CSS-var override for the
 * divider colour.
 */

import { computed } from 'vue'
import DsSeparator from '../primitives/Separator/DsSeparator.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

export type KmSeparatorTone = 'subtle' | 'inverse'

const toneColorMap: Record<KmSeparatorTone, string> = {
  subtle: 'var(--ds-color-border-2, var(--ds-color-border))',
  inverse: 'var(--ds-color-static-white)',
}

const props = withDefaults(
  defineProps<{
    /** Visual orientation. */
    orientation?: 'horizontal' | 'vertical'
    /** Legacy boolean shorthand for `orientation="vertical"`. */
    vertical?: boolean
    /** Semantic divider tone. Legacy `color` wins when present. */
    tone?: KmSeparatorTone
    /** Token name (`primary`, `border`, …) or any CSS colour. */
    color?: string
    /** Legacy: paint with darker border colour. */
    dark?: boolean
  }>(),
  {
    orientation: 'horizontal',
    vertical: false,
    tone: undefined,
    color: '',
    dark: false,
  },
)

const dsOrientation = computed<'horizontal' | 'vertical'>(() =>
  props.vertical ? 'vertical' : props.orientation,
)

const overrideStyle = computed(() => {
  const style: Record<string, string> = {}
  if (props.color) {
    style['--km-separator-color'] = resolveDsColor(props.color) ?? props.color
  } else if (props.tone) {
    style['--km-separator-color'] = toneColorMap[props.tone]
  } else if (props.dark) {
    style['--km-separator-color'] = 'var(--ds-color-border-2, var(--ds-color-border))'
  }
  return style
})
</script>

<template>
  <DsSeparator
    :orientation="dsOrientation"
    class="km-separator"
    :style="overrideStyle"
    data-test="km-separator"
  />
</template>

<style>
/* Default cadence so a separator never blends into its siblings. Wrapped
 * in `:where()` to keep the rule at specificity 0, so any per-call-site
 * margin utility (`my-md`, `mt-lg`, `my-0`, …) trumps it without `!important`. */
:where(.km-separator[data-orientation='horizontal']) {
  margin-block: var(--ds-space-md);
}
:where(.km-separator[data-orientation='vertical']) {
  margin-inline: var(--ds-space-md);
}
.km-separator {
  padding: 0;
  border: 0;
}
.km-separator[style*='--km-separator-color'] {
  background: var(--km-separator-color) !important;
}
</style>
