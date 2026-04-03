<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ activeRecordName }}
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { m } from '@/paraglide/messages'

const ntStore = useNoteTakerStore()
const activeRecordName = computed(() => ntStore.activeRecord?.name || m.entity_noteTaker())
</script>
