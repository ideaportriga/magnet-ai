<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useConversationStore } from '@/stores/conversationStore'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

const convStore = useConversationStore()
const { conversation } = storeToRefs(convStore)
const crumbs = computed(() => [{ label: conversation.value?.name ?? '' }])
</script>
