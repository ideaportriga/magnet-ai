<template>
  <div class="q-mx-none" style="width: 60px">
    <q-chip color="grey-7" text-color="white" dense square class="text-weight-medium text-caption q-py-12 q-px-sm q-mx-none">
      {{ type.toUpperCase() }}
    </q-chip>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  type: string
}>()
</script>
