<template>
  <km-inner-loading :showing="!currentTab" />
  <layouts-details-layout v-if="currentTab" :name="name" :description="description" :system-name="system_name" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #content>
      <div class="flex-none full-width">
        <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
          {{ m.label_tabType() }}
          <div class="full-width stack" data-gap="0">
            <km-radio v-model="tab_type" class="my-sm" name="tab_type" dense :label="m.label_ragTool()" val="RAG" />
            <km-radio v-model="tab_type" class="mb-sm" name="tab_type" dense :label="m.label_retrievalTool()" val="Retrieval" />
            <km-radio v-model="tab_type" class="mb-sm" name="tab_type" dense label="Custom" val="Custom" />
            <km-radio v-model="tab_type" class="mb-sm" name="tab_type" dense :label="m.label_agent()" val="Agent" />
          </div>
          <template v-if="tab_type === &quot;Custom&quot;">
            <div class="km-field text-secondary-text pb-xs pl-sm">
              {{ m.label_customCode() }}
              <km-codemirror v-model="config.jsonString" style="max-block-size: 600px" />
              <div class="km-description text-secondary-text pb-xs">{{ m.hint_enterCustomCodeJson() }}</div>
            </div>
          </template>
          <template v-else>
            <div class="flex-1 pt-md">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ tab_type }}</div>
              <km-select v-model="value" height="30px" :placeholder="tab_type" :options="options" has-dropdown-search option-value="value" />
            </div>
            <div class="cluster pt-sm">
              <km-btn flat simple :label="button_label" icon-size="16px" icon="chat" @click="openNewTab()" />
            </div>
          </template>
        </div>
      </div>
    </template>
    <template #drawer>
      <div class="flex-none" style="inline-size: 500px">
        <ai-apps-drawer :open="openTest" @update:open="openTest = $event" />
      </div>
    </template>
  </layouts-details-layout>
</template>

<script setup>
import { ref, computed, onActivated, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { cloneDeep } from 'lodash'
import { m } from '@/paraglide/messages'

const route = useRoute()
const router = useRouter()
const { draft, updateField } = useEntityDetail('ai_apps')

const openTest = ref(true)

const { options: ragToolsItems } = useCatalogOptions('rag_tools')
const { options: agentItems } = useCatalogOptions('agents')
const { options: retrievalItems } = useCatalogOptions('retrieval')

const activeAIAppTabSystemName = computed(() => route.params?.tab)
const activeAIAppTabChildSystemName = computed(() => route.query?.child)

const currentTab = computed(() => {
  const tabs = draft.value?.tabs || []
  const tab = tabs.find((el) => el.system_name === activeAIAppTabSystemName.value)
  if (activeAIAppTabChildSystemName.value) {
    return tab?.children?.find((el) => el.system_name === activeAIAppTabChildSystemName.value)
  }
  return tab
})

/**
 * Helper to update a property on the current tab (or child tab) within the tabs array.
 * Clones the tabs array, finds the target tab, applies newProperties, and writes back via updateField.
 */
function updateTabProperty(newProperties) {
  const tabs = cloneDeep(draft.value?.tabs || [])
  const tab = tabs.find((el) => el.system_name === activeAIAppTabSystemName.value)
  if (!tab) return

  if (activeAIAppTabChildSystemName.value) {
    const child = tab.children?.find((el) => el.system_name === activeAIAppTabChildSystemName.value)
    if (child) Object.assign(child, newProperties)
  } else {
    Object.assign(tab, newProperties)
  }
  updateField('tabs', tabs)
}

const name = computed({
  get() {
    return currentTab.value?.name || ''
  },
  set(value) {
    updateTabProperty({ name: value })
  },
})

const description = computed({
  get() {
    return currentTab.value?.description || ''
  },
  set(value) {
    updateTabProperty({ description: value })
  },
})

const system_name = computed({
  get() {
    return currentTab.value?.system_name || ''
  },
  set(value) {
    updateTabProperty({ system_name: value })
  },
})

const tab_type = computed({
  get() {
    return currentTab.value?.tab_type || ''
  },
  set(value) {
    updateTabProperty({ tab_type: value })
  },
})

const config = computed({
  get() {
    return currentTab.value?.config || ''
  },
  set(value) {
    updateTabProperty({ config: value })
  },
})

const store_keys = {
  RAG: 'rag_tool',
  Retrieval: 'retrieval_tool',
  Custom: 'custom_code',
  Agent: 'agent',
}
const button_label = computed(() => {
  if (tab_type.value === 'RAG') {
    return value.value ? 'Open RAG Tool' : 'Open RAG Tools Library'
  } else if (tab_type.value === 'Retrieval') {
    return value.value ? 'Open Retrieval Tool' : 'Open Retrieval Tools Library'
  } else if (tab_type.value === 'Custom') {
    return value.value ? 'Open Custom Code' : 'Open Custom Code Library'
  } else if (tab_type.value === 'Agent') {
    return value.value ? 'Open Agent' : 'Open Agents Library'
  }
  return ''
})

const path = computed(() => {
  let link = null
  if (tab_type.value === 'RAG') {
    link = `rag-tools/`
  } else if (tab_type.value === 'Retrieval') {
    link = `retrieval/`
  } else if (tab_type.value === 'Custom') {
    link = `custom-code/`
  } else if (tab_type.value === 'Agent') {
    link = `agents/`
  }
  if (link && value.value) {
    const systemName = typeof value.value === 'string' ? value.value : value.value.system_name
    const option = options.value.find((option) => option.system_name === systemName)
    if (option) {
      link += option.id
    }
  }
  return link
})
const store_key = computed(() => {
  return store_keys[tab_type.value]
})

const options = computed(() => {
  if (tab_type.value === 'RAG') {
    return ragToolsItems.value
  } else if (tab_type.value === 'Retrieval') {
    return retrievalItems.value
  } else if (tab_type.value === 'Custom') {
    return []
  } else if (tab_type.value === 'Agent') {
    return agentItems.value
  }
  return []
})
const value = computed({
  get() {
    return config.value[store_key.value]
  },
  set(value) {
    updateTabProperty({ config: { ...config.value, [store_key.value]: value.system_name } })
  },
})

const navigate = (path = '') => {
  if (route.path !== `/${path}`) {
    router.push(`${path}`)
  }
}

// In-app navigation now that workspaces handle multi-detail flows.
const openNewTab = () => {
  router.push(`/${path.value}`)
}
</script>
