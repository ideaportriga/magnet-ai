<template lang="pug">
layouts-details-layout(v-model:name='name', v-model:description='description', v-model:systemName='system_name')
  template(#breadcrumbs)
    .row.q-pb-md.relative-position.q-px-md
      q-breadcrumbs.text-grey(active-color='text-grey', gutter='lg')
        template(v-slot:separator)
          q-icon(size='12px', name='fas fa-chevron-right', color='text-grey')
        q-breadcrumbs-el
          .column
            .km-small-chip.text-grey.text-capitalize App
            .km-chip.text-grey-8.text-capitalize.breadcrumb-link(@click='navigate(`/ai-apps/${$route.params?.id}`)') {{ selectedRow?.name }}
        q-breadcrumbs-el
          .column
            .km-small-chip.text-grey.text-capitalize Tab
            .km-chip.text-grey-8.text-capitalize {{ name }}
  template(#content)
    .col-auto.full-width
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Tab type
        |
        .full-width.column
          q-radio.q-my-sm(name='tab_type', dense, label='RAG Tool', val='RAG', v-model='tab_type')
          q-radio.q-mb-sm(name='tab_type', dense, label='Retrieval Tool', val='Retrieval', v-model='tab_type')
          q-radio.q-mb-sm(name='tab_type', dense, label='Custom', val='Custom', v-model='tab_type')
          q-radio.q-mb-sm(name='tab_type', dense, label='Agent', val='Agent', v-model='tab_type')
        template(v-if='tab_type === "Custom"')
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Custom code
            km-codemirror(v-model='config.jsonString', style='max-height: 600px')
            .km-description.text-secondary-text.q-pb-4 Enter your custom code in JSON format
        template(v-else)
          .col.q-pt-md
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ tab_type }}
            km-select(height='30px', :placeholder='tab_type', :options='options', v-model='value', hasDropdownSearch, option-value='value')
          .row.q-pt-sm
            km-btn(flat, simple, :label='button_label', iconSize='16px', icon='fas fa-comment-dots', @click='openNewTab()')
  template(#drawer)
    .col-auto(style='width: 500px')
      ai-apps-drawer(v-model:open='openTest')
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useChroma } from '@shared'

const route = useRoute()
const router = useRouter()
const store = useStore()

const { publicItems: ragToolsItems } = useChroma('rag_tools')
const { publicItems: agentItems } = useChroma('agents')
const { publicItems: retrievalItems } = useChroma('retrieval')

const { selectedRow } = useChroma('ai_apps')

const activeAIAppTabSystemName = computed(() => route.params?.tab)
const activeAIAppTabChildSystemName = computed(() => route.query?.child)

const currentTab = computed(() => store.getters.getTabBySystemName(activeAIAppTabSystemName.value, activeAIAppTabChildSystemName.value))

const name = computed({
  get() {
    return currentTab.value?.name || ''
  },
  set(value) {
    store.commit('updateAIAppTabProperty', {
      system_name: activeAIAppTabSystemName.value,
      newProperties: { name: value },
      child_system_name: activeAIAppTabChildSystemName.value,
    })
  },
})

const description = computed({
  get() {
    return currentTab.value?.description || ''
  },
  set(value) {
    store.commit('updateAIAppTabProperty', {
      system_name: activeAIAppTabSystemName.value,
      newProperties: { description: value },
      child_system_name: activeAIAppTabChildSystemName.value,
    })
  },
})

const system_name = computed({
  get() {
    return currentTab.value?.system_name || ''
  },
  set(value) {
    store.commit('updateAIAppTabProperty', {
      system_name: activeAIAppTabSystemName.value,
      newProperties: { system_name: value },
      child_system_name: activeAIAppTabChildSystemName.value,
    })
  },
})

const tab_type = computed({
  get() {
    return currentTab.value?.tab_type || ''
  },
  set(value) {
    store.commit('updateAIAppTabProperty', {
      system_name: activeAIAppTabSystemName.value,
      newProperties: { tab_type: value },
      child_system_name: activeAIAppTabChildSystemName.value,
    })
  },
})

const config = computed({
  get() {
    return currentTab.value?.config || ''
  },
  set(value) {
    store.commit('updateAIAppTabProperty', {
      system_name: activeAIAppTabSystemName.value,
      newProperties: { config: value },
      child_system_name: activeAIAppTabChildSystemName.value,
    })
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
    config.value[store_key.value] = value.system_name
  },
})

const navigate = (path = '') => {
  if (route.path !== `/${path}`) {
    router.push(`${path}`)
  }
}

const openNewTab = () => {
  window.open(router.resolve({ path: `/${path.value}` }).href, '_blank')
}

watch(selectedRow, (newVal, oldVal) => {
  if (newVal?.id !== oldVal?.id) {
    store.commit('setAIApp', newVal)
  }
})

onMounted(() => {
  if (selectedRow.value?.id !== store.getters.ai_app?.id) {
    store.commit('setAIApp', selectedRow.value)
  }
})
</script>

<style lang="stylus"></style>
