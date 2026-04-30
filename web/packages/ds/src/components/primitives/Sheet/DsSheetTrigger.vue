<script setup lang="ts">
/**
 * SheetTrigger — element whose activation opens the parent Sheet.
 */
import type { DialogTriggerProps } from 'reka-ui'
import { DialogTrigger } from 'reka-ui'

const props = defineProps<DialogTriggerProps>()
</script>

<template>
  <DialogTrigger v-bind="props" data-test="ds-sheet-trigger">
    <slot />
  </DialogTrigger>
</template>
