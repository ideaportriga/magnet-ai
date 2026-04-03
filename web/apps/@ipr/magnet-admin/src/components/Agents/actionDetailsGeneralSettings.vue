<template lang="pug">
div
  km-section(:title='m.section_llmInstructions()', :subTitle='m.subtitle_llmInstructions()')
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.agents_nameForLlm() }}
      |
      km-input(ref='input', :placeholder='m.agents_nameForLlm()', border-radius='8px', height='36px', v-model='function_name')
        .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.agents_nameLlmHelp() }}
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.agents_descriptionForLlm() }}
      km-input(ref='input', rows='8', border-radius='8px', height='36px', type='textarea', v-model='function_description')
  q-separator.q-my-lg
  km-section(:title='m.section_displaySettings()', :subTitle='m.subtitle_configureActionDisplay()')
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.agents_displayName() }}
      km-input(ref='input', :placeholder='m.agents_displayName()', border-radius='8px', height='36px', v-model='display_name')
      .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.agents_displayNameHelp() }}
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.agents_displayDescription() }}
      km-input(ref='input', :placeholder='m.agents_displayDescription()', border-radius='8px', height='36px', v-model='display_description')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.agents_displayDescriptionHelp() }}
  q-separator.q-my-lg
  km-section(:title='m.section_toolOfOrigin()', :subTitle='m.subtitle_toolOfOrigin()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.agents_toolOfOriginLabel() }}
      .row.items-center
        .col-auto.q-mr-8
          km-chip(round, size='24px', :label='getToolTypeLabel(action?.type)', color='primary-light', text-color='primary')
        .col.q-mr-8
          km-input(ref='input', readonly, :placeholder='m.agents_displayDescription()', border-radius='8px', height='36px', v-model='tool_name')
    .row
      .col-auto.q-mr-8
        km-btn(flat, simple, :label='m.agents_openTool({ toolType: getToolTypeLabel(action?.type) })', iconSize='16px', icon='fas fa-arrow-right', @click='openTool')
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  emits: ['openTest'],
  setup() {
    const { activeVariant, updateNestedListItemBySystemName } = useAgentEntityDetail()
    const queries = useEntityQueries()
    const { options: promptTemplateItems } = useCatalogOptions('promptTemplates')
    const { options: ragItems } = useCatalogOptions('rag_tools')
    const { data: apiServersData } = queries.api_servers.useList()
    const apiServers = computed(() => apiServersData.value?.items ?? [])

    return {
      m,
      activeVariant,
      updateNestedListItemBySystemName,
      promptTemplateItems,
      ragItems,
      apiServers,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    action() {
      return this.topic?.actions?.find((action) => action?.system_name == this.routeParams?.actionId)
    },
    name: {
      get() {
        return this.action?.name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            name: value,
          },
        })
      },
    },
    description: {
      get() {
        return this.action?.description || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            description: value,
          },
        })
      },
    },
    system_name: {
      get() {
        return this.action?.system_name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            system_name: value,
          },
        })
      },
    },
    function_name: {
      get() {
        return this.action?.function_name
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            function_name: value,
          },
        })
      },
    },
    function_description: {
      get() {
        return this.action?.function_description
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            function_description: value,
          },
        })
      },
    },
    display_name: {
      get() {
        return this.action?.display_name
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            display_name: value,
          },
        })
      },
    },
    display_description: {
      get() {
        return this.action?.display_description
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            display_description: value,
          },
        })
      },
    },
    tool_object: {
      get() {
        if (this.action?.type === 'prompt_template') {
          return this.promptTemplateItems.find((item) => item.system_name === this.action?.tool_system_name)
        } else if (this.action?.type === 'rag') {
          return this.ragItems.find((item) => item.system_name === this.action?.tool_system_name)
        } else if (this.action?.type === 'api') {
          const server = this.apiServers.find((item) => item.system_name === this.action?.tool_provider)
          const tool = server?.tools?.find((item) => item.system_name === this.action?.tool_system_name)
          return {
            ...tool,
            server_id: server?.id,
          }
        }

        return {}
      },
    },
    tool_name() {
      return this.tool_object?.name
    },
  },
  methods: {
    openTool() {
      if (this.action?.type === 'prompt_template') {
        this.navigate(`prompt-templates/${this.tool_object?.id}`)
      } else if (this.action?.type === 'rag') {
        this.navigate(`rag-tools/${this.tool_object?.id}`)
      } else if (this.action?.type === 'api') {
        this.navigate(`api-servers/${this.tool_object?.server_id}/tools/${this.tool_object?.id}`)
      }
    },
    getToolTypeLabel(name) {
      const dict = [
        { name: 'api', label: this.m.agents_apiTool() },
        { name: 'rag', label: this.m.agents_ragTool() },
        { name: 'prompt_template', label: this.m.common_promptTemplate() },
      ]

      return dict.find((item) => item.name === name)?.label || name
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
