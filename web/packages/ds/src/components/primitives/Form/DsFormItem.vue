<script setup lang="ts">
/**
 * FormItem — provides a unique field id to descendant FormLabel/FormControl/
 * FormDescription/FormMessage so labels and aria-* references all link up.
 *
 *   <DsFormItem>
 *     <DsFormLabel>Email</DsFormLabel>
 *     <DsFormControl><DsInput v-model="value" /></DsFormControl>
 *     <DsFormDescription>...</DsFormDescription>
 *     <DsFormMessage />
 *   </DsFormItem>
 */

import { useId } from 'reka-ui'
import { provide } from 'vue'
import { FORM_ITEM_INJECTION_KEY } from './injectionKeys'

const id = useId()
provide(FORM_ITEM_INJECTION_KEY, id)
</script>

<template>
  <div class="ds-form-item" data-test="ds-form-item">
    <slot />
  </div>
</template>

<style>
.ds-form-item {
  display: grid;
  gap: var(--ds-space-xs);
}
</style>
