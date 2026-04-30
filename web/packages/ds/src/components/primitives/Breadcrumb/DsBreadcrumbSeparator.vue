<script setup lang="ts">
/**
 * BreadcrumbSeparator — visual separator between breadcrumb items. Defaults
 * to a chevron; pass a slot to override.
 */
</script>

<template>
  <li
    class="ds-breadcrumb__separator"
    role="presentation"
    aria-hidden="true"
    data-test="ds-breadcrumb-separator"
  >
    <slot>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M9 18l6-6-6-6"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </slot>
  </li>
</template>

<style>
.ds-breadcrumb__separator {
  display: inline-flex;
  align-items: center;
  color: var(--ds-color-text-grey);
}
.ds-breadcrumb__separator > svg {
  inline-size: 14px;
  block-size: 14px;
}
</style>
