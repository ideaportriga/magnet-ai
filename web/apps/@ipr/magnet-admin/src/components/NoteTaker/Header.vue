<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { m } from '@/paraglide/messages'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

const ntStore = useNoteTakerStore()
const activeRecordName = computed(() => ntStore.activeRecord?.name || m.entity_noteTaker())
const crumbs = computed(() => [{ label: activeRecordName.value }])
</script>
