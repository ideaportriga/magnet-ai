<script setup lang="ts">
/**
 * Card header — title row with optional `<DsCardAction>`. When an action is
 * present the layout becomes a 2-column grid (title block on the left,
 * action on the right).
 */
</script>

<template>
  <div class="ds-card__header">
    <slot />
  </div>
</template>

<style>
.ds-card__header {
  display: grid;
  grid-auto-rows: min-content;
  grid-template-rows: auto auto;
  align-items: start;
  gap: var(--ds-space-xs);
  padding-inline: var(--ds-space-2xl);
}

/* If the header contains an action, lay out as title | action. */
.ds-card__header:has([data-slot='card-action']) {
  grid-template-columns: 1fr auto;
}
</style>
