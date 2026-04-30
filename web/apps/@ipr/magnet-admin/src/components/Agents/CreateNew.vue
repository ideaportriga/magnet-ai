<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newAgent()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_agentNameDescription()" @confirm="createRow" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_name() }}
      <div class="full-width">
        <km-input ref="nameRef" v-model="name" data-test="name-input" height="30px" :placeholder="m.placeholder_exampleDemoAgent()" :rules="config.name.rules" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_systemName() }}
      <div class="full-width">
        <km-input ref="system_nameRef" v-model="system_name" data-test="system-name-input" height="30px" :placeholder="m.placeholder_exampleAgentDemo()" :rules="config.system_name.rules" />
      </div>
      <div class="km-description text-secondary-text pb-xs">{{ m.hint_systemNameUniqueId() }}</div>
    </div>
  </km-popup-confirm>
</template>

<script>
import { ref, reactive } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { validateRef } from '@/utils/validateRef'
import { cloneDeep } from 'lodash'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { useSafeMutation } from '@/composables/useSafeMutation'

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
    const createAgent = useSafeMutation(queries.agents.useCreate())
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
        return (this.collections || []).filter((el) => (this.newRow?.variants[0].retrieve?.collection_system_names || []).includes(el?.id))
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
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
      return !validStates.includes(false)
    },
    async createRow() {
      if (!this.validateFields()) return

      this.createNew = false
      const { success, data } = await this.createAgent.run(this.newRow)
      if (!success || !data?.id) return

      this.$router.push(`/agents/${data.id}`)
    },

    async openDetails(row) {
      await this.$router.push(`/agents/${row.id}`)
    },

  },
}
</script>

