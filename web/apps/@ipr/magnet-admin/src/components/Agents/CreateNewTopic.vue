<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='$emit("cancel")')
  q-card.card-style(style='min-width: 800px')
    q-card-section.card-section-style
      .row
        .col
          .km-heading-7 New Topic
        .col-auto
          q-btn(icon='close', flat, dense, @click='$emit("cancel")')
    q-card-section.card-section-style.q-mb-md
      .row.items-center.justify-center
        km-stepper.full-width(
          :steps='[ { step: 0, description: "Topic settings", icon: "pen" }, { step: 1, description: "Add actions", icon: "circle" }, ]',
          :stepper='stepper'
        )
      .column.full-width(v-if='stepper === 0')
        km-notification-text.q-mb-md(notification='Give your Topic a name and internal description. You will be able to add LLM instructions later.')
        .km-field.text-secondary-text.q-pl-8.q-mb-md Name
        km-input.q-mb-md(height='30px', v-model='name', ref='nameRef')
        .km-field.text-secondary-text.q-pl-8 Description for LLM
        km-input.q-mb-sm(type='textarea', rows='4', v-model='topic.description', ref='descriptionRef')
        km-notification-text.q-mb-md(notification='Instructions for the LLM explaining when this topic should be used')
        .km-field.text-secondary-text.q-pl-8 System name
        km-input.q-mb-md(height='30px', v-model='system_name', ref='system_nameRef')
          .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
      agents-tool-selection(v-model:selected='selected', v-if='stepper === 1')
      .row.q-mt-lg
        template(v-if='stepper === 0')
          .col-auto.q-mr-sm
            km-btn(flat, label='Cancel', color='primary', @click='$emit("cancel")')
          .col
          .col-auto
            km-btn(label='Next', @click='proceed', :disable='!readyForNext')

        template(v-else)
          .col-auto.q-mr-sm
            km-btn(flat, label='Cancel', color='primary', @click='$emit("cancel")')
          .col
          .col-auto.q-mr-sm
            km-btn(v-if='stepper != 0', flat, label='Previous', color='primary', @click='stepper--')
          .col-auto
            km-btn(label='Create', @click='create')
</template>
<script>
import { ref } from 'vue'

import { useChroma } from '@shared'
import { agentTopicActionsPopupColumns, agentTopicActionsAPIToolsPopupColumns } from '@/config/agents/topics'
import { toUpperCaseWithUnderscores } from '@shared'

export default {
  props: {
    showNewDialog: {
      default: false,
      type: Boolean,
    },
  },
  emits: ['cancel'],
  setup() {
    const { visibleRows: api_servers } = useChroma('api_servers')
    const { visibleRows: rag_tools } = useChroma('rag_tools')
    const { visibleRows: prompt_templates } = useChroma('promptTemplates')
    const { visibleRows: mcp_servers } = useChroma('mcp_servers')
    const { visibleRows: retrieval_tools } = useChroma('retrieval')

    return {
      searchString: ref(''),
      tabs: ref([
        { name: 'api', label: 'API Tools' },
        { name: 'mcp_tool', label: 'MCP Tools' },
        { name: 'rag', label: 'RAG Tools' },
        { name: 'retrieval', label: 'Retrieval Tools' },
        { name: 'prompt_template', label: 'Prompt Templates' },
      ]),
      tab: ref('api'),
      selected: ref([]),
      topic: ref({
        name: '',
        description: '',
        system_name: '',
      }),
      stepper: ref(0),
      mcp_servers,
      api_servers,
      rag_tools,
      prompt_templates,
      retrieval_tools,
      agentTopicActionsPopupColumns,
      agentTopicActionsAPIToolsPopupColumns,
      autoChangeCode: ref(true),
      isMounted: ref(false),
    }
  },
  computed: {
    rows() {
      if (this.tab === 'rag') return this.getList(this.rag_tools, 'rag')
      if (this.tab === 'retrieval') return this.getList(this.retrieval_tools, 'retrieval')
      if (this.tab === 'prompt_template')
        return this.getList(
          (this.prompt_templates || []).filter((el) => el?.category === 'prompt_tool'),
          'prompt_template'
        )

      return []
    },
    name: {
      get() {
        return this.topic?.name || ''
      },
      set(val) {
        this.topic.name = val
        if (this.autoChangeCode && this.isMounted) this.topic.system_name = toUpperCaseWithUnderscores(val)
      },
    },
    system_name: {
      get() {
        return this.topic?.system_name || ''
      },
      set(val) {
        this.topic.system_name = val
        this.autoChangeCode = false
      },
    },
    instructions: {
      get() {
        return this.topic?.instructions || ''
      },
      set(val) {
        this.topic.instructions = val
      },
    },
    columns() {
      return Object.values(this.tab === 'api' ? this.agentTopicActionsAPIToolsPopupColumns : this.agentTopicActionsPopupColumns)
    },

    readyForNext() {
      return !!this.topic?.name && !!this.topic?.system_name
    },
    allSelected() {
      return this.apiTools.every((tool) => tool.selected === true)
    },
    topicSelectionPromptTemplate: {
      get() {
        return this.selectionPromptName
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'prompt_templates.classification', value: value.system_name })
      },
    },
  },
  mounted() {
    this.isMounted = true
  },
  beforeUnmount() {
    this.isMounted = false
    this.$emit('cancel')
  },
  methods: {
    selectRecord(row) {
      const index = this.selected.findIndex((item) => item?.id === row?.id)
      if (index === -1) {
        this.selected.push(row)
      } else {
        this.selected.splice(index, 1)
      }
    },
    getSelectedQtyByType(tab) {
      return this.selected.filter((item) => item.type === tab).length
    },
    create() {
      // get current topics
      const topics = this.$store.getters.agentDetailVariant?.value?.topics || []
      const actions = this.selected.map((item) => {
        return {
          name: item.name,
          system_name: item.system_name,
          description: item.description,
          type: item.type,
          tool_system_name: item.system_name,
          function_name: (item.name || '').replace(/[^a-zA-Z0-9_\\.-]/g, ''),
          function_description: (item?.name ?? '') + ':' + (item?.description ?? ''),
          display_name: item.name,
          display_description: item.description,
          metadata: {
            created_at: new Date().toISOString(),
            modified_at: new Date().toISOString(),
          },
          tool_provider: item.tool_provider,
        }
      })
      const newTopic = {
        ...this.topic,
        metadata: {
          created_at: new Date().toISOString(),
          modified_at: new Date().toISOString(),
        },
        actions,
      }

      topics.push(newTopic)

      this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'topics', value: topics })

      this.$q.notify({
        position: 'top',
        message: 'New topic have been added',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })

      this.$emit('cancel')
    },
    getList(list, type) {
      //  filter by searchString by all columns

      return list
        .map((item) => {
          return {
            id: item.id,
            name: item.name,
            description: item.description,
            system_name: item.system_name,
            type,
          }
        })
        .filter((item) => {
          return Object.values(item).some((value) => {
            return value.toString().toLowerCase().includes(this.searchString.toLowerCase())
          })
        })
    },
    updateTool(index, value) {
      Object.assign(this.apiTools[index], { selected: value })
    },
    proceed() {
      this.stepper++
    },
  },
}
</script>
<style lang="stylus">
.no-header thead
  display: none
</style>
