<script setup lang="ts">
/**
 * Card — surface container. Replaces shadcn `<Card>`. Compose with the sub-
 * components (`DsCardHeader`, `DsCardTitle`, `DsCardDescription`,
 * `DsCardAction`, `DsCardContent`, `DsCardFooter`) for the standard layout,
 * or use `<DsCard>` standalone with custom children.
 *
 *   <DsCard>
 *     <DsCardHeader>
 *       <DsCardTitle>Plan</DsCardTitle>
 *       <DsCardDescription>Pro tier</DsCardDescription>
 *       <DsCardAction><DsButton size="sm">Edit</DsButton></DsCardAction>
 *     </DsCardHeader>
 *     <DsCardContent>…</DsCardContent>
 *     <DsCardFooter>…</DsCardFooter>
 *   </DsCard>
 */
</script>

<template>
  <div class="ds-card" data-test="ds-card">
    <slot />
  </div>
</template>

<style>
.ds-card {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xl);
  padding-block: var(--ds-space-2xl);
  background: var(--ds-color-message-bg);
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-xl);
  box-shadow: var(--ds-shadow-sm);
}

/* Headers / footers visually separated by a divider get the standard
 * inner padding the body slots use. */
.ds-card__header.is-divided,
.ds-card__footer.is-divided { padding-block: var(--ds-space-2xl); }
</style>
