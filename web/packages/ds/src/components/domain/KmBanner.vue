<script setup lang="ts">
/**
 * `<km-banner>` — inline notice / status callout. Replaces Quasar's
 * `<q-banner>` with a plain CUBE-styled block. Slots:
 *   - `avatar` — leading icon / decoration
 *   - default — banner text / actions
 */
withDefaults(
  defineProps<{
    rounded?: boolean
    dense?: boolean
  }>(),
  { rounded: false, dense: false },
)
</script>

<template>
  <div
    class="km-banner"
    :data-rounded="rounded ? 'true' : undefined"
    :data-dense="dense ? 'true' : undefined"
    role="status"
    data-test="km-banner"
  >
    <span v-if="$slots.avatar" class="km-banner__avatar">
      <slot name="avatar" />
    </span>
    <div class="km-banner__body">
      <slot />
    </div>
  </div>
</template>

<style>
.km-banner {
  display: flex;
  gap: var(--ds-space-sm, 8px);
  align-items: flex-start;
  padding: var(--ds-space-md, 12px) var(--ds-space-lg, 16px);
  background: var(--ds-color-light, var(--ds-color-gray-50));
  border: 1px solid var(--ds-color-border);
}
.km-banner[data-rounded='true'] { border-radius: var(--ds-radius-md, 8px); }
.km-banner[data-dense='true'] { padding: var(--ds-space-sm, 8px) var(--ds-space-md, 12px); }
.km-banner__avatar { flex: none; display: inline-flex; align-items: center; }
.km-banner__body { flex: 1 1 auto; min-inline-size: 0; }
</style>
