<script setup lang="ts">
/**
 * BreadcrumbLink — interactive link inside a breadcrumb. Defaults to `<a>`,
 * use `as-child` to delegate (e.g. `<RouterLink>`).
 */

import { Primitive, type PrimitiveProps } from 'reka-ui'

withDefaults(defineProps<PrimitiveProps>(), {
  as: 'a',
})
</script>

<template>
  <Primitive
    class="ds-breadcrumb__link"
    :as="as"
    :as-child="asChild"
    data-test="ds-breadcrumb-link"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-breadcrumb__link {
  color: var(--ds-color-text-grey);
  text-decoration: none;
  transition: color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-breadcrumb__link:hover { color: var(--ds-color-black); }
.ds-breadcrumb__link:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
  border-radius: var(--ds-radius-xs);
}
</style>
