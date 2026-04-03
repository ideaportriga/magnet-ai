<template lang="pug">
.col-auto.q-py-auto.row.items-center.no-wrap.q-gap-8
  template(v-if='activeTabName')
    .km-body.text-primary.km-breadcrumb-link(@click='navigateToApp') {{ activeRagName }}
    q-icon.text-secondary-text.km-breadcrumb-sep(name='chevron_right', size='18px')
    .km-body {{ activeTabName }}
  template(v-else)
    .km-body {{ activeRagName }}
</template>

<script setup>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute, useRouter } from 'vue-router'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useEntityDetail } from '@/composables/useEntityDetail'

const route = useRoute()
const router = useRouter()
const { draft } = useEntityDetail('ai_apps')
const { options: items } = useCatalogOptions('ai_apps')

const activeRagId = computed(() => route.params.id)
const activeAIAppDB = computed(() => items.value.find((item) => item.id == activeRagId.value))
const activeRagName = computed(() => activeAIAppDB.value?.name)
const activeTabName = computed(() => {
  if (!route.params?.tab) return ''
  const tab = draft.value?.tabs?.find((t) => t.system_name === route.params.tab)
  return tab?.name || route.params.tab
})

const navigateToApp = () => {
  if (activeRagId.value) router.push(`/ai-apps/${activeRagId.value}`)
}
</script>
