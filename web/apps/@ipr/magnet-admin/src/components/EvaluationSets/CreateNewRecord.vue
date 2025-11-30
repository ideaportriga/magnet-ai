<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Test Set',
  confirmButtonLabel='Add & New',
  cancelButtonLabel='Cancel',
  confirmButtonLabel2='Add',
  @confirm='addRecord(true)',
  @confirm2='addRecord',
  @cancel='$emit("cancel")'
)
  .q-pb-xs.q-pl-8.q-mb-md(v-if='selectedEvaluationSet?.type === "rag_tool"')
    retrieval-metadata-filter(
      v-model='newRow.metadata_filter',
      label='Evaluation metadata filter',
      labelClass='km-field text-secondary-text q-mr-xs'
    )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Evaluation input
    .full-width
      km-input(
        ref='user_inputRef',
        rows='10',
        placeholder='Type your text here',
        :model-value='newRow.user_input',
        @input='newRow.user_input = $event',
        border-radius='8px',
        height='36px',
        type='textarea',
        :rules='columnsSettings.user_input.rules'
      )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Expected output
    .full-width
      km-input(
        ref='expected_resultRef',
        rows='10',
        placeholder='Type your text here',
        :model-value='newRow.expected_result',
        @input='newRow.expected_result = $event',
        border-radius='8px',
        height='36px',
        type='textarea'
      )
</template>
<script>
import { ref } from 'vue'
import { columnsSettings } from '@/config/evaluation_sets/evaluation_set_records'
import { uid } from 'quasar'
import { useChroma } from '@shared'

export default {
  props: {
    showNewDialog: Boolean,
  },
  emits: ['cancel', 'addRecord'],
  setup() {
    const { selectedRow: selectedEvaluationSet } = useChroma('evaluation_sets')
    return {
      createNew: ref(false),
      newRow: ref({
        metadata_filter: [],
        user_input: '',
        expected_result: '',
        id: uid(),
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
      const validStates = Object.keys(this.columnsSettings).map((field) => this.$refs[`${field}Ref`]?.validate())
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

<style lang="stylus">
.collection-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
.km-input:not(.q-field--readonly) .q-field__control::before
  background: #fff !important;
</style>
