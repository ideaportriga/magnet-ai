<template lang="pug">
div
  .km-field.text-secondary-text.q-pb-sm.q-pl-8 Name for LLM
    km-input(ref='input', placeholder='Name for the LLM', border-radius='8px', height='36px', v-model='function_name')
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 Helps LLM find and execute Action. Must be unique within the Topic. Cannot contain spaces.
  .km-field.text-secondary-text.q-pb-sm.q-pl-8 Description for LLM
    km-input(ref='input', rows='8', border-radius='8px', height='36px', type='textarea', v-model='function_description')

  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Tool of origin
  .row.q-gap-8.items-center.q-pl-8
    .km-label {{ tool_name }}
    q-icon.cursor-pointer(name='fa fa-external-link', color='secondary', size='10', @click='openTool', v-if='tool_name')
    km-chip.text-grey.q-ml-sm(:label='getToolTypeLabel(action?.type)', color='in-progress')
  template(v-if='action?.type === "mcp_tool"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-sm Tool provider
    .row.q-gap-8.items-center.q-pl-8
      .km-label {{ tool_object?.name }}
      q-icon.cursor-pointer(
        name='fa fa-external-link',
        color='secondary',
        size='10',
        @click='navigate(`mcp/${tool_object?.id}`)',
        v-if='tool_object?.name'
      )
      km-chip.text-grey.q-ml-sm(label='MCP Server', color='in-progress')
</template>

<script>
import { useChroma } from '@shared'

export default {
  emits: ['openTest'],
  setup() {
    const { items: promptTemplateItems } = useChroma('promptTemplates')
    const { items: ragItems } = useChroma('rag_tools')
    const { items: apiServers } = useChroma('api_servers')
    const { items: mcpItems } = useChroma('mcp_servers')
    const { items: retrievalItems } = useChroma('retrieval')

    return {
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
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    action() {
      return this.topic?.actions?.find((action) => action?.system_name == this.activeTopic?.action)
    },
    activeTopic: {
      get() {
        return this.$store.getters.activeTopic
      },
      set(value) {
        this.$store.commit('setActiveTopic', value)
      },
    },
    name: {
      get() {
        return this.action?.name || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
      }
    },
    getToolTypeLabel(name) {
      const dict = [
        { name: 'api', label: 'API Tool' },
        { name: 'rag', label: 'RAG Tool' },
        { name: 'prompt_template', label: 'Prompt Template' },
        { name: 'mcp_tool', label: 'MCP Tool' },
        { name: 'retrieval', label: 'Retrieval Tool' },
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
