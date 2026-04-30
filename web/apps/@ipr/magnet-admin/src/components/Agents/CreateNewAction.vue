<template>
  <km-dialog :model-value="showNewDialog" @cancel="$emit(&quot;cancel&quot;)">
    <km-card class="card-style" style="min-inline-size: 800px">
      <div class="km-card-section card-section-style">
        <div class="cluster">
          <div class="flex-1">
            <div class="km-heading-7">{{ m.agents_newAction() }}</div>
          </div>
          <div class="flex-none">
            <km-btn icon="close" flat dense @click="$emit(&quot;cancel&quot;)" />
          </div>
        </div>
      </div>
      <div class="km-card-section card-section-style mb-md">
        <agents-tool-selection v-model:selected="selected" />
        <div class="cluster mt-lg">
          <div class="flex-none">
            <km-btn flat :label="m.common_cancel()" tone="brand" @click="$emit(&quot;cancel&quot;)" />
          </div>
          <div class="flex-1" />
          <div class="flex-none">
            <km-btn :label="m.common_add()" @click="create" />
          </div>
        </div>
      </div>
    </km-card>
  </km-dialog>
</template>
<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { agentTopicActionsPopupColumns, agentTopicActionsAPIToolsPopupColumns } from '@/config/agents/topics'
import { notify } from '@shared/utils/notify'

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

      notify.success(m.agents_actionAdded())

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
