<script setup lang="ts">
import DsInput from '../Input/DsInput.vue'
</script>

<template>
  <DsInput
    class="ds-sidebar__input"
    data-sidebar="input"
    data-test="ds-sidebar-input"
  >
    <slot />
  </DsInput>
</template>

<style>
.ds-sidebar__input {
  inline-size: 100%;
  block-size: 32px;
  background: var(--ds-color-background);
  box-shadow: none;
}
</style>
