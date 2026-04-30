<script setup lang="ts">
/**
 * `<km-icon>` — drop-in for `@ui-comp`'s SVG-sprite icon component.
 *
 * Renders SVG sprite icons that the legacy `loadIcons()` boot routine injects
 * into the DOM (`<symbol id="icon-name">`). Public API is preserved 1:1 so
 * existing call sites compile without change.
 *
 * Future: when the icon system is migrated to Iconify, this component
 * detects `prefix:name` syntax and dispatches to the Iconify renderer.
 */

withDefaults(
  defineProps<{
    name: string
    width?: string
    height?: string
  }>(),
  {
    width: '24',
    height: '18',
  },
)
</script>

<template>
  <svg
    class="km-icon"
    :viewBox="`0 0 ${width} ${height}`"
    :width="width"
    :height="height"
    role="presentation"
    aria-hidden="true"
    data-test="km-icon"
  >
    <use :href="`#icon-${name}`" />
  </svg>
</template>

<style>
.km-icon {
  display: inline-block;
  vertical-align: middle;
}
</style>
