<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New AI App Tab',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to edit these and other settings after saving.',
  @confirm='create',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
    .full-width
      km-input(data-test="name-input" height='30px', placeholder='E.g. Help Center', v-model='name', ref='nameRef', :rules='config.name.rules')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(data-test="name-system_name" height='30px', placeholder='E.g. HELP_CENTER', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
    .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Tab type
    |
    .full-width.column
      template(v-for='tab in tabTypes')
        q-radio.q-mb-xs(name='tab_type', dense, :label='tab.label', :val='tab.val', v-model='newRow.tab_type')

  template(v-if='newRow.tab_type === "RAG"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 RAG Tool
      km-select(height='30px', placeholder='RAG Tool', :options='ragToolsOptions', v-model='ragToolCode', hasDropdownSearch, option-value='value')
  template(v-if='newRow.tab_type === "Retrieval"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Retrieval Tool
      km-select(
        height='30px',
        placeholder='Retrieval Tool',
        :options='retrievalToolsOptions',
        v-model='retrievalToolCode',
        hasDropdownSearch,
        option-value='value'
      ) 
  template(v-if='newRow.tab_type === "Custom"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Custom code
      km-codemirror(v-model='newRow.config.jsonString')
      .km-description.text-secondary-text.q-pb-4 Enter your custom code in JSON format
  template(v-if='newRow.tab_type === "Agent"')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Agent
      km-select(height='30px', placeholder='Agent', :options='agentsOptions', v-model='agentsCode', hasDropdownSearch, option-value='value')
</template>
<script>
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'
import { cloneDeep } from 'lodash'
import { toUpperCaseWithUnderscores } from '@shared'
import tabTypes from '@/config/ai_apps/tab_types'

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
    const { items, searchString, config, requiredFields, ...useCollection } = useChroma('rag_tools')
    const { items: agentItems } = useChroma('agents')
    const { items: retrievalItems } = useChroma('retrieval')
    return {
      items,
      retrievalItems,
      agentItems,
      searchString,
      config,
      useCollection,
      createNew: ref(false),
      requiredFields,
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
      return this.$store.getters.rag
    },
    ragToolsOptions() {
      return this.items.map((item) => ({
        label: item.name,
        value: item.system_name,
        modified_at: item?._metadata?.modified_at,
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
        modified_at: item?._metadata?.modified_at,
      }))
    },
    agentsOptions() {
      return this.agentItems.map((item) => ({
        label: item.name,
        value: item.system_name,
        modified_at: item?._metadata?.modified_at,
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
  },
  watch: {},
  mounted() {
    this.searchString = ''

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
      console.log(this.json)
    },
    validateFields() {
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
      return !validStates.includes(false)
    },

    async create() {
      if (!this.validateFields()) return
      this.createNew = false
      if (this.newRow.tab_type === 'Group') {
        this.newRow.children = []
      }
      await this.$store.commit('addAIAppTab', this.newRow)
      this.$emit('cancel')
    },
  },
}
</script>

<style lang="stylus">
.collection-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
.km-input:not(.q-field--readonly) .q-field__control::before
  background: #fff !important;
</style>
