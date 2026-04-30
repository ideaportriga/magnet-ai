<script setup lang="ts">
/**
 * Empty — empty state container. Compose with `DsEmptyHeader`,
 * `DsEmptyMedia`, `DsEmptyTitle`, `DsEmptyDescription`, `DsEmptyContent`.
 *
 *   <DsEmpty>
 *     <DsEmptyHeader>
 *       <DsEmptyMedia variant="icon"><Icon /></DsEmptyMedia>
 *       <DsEmptyTitle>No results</DsEmptyTitle>
 *       <DsEmptyDescription>Try a different search term.</DsEmptyDescription>
 *     </DsEmptyHeader>
 *     <DsEmptyContent>
 *       <DsButton>Reset filters</DsButton>
 *     </DsEmptyContent>
 *   </DsEmpty>
 */
</script>

<template>
  <div class="ds-empty" data-test="ds-empty">
    <slot />
  </div>
</template>

<style>
.ds-empty {
  display: flex;
  min-inline-size: 0;
  flex: 1 1 auto;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-2xl);
  text-align: center;
  text-wrap: balance;
  border-radius: var(--ds-radius-lg);
  border: 1px dashed transparent;
  padding: var(--ds-space-2xl);
}
@media (min-width: 768px) {
  .ds-empty { padding: var(--ds-space-4xl); }
}
</style>
