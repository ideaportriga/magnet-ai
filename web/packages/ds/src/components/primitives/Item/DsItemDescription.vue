<script setup lang="ts">
/**
 * ItemDescription — secondary copy inside `DsItemContent`. Truncates to two
 * lines and inherits anchor styling for inline links.
 */
</script>

<template>
  <p class="ds-item__description" data-test="ds-item-description">
    <slot />
  </p>
</template>

<style>
.ds-item__description {
  margin: 0;
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
  line-height: var(--ds-line-height-normal);
  font-weight: var(--ds-font-weight-regular);
  text-wrap: balance;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.ds-item__description > a {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 4px;
}
.ds-item__description > a:hover {
  color: var(--ds-color-primary);
}
</style>
