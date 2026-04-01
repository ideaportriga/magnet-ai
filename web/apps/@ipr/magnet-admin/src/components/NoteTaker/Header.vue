<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ activeRecordName }}
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNoteTakerStore } from '@/stores/noteTakerStore'

const ntStore = useNoteTakerStore()
const activeRecordName = computed(() => ntStore.activeRecord?.name || 'Note Taker')
</script>
