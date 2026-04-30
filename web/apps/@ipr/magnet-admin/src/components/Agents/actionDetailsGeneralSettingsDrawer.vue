<template>
  <div>
    <div class="km-field text-secondary-text pb-sm pl-sm">
      {{ m.agents_nameForLlmShort() }}
      <km-input ref="input" v-model="function_name" :placeholder="m.agents_nameForLlm()" border-radius="8px" height="36px" />
      <div class="km-field text-secondary-text pb-sm pl-sm">{{ m.agents_nameLlmHelp() }}</div>
    </div>
    <div class="km-field text-secondary-text pb-sm pl-sm">
      {{ m.agents_descriptionForLlmShort() }}
      <km-input ref="input" v-model="function_description" rows="8" border-radius="8px" height="36px" type="textarea" />
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.agents_toolOfOriginLabel() }}</div>
    <div class="cluster pl-sm" data-gap="sm">
      <div class="km-label">{{ tool_name }}</div>
      <km-glyph v-if="tool_name" class="cursor-pointer" name="external-link" size="10" @click="openTool" />
      <km-chip class="text-grey ml-sm" :label="getToolTypeLabel(action?.type)" tone="neutral" />
    </div>
    <template v-if="action?.type === &quot;mcp_tool&quot;">
      <div class="km-field text-secondary-text pb-xs pl-sm mt-sm">{{ m.agents_toolProvider() }}</div>
      <div class="cluster pl-sm" data-gap="sm">
        <div class="km-label">{{ tool_object?.name }}</div>
        <km-glyph v-if="tool_object?.name" class="cursor-pointer" name="external-link" size="10" @click="navigate(`mcp/${tool_object?.id}`)" />
        <km-chip class="text-grey ml-sm" :label="m.entity_mcpServer()" tone="neutral" />
      </div>
    </template>
  </div>
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
    const { activeVariant, activeTopic: activeTopicRef, updateNestedListItemBySystemName } = useAgentEntityDetail()
    const queries = useEntityQueries()
    const { options: promptTemplateItems } = useCatalogOptions('promptTemplates')
    const { options: ragItems } = useCatalogOptions('rag_tools')
    const { options: retrievalItems } = useCatalogOptions('retrieval')
    const { data: apiServersData } = queries.api_servers.useList()
    const apiServers = computed(() => apiServersData.value?.items ?? [])
    const { data: mcpData } = queries.mcp_servers.useList()
    const mcpItems = computed(() => mcpData.value?.items ?? [])

    return {
      m,
      activeVariant,
      activeTopicRef,
      updateNestedListItemBySystemName,
      promptTemplateItems,
      ragItems,
      apiServers,
      mcpItems,
      retrievalItems,
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
      return this.topic?.actions?.find((action) => action?.system_name == this.activeTopic?.action)
    },
    activeTopic: {
      get() {
        return this.activeTopicRef
      },
      set(value) {
        this.activeTopicRef = value
      },
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
        } else if (this.action?.type === 'mcp_tool') {
          return this.mcpItems.find((item) => item.system_name === this.action?.tool_provider)
        } else if (this.action?.type === 'retrieval') {
          return this.retrievalItems.find((item) => item.system_name === this.action?.tool_system_name)
        } else if (this.action?.type === 'knowledge_graph') {
          return {
            name: `${this.action?.tool_provider} / ${this.action?.tool_system_name}`,
            system_name: this.action?.tool_provider,
          }
        }
        return {}
      },
    },
    tool_name() {
      if (this.action?.type === 'mcp_tool') {
        return this.tool_object?.tools?.find((tool) => tool.name === this.action?.tool_system_name)?.name
      }
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
        this.navigate(`api-servers/${this.tool_object?.server_id}/tools/${this.tool_object?.system_name}`)
      } else if (this.action?.type === 'mcp_tool') {
        this.navigate(`mcp/${this.tool_object?.id}/tools/${this.tool_name}`)
      } else if (this.action?.type === 'retrieval') {
        this.navigate(`retrieval/${this.tool_object?.id}`)
      } else if (this.action?.type === 'knowledge_graph') {
        this.navigate(`knowledge-graph/${this.tool_object?.id || ''}`)
      }
    },
    getToolTypeLabel(name) {
      const dict = [
        { name: 'api', label: this.m.agents_apiTool() },
        { name: 'rag', label: this.m.agents_ragTool() },
        { name: 'prompt_template', label: this.m.common_promptTemplate() },
        { name: 'mcp_tool', label: this.m.agents_mcpTool() },
        { name: 'retrieval', label: this.m.agents_retrievalToolLabel() },
        { name: 'knowledge_graph', label: this.m.agents_knowledgeGraphLabel() },
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
