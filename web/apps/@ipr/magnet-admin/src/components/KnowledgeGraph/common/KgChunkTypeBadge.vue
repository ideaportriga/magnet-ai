<template>
  <div class="q-mx-none" style="width: 60px">
    <q-chip color="grey-7" text-color="white" dense square class="text-weight-medium text-caption q-py-12 q-px-sm q-mx-none">
      {{ label }}
    </q-chip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  type: string
}>()

const label = computed(() => String(props.type || '').toUpperCase())
</script>


