<template>
  <q-chip
    :color="getTypeColor(type)"
    text-color="white"
    dense
    square
    icon="insert_drive_file"
    class="text-weight-medium text-caption q-py-12 q-px-sm q-mx-none"
  >
    {{ type.toUpperCase() }}
  </q-chip>
</template>

<script setup lang="ts">
defineProps<{
  type: string
}>()

const getTypeColor = (type: string) => {
  switch (type?.toLowerCase()) {
    case 'pdf':
      return 'red-7'
    case 'html':
      return 'orange-7'
    case 'md':
    case 'markdown':
      return 'blue-7'
    case 'txt':
    case 'text':
      return 'grey-7'
    case 'doc':
    case 'docx':
      return 'blue-9'
    default:
      return 'grey-5'
  }
}
</script>
