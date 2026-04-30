<script setup lang="ts">
/**
 * Skeleton — animated placeholder for loading states. Size it via inline
 * styles, utility classes, or wrapping element.
 *
 *   <DsSkeleton style="block-size: 1rem; inline-size: 60%;" />
 */
</script>

<template>
  <div
    class="ds-skeleton"
    aria-hidden="true"
    data-test="ds-skeleton"
  />
</template>

<style>
.ds-skeleton {
  display: block;
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-primary-bg);
  animation: ds-skeleton-pulse 1.6s var(--ds-ease-in-out) infinite;
}

@keyframes ds-skeleton-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
}

/* Respect reduced motion: keep the colour, drop the pulse. */
@media (prefers-reduced-motion: reduce) {
  .ds-skeleton { animation: none; }
}
</style>
