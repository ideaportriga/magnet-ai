<script setup lang="ts">
/**
 * Renders programmatic confirmation dialogs queued via `useDialog().confirm`.
 * Mount once near the application root, alongside DsToastHost.
 */

import DsAlertDialog from '../components/primitives/Dialog/DsAlertDialog.vue'
import { dialogQueue, settleConfirm } from './dialogStore'
</script>

<template>
  <DsAlertDialog
    v-for="item in dialogQueue.items"
    :key="item.id"
    :open="item.open"
    :title="item.title"
    :description="item.description"
    :confirm-label="item.confirmLabel"
    :cancel-label="item.cancelLabel"
    :tone="item.tone"
    @confirm="settleConfirm(item.id, true)"
    @cancel="settleConfirm(item.id, false)"
    @update:open="(open: boolean) => !open && settleConfirm(item.id, false)"
  />
</template>
