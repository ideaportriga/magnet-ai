<script setup lang="ts">
/**
 * InputGroup — bordered container that visually fuses an input with leading
 * or trailing addons (icons, text, buttons).
 *
 *   <DsInputGroup>
 *     <DsInputGroupAddon align="inline-start"><SearchIcon /></DsInputGroupAddon>
 *     <DsInputGroupInput v-model="q" placeholder="Search…" />
 *     <DsInputGroupAddon align="inline-end">
 *       <DsInputGroupButton @click="clear">Clear</DsInputGroupButton>
 *     </DsInputGroupAddon>
 *   </DsInputGroup>
 */
</script>

<template>
  <div
    role="group"
    class="ds-input-group"
    data-test="ds-input-group"
  >
    <slot />
  </div>
</template>

<style>
.ds-input-group {
  position: relative;
  display: flex;
  inline-size: 100%;
  min-inline-size: 0;
  align-items: center;
  block-size: 36px;
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-control-bg);
  box-shadow: var(--ds-shadow-sm);
  outline: none;
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}

.ds-input-group:has(> textarea) {
  block-size: auto;
}

/* alignment-driven layout */
.ds-input-group:has(> [data-align='inline-start']) > input {
  padding-inline-start: var(--ds-space-sm);
}
.ds-input-group:has(> [data-align='inline-end']) > input {
  padding-inline-end: var(--ds-space-sm);
}
.ds-input-group:has(> [data-align='block-start']),
.ds-input-group:has(> [data-align='block-end']) {
  block-size: auto;
  flex-direction: column;
}
.ds-input-group:has(> [data-align='block-start']) > input { padding-block-end: var(--ds-space-md); }
.ds-input-group:has(> [data-align='block-end']) > input { padding-block-start: var(--ds-space-md); }

/* focus / error */
.ds-input-group:has([data-slot='input-group-control']:focus-visible) {
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 3px var(--ds-color-primary-transparent);
}
.ds-input-group:has([data-slot][aria-invalid='true']) {
  border-color: var(--ds-color-error);
}
.ds-input-group:has([data-slot][aria-invalid='true']):has(:focus-visible) {
  box-shadow: 0 0 0 3px var(--ds-color-error-bg);
}
</style>
