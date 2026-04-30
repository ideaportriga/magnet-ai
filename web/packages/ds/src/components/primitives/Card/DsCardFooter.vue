<script setup lang="ts">
/** Card footer — actions row at the bottom of the card. */
</script>

<template>
  <div class="ds-card__footer">
    <slot />
  </div>
</template>

<style>
.ds-card__footer {
  display: flex;
  align-items: center;
  padding-inline: var(--ds-space-2xl);
}
</style>
