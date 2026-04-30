<template>
  <km-chip
    :tone="getTypeTone(type)"
    dense
    square
    icon="file"
    class="text-weight-medium text-caption py-md px-sm mx-0"
  >
    {{ label }}
  </km-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps<{
  type: string
}>()

const label = computed(() => String(props.type || '').toUpperCase())

function getTypeTone(type: string) {
  switch (String(type || '').toLowerCase()) {
    case 'pdf':
      return 'danger'
    case 'aspx':
    case 'html':
      return 'warning'
    case 'md':
    case 'markdown':
      return 'info'
    case 'txt':
    case 'text':
      return 'neutral-strong'
    case 'doc':
    case 'docx':
      return 'info'
    default:
      return 'neutral-strong'
  }
}
</script>


