<script setup lang="ts">
/**
 * SheetClose — element that closes the parent Sheet when activated.
 */
import type { DialogCloseProps } from 'reka-ui'
import { DialogClose } from 'reka-ui'

const props = defineProps<DialogCloseProps>()
</script>

<template>
  <DialogClose v-bind="props" data-test="ds-sheet-close">
    <slot />
  </DialogClose>
</template>
