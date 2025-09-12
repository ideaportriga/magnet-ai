<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='$emit("cancel")')
  q-card.card-style(style='min-width: 800px')
    q-card-section.card-section-style.q-mb-md
      .row
        .col
          .km-heading-7 New Action
        .col-auto
          q-btn(icon='close', flat, dense, @click='$emit("cancel")')
    q-card-section.card-section-style.q-mb-md
      .column.full-width
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
                    row-key='system_name',
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
      .row.q-mt-lg
        .col-auto
          km-btn(flat, label='Cancel', color='primary', @click='$emit("cancel")')
        .col
        .col-auto
          km-btn(label='Add', @click='create')
</template>
<script>
import { ref } from 'vue'

import { useChroma } from '@shared'
import { agentTopicActionsPopupColumns, agentTopicActionsAPIToolsPopupColumns } from '@/config/agents/topics'

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
    const { visibleRows: retrieval_tools } = useChroma('retrieval')
    const { visibleRows: prompt_templates } = useChroma('promptTemplates')
    const { visibleRows: mcp_servers } = useChroma('mcp_servers')

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
      stepper: ref(0),
      api_tools,
      rag_tools,
      retrieval_tools,
      prompt_templates,
      mcp_servers,
      agentTopicActionsPopupColumns,
      agentTopicActionsAPIToolsPopupColumns,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    actions() {
      return this.topic?.actions || []
    },
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
    columns() {
      return Object.values(this.tab == 'api' ? this.agentTopicActionsAPIToolsPopupColumns : this.agentTopicActionsPopupColumns)
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
  methods: {
    create() {
      // get current topics
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
          tool_provider: item.type === 'mcp_tool' ? item.tool_provider : null,
        }
      })

      this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
        arrayPath: 'topics',
        itemSystemName: this.topic?.system_name,
        data: {
          actions: [...actions, ...this.actions],
        },
      })

      this.$q.notify({
        position: 'top',
        message: 'New action(s) have been added',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })

      this.$emit('cancel')
    },
    getSelectedQtyByType(tab) {
      return this.selected.filter((item) => item.type === tab).length
    },
    selectRecord(row) {
      const index = this.selected.findIndex((item) => item?.id === row?.id)
      if (index === -1) {
        this.selected.push(row)
      } else {
        this.selected.splice(index, 1)
      }
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
