<script setup lang="ts">
/**
 * `<km-confirm-action>` — small inline confirmation dialog.
 *
 * The legacy component is mounted via Quasar's plugin Dialog API and
 * exposes `show()`/`hide()` instance methods. Modern code should use
 * `useDialog().confirm({ ... })` from `@ds/composables/useDialog` instead.
 *
 * To keep call sites compiling we still expose `show()`/`hide()` as exposed
 * methods, but the recommended migration is to switch to `useDialog`.
 */

import { ref } from 'vue'
import DsAlertDialog from '../primitives/Dialog/DsAlertDialog.vue'

withDefaults(
  defineProps<{
    title?: string
    description?: string
    confirmLabel?: string
    cancelLabel?: string
    tone?: 'neutral' | 'danger'
  }>(),
  {
    title: 'Confirm action',
    description: '',
    confirmLabel: 'Yes',
    cancelLabel: 'Go back',
    tone: 'neutral',
  },
)

const emit = defineEmits<{
  ok: []
  hide: []
}>()

const open = ref(false)

function show() { open.value = true }
function hide() { open.value = false; emit('hide') }
function onConfirm() { emit('ok'); hide() }
function onCancel() { hide() }

defineExpose({ show, hide })
</script>

<template>
  <DsAlertDialog
    v-model:open="open"
    :title="title"
    :description="description"
    :confirm-label="confirmLabel"
    :cancel-label="cancelLabel"
    :tone="tone"
    @confirm="onConfirm"
    @cancel="onCancel"
  />
</template>
