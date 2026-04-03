<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='$emit("cancel")')
  q-card.card-style(style='min-width: 800px')
    q-card-section.card-section-style
      .row
        .col
          .km-heading-7 {{ m.agents_newAction() }}
        .col-auto
          q-btn(icon='close', flat, dense, @click='$emit("cancel")')
    q-card-section.card-section-style.q-mb-md
      agents-tool-selection(v-model:selected='selected')
        //- .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
        //-   .row
        //-     .col-auto.center-flex-y
        //-     km-input(:placeholder='m.common_search()', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
        //-   .row.q-gap-16.full-height.full-width  
        //-     .col.full-height.full-width
        //-       .column.items-center.full-height.full-width.q-gap-16.overflow-auto
        //-         .col-auto.full-width(v-if='tab != "mcp_tool" && tab != "api"')
        //-           km-table-new(
        //-             @selectRow='selectRecord',
        //-             selection='multiple',
        //-             row-key='system_name',
        //-             :active-record-id='selectedRow?.id',
        //-             v-model:selected='selected',
        //-             :columns='columns',
        //-             :rows='rows ?? []',
        //-             binary-state-sort,
        //-             :infinite-scroll='true'
        //-           )
        //-         .col-auto.full-width(v-if='tab == "mcp_tool"')
        //-           agents-select-section(
        //-             v-for='(server, index) in mcp_servers',
        //-             :searchString='searchString',
        //-             :key='server.id',
        //-             :server='server',
        //-             :selected='selected',
        //-             @select='selectRecord',
        //-             type='mcp_tool',
        //-             system-name-key='name'
        //-           )
        //-         .col-auto.full-width(v-if='tab == "api"')
        //-           agents-select-section(
        //-             v-for='(server, index) in api_servers',
        //-             :key='server.id',
        //-             :server='server',
        //-             :selected='selected',
        //-             @select='selectRecord',
        //-             type='api',
        //-             system-name-key='system_name',
        //-             :search-fields='["name", "description", "system_name"]',
        //-             :search-string='searchString'
        //-           )
      .row.q-mt-lg
        .col-auto
          km-btn(flat, :label='m.common_cancel()', color='primary', @click='$emit("cancel")')
        .col
        .col-auto
          km-btn(:label='m.common_add()', @click='create')
</template>
<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
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
    const queries = useEntityQueries()

    const { options: api_servers } = useCatalogOptions('api_servers')
    const { options: rag_tools } = useCatalogOptions('rag_tools')
    const { options: retrieval_tools } = useCatalogOptions('retrieval')
    const { options: mcp_servers } = useCatalogOptions('mcp_servers')

    const { data: promptTemplatesData } = queries.promptTemplates.useList()
    const prompt_templates = computed(() => promptTemplatesData.value?.items ?? [])

    const { activeVariant, updateVariantField, updateNestedListItemBySystemName } = useAgentEntityDetail()
    return {
      m,
      activeVariant,
      updateVariantField,
      updateNestedListItemBySystemName,
      searchString: ref(''),
      tabs: ref([
        { name: 'api', label: m.agents_apiTools() },
        { name: 'mcp_tool', label: m.agents_mcpTools() },
        { name: 'rag', label: m.agents_ragTools() },
        { name: 'retrieval', label: m.agents_retrievalTools() },
        { name: 'prompt_template', label: m.agents_promptTemplates() },
      ]),
      tab: ref('api'),
      selected: ref([]),
      stepper: ref(0),
      api_servers,
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
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    actions() {
      return this.topic?.actions || []
    },
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
        this.updateVariantField('prompt_templates.classification', value.system_name)
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
          tool_provider: item.tool_provider,
        }
      })

      this.updateNestedListItemBySystemName({
        arrayPath: 'topics',
        itemSystemName: this.topic?.system_name,
        data: {
          actions: [...actions, ...this.actions],
        },
      })

      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: m.agents_actionAdded(),
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
