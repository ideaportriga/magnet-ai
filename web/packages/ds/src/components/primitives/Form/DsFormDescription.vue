<script setup lang="ts">
import { useFormField } from './useFormField'

const { formDescriptionId } = useFormField()
</script>

<template>
  <p
    :id="formDescriptionId"
    class="ds-form-description"
    data-test="ds-form-description"
  >
    <slot />
  </p>
</template>

<style>
.ds-form-description {
  margin: 0;
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-text-grey);
}
</style>
