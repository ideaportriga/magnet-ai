<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newEvaluation()" :confirm-button-label="m.common_saveAndRun()" :cancel-button-label="m.common_cancel()" :loading="loading" @confirm="createEvaluationJob" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.entity_testSet() }}
      <div class="full-width">
        <km-select ref="test_set_typeRef" v-model="newRow.evaluation_set" height="auto" min-height="36px" :placeholder="m.entity_testSet()" :options="filteredSetItems" option-value="system_name" option-label="name" emit-value map-options :rules="config.test_set_type.rules" has-dropdown-search />
      </div>
    </div>
    <div v-if="evaluationSetType == &quot;prompt_template&quot;" class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.evaluation_evaluatedPromptTemplates() }}
      <div class="full-width">
        <km-select ref="evaluated_toolsRef" v-model="evaluationTargetTools" height="auto" min-height="36px" :placeholder="m.evaluation_selectPromptTemplate()" :options="promptTemplates" has-dropdown-search option-value="system_name" option-label="name" emit-value map-options :rules="config.evaluated_tools.rules" :disabled="disablePromptSelection" />
      </div>
    </div>
    <div v-if="evaluationSetType == &quot;prompt_template&quot;" class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.evaluation_promptTemplateVariants() }}
      <div class="full-width">
        <km-select ref="evaluated_toolsRef" v-model="newRow.evaluation_target_tools_variants" height="auto" min-height="36px" :placeholder="m.evaluation_selectVariants()" multiple use-chips select-all :options="variants" has-dropdown-search option-value="value" option-label="label" emit-value map-options :rules="config.evaluated_tools.rules" />
      </div>
    </div>
    <div v-if="evaluationSetType == &quot;rag_tool&quot;" class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.evaluation_evaluatedRags() }}
      <div class="full-width">
        <km-select ref="evaluated_toolsRef" v-model="evaluationTargetTools" height="auto" min-height="36px" :placeholder="m.evaluation_selectRagTool()" :options="ragItems" has-dropdown-search option-value="system_name" option-label="name" emit-value map-options :rules="config.evaluated_tools.rules" :disabled="disableRagSelection" />
      </div>
    </div>
    <div v-if="evaluationSetType == &quot;rag_tool&quot;" class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.evaluation_evaluatedRagVariants() }}
      <div class="full-width">
        <km-select ref="evaluated_toolsRef" v-model="newRow.evaluation_target_tools_variants" height="auto" min-height="36px" :placeholder="m.evaluation_selectVariants()" multiple use-chips select-all :options="ragVariants" has-dropdown-search option-value="value" option-label="label" emit-value map-options :rules="config.evaluated_tools.rules" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.evaluation_numberOfIterations() }}
      <div class="full-width">
        <km-input ref="iteration_countRef" v-model="newRow.iteration_count" type="number" height="36px" :placeholder="m.evaluation_numberOfIterations()" :rules="config.iteration_count.rules" />
      </div>
      <km-notification-text v-if="notification" class="mt-md" :notification="notification" />
    </div>
  </km-popup-confirm>
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useEvaluationStore } from '@/stores/evaluationStore'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { validateRef } from '@/utils/validateRef'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

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
      return m.evaluation_aboutToStart({ count: this.testSetQty })
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
      return `${m.common_variant()} ${match?.[1]}`
    },
    validateFields() {
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
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
          name: m.evaluation_customEvaluationJob(),
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
        notify.error(m.evaluation_failedToCreateJob())
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

