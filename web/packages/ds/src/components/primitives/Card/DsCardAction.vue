<script setup lang="ts">
/**
 * Card action — auxiliary control aligned to the top-right of the card
 * header. Picked up by `DsCardHeader` via `:has([data-slot='card-action'])`.
 */
</script>

<template>
  <div class="ds-card__action" data-slot="card-action">
    <slot />
  </div>
</template>

<style>
.ds-card__action {
  grid-column-start: 2;
  grid-row: 1 / span 2;
  place-self: start end;
}
</style>
