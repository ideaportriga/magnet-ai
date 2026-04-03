<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.dialog_newAgent()',
  :confirmButtonLabel='m.common_save()',
  :cancelButtonLabel='m.common_cancel()',
  :notification='m.hint_agentNameDescription()',
  @confirm='createRow',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_name() }}
    .full-width
      km-input(height='30px', :placeholder='m.placeholder_exampleDemoAgent()', v-model='name', ref='nameRef', :rules='config.name.rules')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_systemName() }}
    .full-width
      km-input(height='30px', :placeholder='m.placeholder_exampleAgentDemo()', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
    .km-description.text-secondary-text.q-pb-4 {{ m.hint_systemNameUniqueId() }}
</template>

<script>
import { ref, reactive } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { cloneDeep } from 'lodash'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

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
    const { config, requiredFields } = useEntityConfig('agents')
    const queries = useEntityQueries()
    const { mutateAsync: createAgent } = queries.agents.useCreate()
    const { data: modelListData } = queries.model.useList()

    const { draft } = useAgentEntityDetail()
    return {
      m,
      draft,
      modelListData,
      requiredFields,
      config,
      createAgent,
      createNew: ref(false),
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
      return (this.modelListData?.items ?? []).find((el) => el.is_default)
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
      return this.draft
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
      const result = await this.createAgent(this.newRow)

      if (!result.id) {
        return
      }

      this.$router.push(`/agents/${result.id}`)
    },

    async openDetails(row) {
      await this.$router.push(`/agents/${row.id}`)
    },

  },
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
