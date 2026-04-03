<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.dialog_newEvaluation()',
  :confirmButtonLabel='m.common_saveAndRun()',
  :cancelButtonLabel='m.common_cancel()',
  @confirm='createEvaluationJob',
  @cancel='$emit("cancel")',
  :loading='loading'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Test Set
    .full-width
      km-select(
        height='auto',
        minHeight='36px',
        placeholder='Test Set',
        :options='filteredSetItems',
        v-model='newRow.evaluation_set',
        option-value='system_name',
        option-label='name',
        emit-value,
        map-options,
        ref='test_set_typeRef',
        :rules='config.test_set_type.rules',
        hasDropdownSearch
      )

  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md(v-if='evaluationSetType == "prompt_template"') Evaluated Prompt Templates
    |
    .full-width
      km-select(
        height='auto',
        minHeight='36px',
        placeholder='Select Prompt Template',
        :options='promptTemplates',
        v-model='evaluationTargetTools',
        hasDropdownSearch,
        option-value='system_name',
        option-label='name',
        emit-value,
        map-options,
        ref='evaluated_toolsRef',
        :rules='config.evaluated_tools.rules',
        :disabled='disablePromptSelection'
      )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md(v-if='evaluationSetType == "prompt_template"') Prompt Template variants
    .full-width
      km-select(
        height='auto',
        minHeight='36px',
        placeholder='Select Variants',
        multiple,
        use-chips,
        selectAll,
        :options='variants',
        v-model='newRow.evaluation_target_tools_variants',
        hasDropdownSearch,
        option-value='value',
        option-label='label',
        emit-value,
        map-options,
        ref='evaluated_toolsRef',
        :rules='config.evaluated_tools.rules'
      )

  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md(v-if='evaluationSetType == "rag_tool"') Evaluated RAGs
    |
    .full-width
      km-select(
        height='auto',
        minHeight='36px',
        placeholder='Select RAG',
        :options='ragItems',
        v-model='evaluationTargetTools',
        hasDropdownSearch,
        option-value='system_name',
        option-label='name',
        emit-value,
        map-options,
        ref='evaluated_toolsRef',
        :rules='config.evaluated_tools.rules',
        :disabled='disableRagSelection'
      )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md(v-if='evaluationSetType == "rag_tool"') Evaluated RAG Variants
    .full-width
      km-select(
        height='auto',
        minHeight='36px',
        placeholder='Select Variants',
        multiple,
        use-chips,
        selectAll,
        :options='ragVariants',
        v-model='newRow.evaluation_target_tools_variants',
        hasDropdownSearch,
        option-value='value',
        option-label='label',
        emit-value,
        map-options,
        ref='evaluated_toolsRef',
        :rules='config.evaluated_tools.rules'
      )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Number of iterations
    .full-width
      km-input(
        type='number',
        height='36px',
        placeholder='Number of iterations',
        v-model='newRow.iteration_count',
        ref='iteration_countRef',
        :rules='config.iteration_count.rules'
      )
    km-notification-text.q-mt-md(v-if='notification', :notification='notification')
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useEvaluationStore } from '@/stores/evaluationStore'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { m } from '@/paraglide/messages'

