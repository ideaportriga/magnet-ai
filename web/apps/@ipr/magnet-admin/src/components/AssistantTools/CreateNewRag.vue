<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Assistant Tool (RAG)',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  @confirm='createTools',
  @cancel='$emit("cancel")',
  :loading='loading'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 RAG tool
    km-select(
      height='auto',
      minHeight='30px',
      placeholder='Select RAG',
      :options='ragItems',
      v-model='rag',
      hasDropdownSearch,
      option-value='system_name',
      option-label='name',
      emit-value,
      map-options
    )
</template>
<script>
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'
import { cloneDeep } from 'lodash'

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
    const { items, searchString, create, config, requiredFields, ...useCollection } = useChroma('assistant_tools')
    const { items: ragItems } = useChroma('rag_tools')

    return {
      ragItems,
      items,
      searchString,
      config,
      useCollection,
      create,
      createNew: ref(false),
      requiredFields,
      newRow: reactive({
        rag_tool: '',
      }),
      autoChangeCode: ref(true),
      loading: ref(false),
    }
  },
  computed: {
    rag: {
      get() {
        return this.newRow?.rag_tool || ''
      },
      set(value) {
        this.newRow.rag_tool = value
      },
    },
    currentRaw() {
      return this.$store.getters.assistant_tool
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
    async getConfigs() {
      const response = await this.$store.dispatch('getAssistantConfigFromRAG', JSON.stringify(this.newRow))
      return response || []
    },
    validateFields() {
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
      return !validStates.includes(false)
    },
    async createTools() {
      try {
        if (this.validateFields()) {
          this.loading = true
          const response = await this.getConfigs()

          await this.create(JSON.stringify(response))

          this.loading = false

          this.$q.notify({
            position: 'top',
            message: 'New assistant tool(s) have been added',
            color: 'positive',
            textColor: 'black',
            timeout: 1000,
          })

          this.$emit('cancel')
        }
      } catch (error) {
        this.loading = false
        this.$q.notify({
          position: 'top',
          message: error.message,
          color: 'negative',
          textColor: 'black',
          timeout: 1000,
        })
      }
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
