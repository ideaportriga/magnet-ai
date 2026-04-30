<script setup lang="ts">
/**
 * `<km-chip-copy>` — table-cell copy button. Always shows the copy icon
 * (faint at rest, full color on hover); clicking copies `row.system_name`
 * (or `label`) to the clipboard and triggers a "Copied" toast.
 */

import KmBtn from './KmBtn.vue'
import { copyToClipboard } from '../../utils/clipboard'
import { notify } from '../../composables/useNotify'

const props = withDefaults(
  defineProps<{
    row?: Record<string, unknown>
    label?: string
  }>(),
  {
    row: () => ({}),
    label: 'Copy',
  },
)

async function copy() {
  const text = String(props.row.system_name ?? props.label ?? '')
  try {
    await copyToClipboard(text)
    notify.copied()
  } catch {
    notify.error('Failed to copy')
  }
}
</script>

<template>
  <span class="km-chip-copy">
    <KmBtn
      flat
      simple
      class="km-chip-copy__btn"
      interaction-tone="brand"
      icon="copy"
      icon-size="16px"
      :label="String(row.system_name ?? label)"
      data-test="km-chip-copy"
      @click.stop="copy"
    />
  </span>
</template>

<style>
/* Reveal-on-hover affordance: at rest only the label is visible; on hover
 * the copy icon expands into existence to the left of the label and the
 * chip's tinted background paints around both. The animation grows the
 * chip outward (icon width 0 -> 16px) instead of sliding the chip itself,
 * so the chip never extends left of its rest position — the table cell's
 * `overflow: hidden` can't clip it. */
.km-chip-copy { display: inline-flex; }
.km-chip-copy__btn {
  max-inline-size: 200px;
}
.km-chip-copy__btn :where(.km-glyph) {
  inline-size: 0;
  /* Cancel DsButton's flex `gap` between the icon and the label while the
   * icon is hidden, so the label doesn't have a phantom gutter at rest. */
  margin-inline-end: calc(var(--ds-space-sm) * -1);
  opacity: 0;
  overflow: hidden;
  transition:
    inline-size var(--ds-duration-base) var(--ds-ease-out),
    margin-inline-end var(--ds-duration-base) var(--ds-ease-out),
    opacity var(--ds-duration-base) var(--ds-ease-out);
}
.km-chip-copy:hover .km-chip-copy__btn :where(.km-glyph) {
  inline-size: 16px;
  margin-inline-end: 0;
  opacity: 1;
}
</style>