export default {
  props: {
    evaluationSetCode: {
      default: '',
      type: String,
    },
    showNewDialog: {
      default: false,
      type: Boolean,
    },
    system_name: {
      type: String,
      default: '',
    },
    type: {
      type: String,
      default: '',
    },
    disablePromptSelection: {
      type: Boolean,
      default: false,
    },
    disableRagSelection: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['cancel', 'create'],
  setup() {
    const queries = useEntityQueries()
    const evalStore = useEvaluationStore()
    const { data: setItemsData } = queries.evaluation_sets.useList()
    const { data: ragItemsData } = queries.rag_tools.useList()
    const { data: promptTemplatesData } = queries.promptTemplates.useList()

    const setItems = computed(() => setItemsData.value?.items ?? [])
    const ragItems = computed(() => ragItemsData.value?.items ?? [])
    const promptTemplates = computed(() => promptTemplatesData.value?.items ?? [])
    const evalSetsItems = computed(() => setItemsData.value?.items ?? [])

    const entityConfig = useEntityConfig('evaluation_jobs')
    const config = computed(() => entityConfig.config || {})
    const requiredFields = computed(() => entityConfig.requiredFields || [])

    return {
      m,
      evalStore,
      setItems,
      ragItems,
      promptTemplates,
      config,
      requiredFields,
      evalSetsItems,
      createNew: ref(false),
      loading: ref(false),
      newRow: reactive({
        evaluation_set: '',
        iteration_count: 1,
        evaluation_target_tools: [],
        evaluation_target_tools_variants: [],
      }),
    }
  },
  computed: {
    notification() {
      if (!this.testSetQty) return ''
      return `You are about to start an evaluation with ${this.testSetQty} test set records`
    },
    testSetQty() {
      return (this.evalSetsItems || []).find((el) => el?.system_name == this.newRow?.evaluation_set)?.items?.length
    },
    evaluationTargetTools: {
      get() {
        return this.newRow.evaluation_target_tools[0]
      },
      set(value) {
        this.newRow.evaluation_target_tools = [value]
      },
    },
    variants() {
      return this.promptTemplates
        .find((el) => el.system_name === this.evaluationTargetTools)
        ?.variants?.map((el) => ({ label: this.getVariantLabel(el.variant), value: el.variant }))
    },
    ragVariants() {
      return this.ragItems
        .find((el) => el.system_name === this.evaluationTargetTools)
        ?.variants?.map((el) => ({ label: this.getVariantLabel(el.variant), value: el.variant }))
    },
    filteredSetItems() {
      if (!this.type) return this.setItems
      return this.setItems.filter((item) => item.type === this.type)
    },
    evaluationSetType() {
      return this.setItems.find((item) => item.system_name === this.newRow.evaluation_set)?.type || this.type
    },
  },
  watch: {
    evaluationSetType(val, oldVal) {
      if (val !== oldVal) {
        this.newRow.evaluation_target_tools = []
      }
    },
    'newRow.evaluation_target_tools': {
      handler() {
        if (this.evaluationSetType === 'prompt_template') {
          this.newRow.evaluation_target_tools_variants = this.variants?.map((el) => el.value) || []
        }
        if (this.evaluationSetType === 'rag_tool') {
          this.newRow.evaluation_target_tools_variants = this.ragVariants?.map((el) => el.value) || []
        }
      },
    },
  },
  mounted() {
    if (this.system_name) {
      if (this.type === 'rag_tool') {
        this.newRow.evaluation_target_tools.push(this.system_name)
      }

      if (this.type === 'prompt_template') {
        this.evaluationTargetTools = this.system_name
      }
    }

    if (this.evaluationSetCode) {
      this.newRow.evaluation_set = this.evaluationSetCode
    }

    this.isMounted = true
  },
  beforeUnmount() {
    this.isMounted = false
    this.$emit('cancel')
  },
  methods: {
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
    validateFields() {
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
      return !validStates.includes(false)
    },
    async createEvaluationJob() {
      if (!this.validateFields()) return

      this.loading = true
      try {
        const job_type = this.evaluationSetType === 'prompt_template' ? 'prompt_eval' : 'rag_eval'

        const params = {
          type: job_type,
          config: [
            {
              system_name: this.newRow.evaluation_target_tools[0],
              variants: this.newRow.evaluation_target_tools_variants,
              test_set_system_names: [this.newRow.evaluation_set],
            },
          ],
          iteration_count: this.newRow.iteration_count,
          result_entity: 'evaluations',
        }

        const payload = {
          name: 'Custom Evaluation Job',
          job_type: 'one_time_immediate',
          run_configuration: {
            type: 'evaluation',
            params: {
              ...params,
            },
          },
        }

        const response = await this.evalStore.createJob(JSON.stringify(payload))

        this.$emit('create', response)
        this.$emit('cancel')
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: 'Failed to create evaluation job. Please try again.', timeout: 5000 })
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before {
  background: var(--q-white) !important;
}
</style>
