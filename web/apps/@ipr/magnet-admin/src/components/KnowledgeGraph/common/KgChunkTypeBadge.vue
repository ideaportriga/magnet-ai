<template>
  <div class="mx-0" style="inline-size: 60px">
    <km-chip tone="neutral-strong" dense square class="text-weight-medium text-caption py-md px-sm mx-0">
      {{ label }}
    </km-chip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps<{
  type: string
}>()

const label = computed(() => String(props.type || '').toUpperCase())
</script>


