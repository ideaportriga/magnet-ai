<template lang="pug">
div
  km-section(title='LLM instructions', subTitle='Instructions for the Language model that help Agents execute Action')
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 Name for the LLM
      |
      km-input(ref='input', placeholder='Name for the LLM', border-radius='8px', height='36px', v-model='function_name')
        .km-field.text-secondary-text.q-pb-sm.q-pl-8 Helps LLM find and execute Action. Must be unique within the Topic. Cannot contain spaces.
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 Description for the LLM
      km-input(ref='input', rows='8', border-radius='8px', height='36px', type='textarea', v-model='function_description')
  q-separator.q-my-lg
  km-section(title='Display settings', subTitle='Configure information about the Action that is displayed to end user')
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 Display name
      km-input(ref='input', placeholder='Display name', border-radius='8px', height='36px', v-model='display_name')
      .km-field.text-secondary-text.q-pb-sm.q-pl-8 This name will be displayed for the end user when the action is selected by an Agent. Keep it short and non-technical.
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 Display description
      km-input(ref='input', placeholder='Display description', border-radius='8px', height='36px', v-model='display_description')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 This description will be displayed for the end user when the action is selected by an Agent. Keep it short and non-technical.
  q-separator.q-my-lg
  km-section(title='Tool of origin', subTitle='Tool from which the Action was created')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Tool of origin
      .row.items-center
        .col-auto.q-mr-8
          km-chip(round, size='24px', :label='getToolTypeLabel(action?.type)', color='primary-light', text-color='primary')
        .col.q-mr-8
          km-input(ref='input', readonly, placeholder='Display description', border-radius='8px', height='36px', v-model='tool_name')
    .row
      .col-auto.q-mr-8
        km-btn(flat, simple, :label='`Open ${getToolTypeLabel(action?.type)}`', iconSize='16px', icon='fas fa-arrow-right', @click='openTool')
</template>

<script>
import { useChroma } from '@shared'

export default {
  emits: ['openTest'],
  setup() {
    const { items: promptTemplateItems } = useChroma('promptTemplates')
    const { items: ragItems } = useChroma('rag_tools')
    const { items: apiServers } = useChroma('api_servers')

    return {
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
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    action() {
      return this.topic?.actions?.find((action) => action?.system_name == this.routeParams?.actionId)
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
        { name: 'api', label: 'API Tool' },
        { name: 'rag', label: 'RAG Tool' },
        { name: 'prompt_template', label: 'Prompt Template' },
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
