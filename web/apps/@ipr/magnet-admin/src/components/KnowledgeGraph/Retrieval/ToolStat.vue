<template>
  <div class="tool-stat">
    <q-icon :name="icon" size="14px" color="grey-7" class="q-mr-xs" />
    <span class="text-caption text-grey-8 km-tiny">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
defineProps<{
  icon: string
  label: string
}>()
</script>

<style scoped>
.tool-stat {
  display: flex;
  align-items: center;
}
</style>
