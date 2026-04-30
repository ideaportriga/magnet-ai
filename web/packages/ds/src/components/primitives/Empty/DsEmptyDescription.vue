<script setup lang="ts">
/**
 * EmptyDescription — secondary copy under the title of an empty state.
 */
</script>

<template>
  <p class="ds-empty__description" data-test="ds-empty-description">
    <slot />
  </p>
</template>

<style>
.ds-empty__description {
  margin: 0;
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
  line-height: var(--ds-line-height-relaxed);
}
.ds-empty__description > a {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 4px;
}
.ds-empty__description > a:hover {
  color: var(--ds-color-primary);
}
</style>
