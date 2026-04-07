<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.dialog_newAiAppTab()',
  :confirmButtonLabel='m.common_save()',
  :cancelButtonLabel='m.common_cancel()',
  :notification='m.hint_editAfterSaving()',
  @confirm='create',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_name() }}
    .full-width
      km-input(data-test='name-input', height='30px', :placeholder='m.placeholder_exampleHelpCenter()', v-model='name', ref='nameRef', :rules='config.name.rules')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_systemName() }}
    .full-width
      km-input(
        data-test='name-system_name',
        height='30px',
        :placeholder='m.placeholder_exampleSystemNameHelpCenter()',
        v-model='system_name',
        ref='system_nameRef',
        :rules='config.system_name.rules'
      )
    .km-description.text-secondary-text.q-pb-4 {{ m.hint_systemNameUniqueId() }}
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.label_tabType() }}
    |
    .full-width.column
      template(v-for='tab in tabTypes')
        q-radio.q-mb-xs(name='tab_type', dense, :label='tab.label', :val='tab.val', v-model='newRow.tab_type')

  template(v-if='newRow.tab_type === "RAG"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_ragTool() }}
      km-select(
        height='30px',
        :placeholder='m.entity_ragTool()',
        :options='ragToolsOptions',
        v-model='ragToolCode',
        hasDropdownSearch,
        option-value='value',
        ref='ragToolRef',
        :rules='ragToolRules'
      )
  template(v-if='newRow.tab_type === "Retrieval"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_retrievalTool() }}
      km-select(
        height='30px',
        :placeholder='m.entity_retrievalTool()',
        :options='retrievalToolsOptions',
        v-model='retrievalToolCode',
        hasDropdownSearch,
        option-value='value',
        ref='retrievalToolRef',
        :rules='retrievalToolRules'
      )
  template(v-if='newRow.tab_type === "Custom"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_customCode() }}
      km-codemirror(v-model='newRow.config.jsonString', :rules='customCodeRules', ref='customCodeRef')
      .km-description.text-secondary-text.q-pb-4 {{ m.hint_enterCustomCodeJson() }}
  template(v-if='newRow.tab_type === "Agent"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_agent() }}
      km-select(
        height='30px',
        :placeholder='m.entity_agent()',
        :options='agentsOptions',
        v-model='agentsCode',
        hasDropdownSearch,
        option-value='value',
        ref='agentsRef',
        :rules='agentsRules'
      )
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { cloneDeep } from 'lodash'
import { toUpperCaseWithUnderscores } from '@shared'
import tabTypes from '@/config/ai_apps/tab_types'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { useEntityDetail } from '@/composables/useEntityDetail'

export default {
  props: {
    copy: {
      type: Boolean,
      default: false,
    },
    showNewDialog: {
      default: false,
      type: Boolean,
    },
  },
  emits: ['cancel'],
  setup() {
    const { draft: ragDraft } = useVariantEntityDetail('rag_tools')
    const { draft, updateField } = useEntityDetail('ai_apps')

    const { options: items } = useCatalogOptions('rag_tools')
    const { options: agentItems } = useCatalogOptions('agents')
    const { options: retrievalItems } = useCatalogOptions('retrieval')

    const entityConfig = useEntityConfig('rag_tools')
    const config = computed(() => entityConfig.config || {})
    const requiredFields = computed(() => entityConfig.requiredFields || [])

    return {
      m,
      ragDraft,
      draft,
      updateField,
      items,
      retrievalItems,
      agentItems,
      config,
      requiredFields,
      createNew: ref(false),
      newRow: reactive({
        name: '',
        description: '',
        system_name: '',
        tab_type: 'RAG',
        config: {},
      }),
      autoChangeCode: ref(true),
      tabTypes,
    }
  },
  computed: {
    name: {
      get() {
        return this.newRow?.name || ''
      },
      set(val) {
        this.newRow.name = val
        if (this.autoChangeCode && this.isMounted) this.newRow.system_name = toUpperCaseWithUnderscores(val)
      },
    },
    system_name: {
      get() {
        return this.newRow?.system_name || ''
      },
      set(val) {
        this.newRow.system_name = val
        this.autoChangeCode = false
      },
    },
    currentRaw() {
      return this.ragDraft
    },
    ragToolsOptions() {
      return this.items.map((item) => ({
        label: item.name,
        value: item.system_name,
        modified_at: item?.updated_at,
      }))
    },
    ragToolCode: {
      get() {
        return this.items.find((el) => el.system_name == this.newRow.config.rag_tool)?.name
      },
      set(val) {
        this.newRow.config.rag_tool = val?.value
      },
    },
    retrievalToolsOptions() {
      return this.retrievalItems.map((item) => ({
        label: item.name,
        value: item.system_name,
        modified_at: item?.updated_at,
      }))
    },
    agentsOptions() {
      return this.agentItems.map((item) => ({
        label: item.name,
        value: item.system_name,
        modified_at: item?.updated_at,
      }))
    },
    agentsCode: {
      get() {
        return this.agentItems.find((el) => el.system_name == this.newRow.config.agent)?.name
      },
      set(val) {
        this.newRow.config.agent = val?.value
      },
    },
    retrievalToolCode: {
      get() {
        return this.retrievalItems.find((el) => el.system_name == this.newRow.config.retrieval_tool)?.name
      },
      set(val) {
        this.newRow.config.retrieval_tool = val?.value
      },
    },
    ragToolRules() {
      if (this.newRow.tab_type !== 'RAG') return []
      return [
        (value) => {
          const configValue = this.newRow.config.rag_tool
          return !!configValue || 'RAG Tool is required'
        },
      ]
    },
    retrievalToolRules() {
      if (this.newRow.tab_type !== 'Retrieval') return []
      return [
        (value) => {
          const configValue = this.newRow.config.retrieval_tool
          return !!configValue || 'Retrieval Tool is required'
        },
      ]
    },
    agentsRules() {
      if (this.newRow.tab_type !== 'Agent') return []
      return [
        (value) => {
          const configValue = this.newRow.config.agent
          return !!configValue || 'Agent is required'
        },
      ]
    },
    customCodeRules() {
      return [
        (value) => {
          return !!value || 'Custom code is required'
        },
      ]
    },
  },
  watch: {},
  mounted() {
    if (this.copy) {
      this.newRow = reactive(cloneDeep(this.currentRaw))
      this.newRow.name = this.newRow.name + '_COPY'
      this.newRow.description = this.newRow.description + '_COPY'
      this.newRow.system_name = this.newRow.system_name + '_COPY'
      delete this.newRow.id
    }

    this.isMounted = true
  },
  beforeUnmount() {
    this.isMounted = false
    this.$emit('cancel')
  },
  methods: {
    jsonTest() {
    },
    validateFields() {
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())

      // Validate tool/agent fields based on tab type
      if (this.newRow.tab_type === 'RAG') {
        const ragToolValid = this.$refs.ragToolRef?.validate()
        if (ragToolValid === false) return false
      } else if (this.newRow.tab_type === 'Retrieval') {
        const retrievalToolValid = this.$refs.retrievalToolRef?.validate()
        if (retrievalToolValid === false) return false
      } else if (this.newRow.tab_type === 'Agent') {
        const agentsValid = this.$refs.agentsRef?.validate()
        if (agentsValid === false) return false
      } else if (this.newRow.tab_type === 'Custom') {
        const customCodeValid = this.$refs.customCodeRef?.validate()
        if (customCodeValid === false) return false
      }

      return !validStates.includes(false)
    },

    async create() {
      if (!this.validateFields()) return
      this.createNew = false
      if (this.newRow.tab_type === 'Group') {
        this.newRow.children = []
      }
      const currentTabs = this.draft?.tabs || []
      const existing = currentTabs.find((el) => el.system_name === this.newRow.system_name)
      if (existing) {
        Object.assign(existing, this.newRow)
        this.updateField('tabs', [...currentTabs])
      } else {
        this.updateField('tabs', [...currentTabs, this.newRow])
      }
      this.$emit('cancel')
    },
  },
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
