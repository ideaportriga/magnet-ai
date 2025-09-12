<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Evaluation',
  confirmButtonLabel='Save & Run',
  cancelButtonLabel='Cancel',
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
        :rules='config.evaluated_tools.rules'
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
        :rules='config.evaluated_tools.rules'
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
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'

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
    // eslint-disable-next-line vue/prop-name-casing
    system_name: {
      type: String,
      default: '',
    },
    type: {
      type: String,
      default: '',
    },
  },
  emits: ['cancel', 'create'],
  setup() {
    const { items: setItems } = useChroma('evaluation_sets')
    const { create, get, requiredFields, config } = useChroma('evaluation_jobs')
    const { items: ragItems } = useChroma('rag_tools')
    const { items: promptTemplates } = useChroma('promptTemplates')

    return {
      setItems,
      ragItems,
      promptTemplates,
      get,
      create,
      config,
      requiredFields,
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
      return (this.$store?.getters['chroma/evaluation_sets']?.items || []).find((el) => el?.system_name == this.newRow?.evaluation_set)?.items?.length
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
      // POST /scheduler/create-job
      // Content-Type: application/json

      // {
      //     "name": "Custom Evaluation Job",
      //     "job_type": "one_time_immediate",
      //     "run_configuration": {
      //         "type": "evaluation",
      //         "params": {
      //             "type": "rag_eval",
      //             "iteration_count": 1,
      //             "config": [
      //                 {
      //                     "system_name": "MAGNET_AI_MANUAL",
      //                     "test_set_system_names": ["MANUAL_TEST_SET"],
      //                     "variants": ["variant_1"]
      //                 }
      //             ],
      //             "result_entity": "evaluations"
      //         }
      //     }
      // }
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

        const response = await this.$store.dispatch('createJob', JSON.stringify(payload))

        this.$emit('create', response)
        this.$emit('cancel')
      } catch (error) {
        console.error('Something goes wrong:', error)
      } finally {
        this.loading = false
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

.km-input:not(.q-field--readonly) .q-field__control::before {
  background: #fff !important;
}
</style>
