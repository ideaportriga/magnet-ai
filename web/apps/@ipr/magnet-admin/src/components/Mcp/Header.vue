<template lang="pug">
.col-auto.q-py-auto.row.items-center.no-wrap.q-gap-8
  template(v-if='activeToolName')
    .km-body.text-primary.km-breadcrumb-link(@click='navigateToServer') {{ server?.name }}
    q-icon.text-secondary-text.km-breadcrumb-sep(name='chevron_right', size='18px')
    .km-body {{ activeToolName }}
  template(v-else)
    .km-body {{ server?.name }}
</template>
<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEntityDetail } from '@/composables/useEntityDetail'

const { draft } = useEntityDetail('mcp_servers')
const route = useRoute()
const router = useRouter()

const server = computed(() => draft.value)
const activeToolName = computed(() => route.params?.name || '')
const navigateToServer = () => {
  if (server.value?.id) router.push(`/mcp/${server.value.id}`)
}
</script>
