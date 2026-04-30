<script setup lang="ts">
/**
 * CommandDialog — a Command palette wrapped inside DsDialog. Renders the
 * title/description visually-hidden by default for accessibility.
 */
import type { DialogRootEmits, DialogRootProps } from 'reka-ui'
import { useForwardPropsEmits } from 'reka-ui'
import DsDialog from '../Dialog/DsDialog.vue'
import DsCommand from './DsCommand.vue'

const props = withDefaults(
  defineProps<DialogRootProps & { title?: string; description?: string }>(),
  {
    title: 'Command Palette',
    description: 'Search for a command to run...',
  },
)
const emits = defineEmits<DialogRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <DsDialog
    v-bind="forwarded"
    visually-hidden-title
    hide-close
    size="md"
  >
    <template #title>{{ title }}</template>
    <template #description>{{ description }}</template>

    <div class="ds-command-dialog" data-test="ds-command-dialog">
      <DsCommand>
        <slot />
      </DsCommand>
    </div>
  </DsDialog>
</template>

<style>
.ds-command-dialog {
  margin: calc(-1 * var(--ds-dialog-padding, var(--ds-space-lg)));
  overflow: hidden;
  border-radius: inherit;
}
</style>
