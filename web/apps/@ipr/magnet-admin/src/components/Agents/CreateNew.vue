<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Agent',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='Please give your Agent a name and description. You will be navigated to Agent configuration screen at the next step.',
  @confirm='createRow',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
    .full-width
      km-input(height='30px', placeholder='E.g. Demo Agent', v-model='name', ref='nameRef', :rules='config.name.rules')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(height='30px', placeholder='E.g. AGENT_DEMO', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
    .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
</template>

<script>
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'
import { cloneDeep } from 'lodash'
import { toUpperCaseWithUnderscores } from '@shared'

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
    const { searchString, create, requiredFields, config, ...useCollection } = useChroma('agents')

    return {
      searchString,
      useCollection,
      requiredFields,
      config,
      create,
      createNew: ref(false),
      loadingRefresh: ref(false),
      newRow: reactive({
        name: '',
        description: '',
        system_name: '',
        active_variant: 'variant_1',
        variants: [
          {
            description: '',
            variant: 'variant_1',
            value: {
              prompt_templates: {
                classification: 'DEFAULT_AGENT_CLASSIFICATION',
                topic_processing: 'DEFAULT_AGENT_TOPIC_PROCESSING',
              },
              settings: { conversation_closure_interval: '1D' },
              topics: [],
            },
          },
        ],
      }),
      autoChangeCode: ref(true),
      isMounted: ref(false),
    }
  },
  computed: {
    defaultModel() {
      return this.$store.getters['chroma/model']?.items?.find((el) => el.is_default)
    },
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
      return this.$store.getters.agent_detail
    },
    collectionSystemNames: {
      get() {
        return this.collections.filter((el) => (this.newRow?.variants[0].retrieve?.collection_system_names || []).includes(el?.id))
      },
      set(value) {
        value = (value || []).map((el) => {
          if (typeof el === 'string') {
            return el
          } else {
            return el?.id
          }
        })
        this.newRow.variants[0].retrieve.collection_system_names = value
      },
    },
  },
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
    validateFields() {
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
      return !validStates.includes(false)
    },
    async createRow() {
      if (!this.validateFields()) return

      this.createNew = false
      const result = await this.create(JSON.stringify(this.newRow))

      if (!result.id) {
        return
      }

      await this.useCollection.selectRecord(result.id)
      await this.$store.commit('setAgentDetail', this.newRow)
      this.$router.push(`/agents/${result.id}`)
    },

    async openDetails(row) {
      await this.$router.push(`/agents/${row.id}`)
    },

    async refreshTable() {
      this.loadingRefresh = true
      this.useCollection.get()
      this.loadingRefresh = false
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
