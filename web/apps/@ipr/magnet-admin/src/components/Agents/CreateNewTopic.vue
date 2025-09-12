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
          :steps='[ { step: 0, description: "Topic settings", icon: "pen" }, { step: 1, description: "Add actions", icon: "circle" }, { step: 2, description: "Instructions", icon: "circle" }, ]',
          :stepper='stepper'
        )
      .column.full-width(v-if='stepper === 0')
        .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-lg
          q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
          .km-paragraph.q-pb-4 Give your Topic a name and internal description. You will be able to add LLM instructions later.
        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
          .full-width
            km-input(height='30px', placeholder='E.g. Topic 1', v-model='name', ref='nameRef')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Description
          .full-width
            km-input(height='30px', placeholder='E.g. Topic 1 description', v-model='topic.description', ref='descriptionRef')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
          .full-width
            km-input(height='30px', placeholder='E.g. TOPIC_1', v-model='system_name', ref='system_nameRef')
          .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
      .column.full-width(v-if='stepper === 1')
        .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-lg
          q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
          .km-paragraph.q-pb-4 Select tools to serve as Actions that can be performed within this Topic.
        div
          q-tabs.bb-border.full-width(
            v-model='tab',
            narrow-indicator,
            dense,
            align='left',
            active-color='primary',
            indicator-color='primary',
            active-bg-color='white',
            no-caps,
            content-class='km-tabs'
          )
            template(v-for='t in tabs')
              q-tab(:name='t.name')
                .row.q-mx-md(style='height: 24px')
                  .col.km-title {{ t.label }}
                  .col-auto.q-ml-sm(v-if='getSelectedQtyByType(t.name) > 0')
                    km-chip(round, size='24px', :label='getSelectedQtyByType(t.name)', color='primary-light', text-color='primary')

        .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 360px) !important')
          .row
            .col-auto.center-flex-y
            km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
          .row.q-gap-16.full-height.full-width
            .col.full-height.full-width
              .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                .col-auto.full-width(v-if='tab != "mcp_tool"')
                  km-table-new(
                    @selectRow='selectRecord',
                    selection='multiple',
                    row-key='id',
                    :active-record-id='selectedRow?.id',
                    v-model:selected='selected',
                    :columns='columns',
                    :rows='rows ?? []',
                    binary-state-sort,
                    :infinite-scroll='true'
                  )
                .col-auto.full-width(v-else)
                  agents-select-section(
                    v-for='(server, index) in mcp_servers',
                    :key='server.id',
                    :server='server',
                    :selected='selected',
                    @select='selectRecord',
                    :open-on-mount='index == 0'
                  )

      .column.full-width(v-if='stepper === 2')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Advanced instructions
          km-input(ref='input', rows='8', border-radius='8px', height='36px', type='textarea', v-model='instructions')
          .km-description.text-secondary-text.q-pb-4.q-mt-xs LLM settings for this prompt are defined by the Prompt Template that the Agent uses for Topic processing.
      .row.q-mt-lg
        template(v-if='stepper === 0')
          .col-auto.q-mr-sm
            km-btn(flat, label='Cancel', color='primary', @click='$emit("cancel")')
          .col
          .col-auto
            km-btn(label='Next', @click='proceed', :disable='!readyForNext')
        template(v-else-if='stepper === 1')
          .col-auto.q-mr-sm
            km-btn(flat, label='Cancel', color='primary', @click='$emit("cancel")')
          .col
          .col-auto.q-mr-sm
            km-btn(flat, label='Back', @click='stepper--')
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
    const { visibleRows: api_tools } = useChroma('api_tools')
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
      api_tools,
      mcp_servers,
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
      if (this.tab === 'api') return this.getList(this.api_tools, 'api')
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
