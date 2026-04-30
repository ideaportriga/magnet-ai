<script setup lang="ts">
/** Card content — main slot. Inline padding only; vertical rhythm comes
 * from the card root. */
</script>

<template>
  <div class="ds-card__content">
    <slot />
  </div>
</template>

<style>
.ds-card__content {
  padding-inline: var(--ds-space-2xl);
}
</style>
