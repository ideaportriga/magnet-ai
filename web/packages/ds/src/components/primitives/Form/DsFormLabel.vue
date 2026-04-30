<script setup lang="ts">
import type { LabelProps } from 'reka-ui'
import DsLabel from '../Label/DsLabel.vue'
import { useFormField } from './useFormField'

defineProps<LabelProps>()

const { error, formItemId } = useFormField()
</script>

<template>
  <DsLabel
    class="ds-form-label"
    :data-error="!!error"
    data-test="ds-form-label"
    :for="formItemId"
  >
    <slot />
  </DsLabel>
</template>

<style>
.ds-form-label[data-error='true'] {
  color: var(--ds-color-error);
}
</style>
