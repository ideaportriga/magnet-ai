<script setup lang="ts">
import { ErrorMessage } from 'vee-validate'
import { toValue } from 'vue'
import { useFormField } from './useFormField'

const { name, formMessageId } = useFormField()
</script>

<template>
  <ErrorMessage
    :id="formMessageId"
    class="ds-form-message"
    data-test="ds-form-message"
    as="p"
    :name="toValue(name)"
  />
</template>

<style>
.ds-form-message {
  margin: 0;
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-error);
}
</style>
