<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newTestSet()" :confirm-button-label="m.common_addAndNew()" :cancel-button-label="m.common_cancel()" :confirm-button-label2="m.common_add()" @confirm="addRecord(true)" @confirm2="addRecord" @cancel="$emit(&quot;cancel&quot;)">
    <div v-if="selectedEvaluationSet?.type === &quot;rag_tool&quot;" class="pb-xs pl-sm mb-md">
      <retrieval-metadata-filter v-model="newRow.metadata_filter" :label="m.evaluationJobs_metadataFilter()" label-class="km-field text-secondary-text mr-xs" />
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.evaluation_input() }}
      <div class="full-width">
        <km-input ref="user_inputRef" rows="10" :placeholder="m.placeholder_typeYourTextHere()" :model-value="newRow.user_input" border-radius="8px" height="36px" type="textarea" :rules="columnsSettings.user_input.rules" @input="newRow.user_input = $event" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.evaluation_expectedOutput() }}
      <div class="full-width">
        <km-input ref="expected_resultRef" rows="10" :placeholder="m.placeholder_typeYourTextHere()" :model-value="newRow.expected_result" border-radius="8px" height="36px" type="textarea" @input="newRow.expected_result = $event" />
      </div>
    </div>
  </km-popup-confirm>
</template>
<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { columnsSettings } from '@/config/evaluation_sets/evaluation_set_records'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { validateRef } from '@/utils/validateRef'

export default {
  props: {
    showNewDialog: Boolean,
  },
  emits: ['cancel', 'addRecord'],
  setup() {
    const { draft } = useEntityDetail('evaluation_sets')
    const selectedEvaluationSet = computed(() => draft.value)
    return {
      m,
      createNew: ref(false),
      newRow: ref({
        metadata_filter: [],
        user_input: '',
        expected_result: '',
        id: crypto.randomUUID(),
      }),
      autoChangeCode: ref(true),
      columnsSettings,
      selectedEvaluationSet,
    }
  },
  computed: {},
  watch: {},
  mounted() {
    this.isMounted = true
  },
  beforeUnmount() {
    this.isMounted = false
    this.$emit('cancel')
  },
  methods: {
    validateFields() {
      const validStates = Object.keys(this.columnsSettings).map((field) => validateRef(this.$refs[`${field}Ref`]))
      return !validStates.includes(false)
    },
    addRecord(addNew = false) {
      if (!this.validateFields()) return
      this.$emit('addRecord', this.newRow)
      if (addNew) {
        this.newRow = {
          filter_object: null,
          user_input: '',
          expected_result: '',
        }
      } else {
        this.$emit('cancel')
      }
    },
  },
}
</script>

