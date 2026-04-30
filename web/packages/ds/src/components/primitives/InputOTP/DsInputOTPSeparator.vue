<script setup lang="ts">
</script>

<template>
  <div
    class="ds-input-otp__separator"
    role="separator"
    data-test="ds-input-otp-separator"
  >
    <slot>
      <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
        <path
          d="M2 6 L10 6"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
    </slot>
  </div>
</template>

<style>
.ds-input-otp__separator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ds-color-text-grey);
  padding-inline: var(--ds-space-2xs);
}
</style>
