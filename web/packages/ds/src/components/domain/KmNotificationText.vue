<script setup lang="ts">
/**
 * `<km-notification-text>` — small explanatory text used inside dialogs. The
 * legacy component renders a single string; we keep that shape and add an
 * optional default slot for callers that want richer markup.
 */

withDefaults(
  defineProps<{
    notification?: string
    tone?: 'neutral' | 'info' | 'success' | 'warning' | 'error'
  }>(),
  {
    notification: '',
    tone: 'neutral',
  },
)
</script>

<template>
  <p
    class="km-notification-text"
    :data-tone="tone"
    data-test="km-notification-text"
  >
    <slot>{{ notification }}</slot>
  </p>
</template>

<style>
.km-notification-text {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
  text-align: center;
  margin: 0;
}
.km-notification-text[data-tone='info']    { color: var(--ds-color-info); }
.km-notification-text[data-tone='success'] { color: var(--ds-color-success-text); }
.km-notification-text[data-tone='warning'] { color: var(--ds-color-warning-text); }
.km-notification-text[data-tone='error']   { color: var(--ds-color-error-text); }
</style>
