<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useEntityDetail } from '@/composables/useEntityDetail'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

const { draft } = useEntityDetail('provider')
const crumbs = computed(() => [{ label: draft.value?.name ?? '' }])
</script>
