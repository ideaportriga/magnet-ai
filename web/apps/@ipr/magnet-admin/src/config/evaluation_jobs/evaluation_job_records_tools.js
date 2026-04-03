import { required, minLength } from '@shared/utils/validationRules'
import TextWrap from './component/TextWrap.vue'
import { markRaw } from 'vue'
import { m } from '@/paraglide/messages'
export const evaluationRecord = {
  rowsPerPage: 5,
  sortBy: 'user_message',
  descending: false,
}

export const columnsSettings = {
  iteration: {
    name: 'iteration',
    label: m.evaluation_iteration(),
    field: 'iteration',
    display: true,
    readonly: true,
    ignorePatch: true,
    fromMetadata: false,
    sortable: true,
    align: 'left',
  },
  user_message: {
    name: 'user_message',
    code: 'user_message',
    display: true,
    label: m.evaluation_input(),
    field: 'user_message',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(1, 'Evaluation test set knowledge user_message must consist at least 1 source')],
    align: 'left',
    sortable: true,
    type: 'component',
    component: markRaw(TextWrap),
    headerStyle: 'min-width: 15vw',
  },
  generated_output: {
    name: 'generated_output',
    code: 'generated_output',
    display: true,
    label: m.evaluation_generatedOutput(),
    field: 'generated_output',
    readonly: true,
    columnNumber: 2,
    fromMetadata: false,
    ignorePatch: true,
    align: 'left',
    type: 'component',
    component: markRaw(TextWrap),
    headerStyle: 'min-width: 15vw',
  },
  expected_output: {
    name: 'expected_output',
    code: 'expected_output',
    display: true,
    label: m.evaluation_expectedOutput(),
    field: 'expected_output',
    readonly: true,
    columnNumber: 1,
    fromMetadata: false,
    ignorePatch: true,
    align: 'left',
    type: 'component',
    component: markRaw(TextWrap),
    headerStyle: 'min-width: 15vw',
  },
  score: {
    name: 'score',
    label: m.evaluation_score(),
    field: 'score',
    display: true,
    sortable: true,
    align: 'left',
  },
}

export const columnsCompareSettings = {
  iteration: {
    name: 'iteration',
    label: m.evaluation_iteration(),
    field: 'iteration',
    display: true,
    readonly: true,
    ignorePatch: true,
    fromMetadata: false,
    sortable: true,
    align: 'left',
  },
  variant: {
    name: 'variant',
    code: 'variant',
    display: true,
    label: m.common_variant(),
    field: (row) => {
      const variant = row.variant
      const match = variant?.match(/variant_(\d+)/)
      return `${m.common_variant()} ${match?.[1]}`
    },
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(1, 'Evaluation test set knowledge variant must consist at least 1 source')],
    align: 'left',
    sortable: true,
  },

  generated_output: {
    name: 'generated_output',
    code: 'generated_output',
    display: true,
    label: m.evaluation_generatedOutput(),
    field: 'generated_output',
    readonly: true,
    columnNumber: 2,
    fromMetadata: false,
    ignorePatch: true,
    align: 'left',
    type: 'component',
    component: markRaw(TextWrap),
    headerStyle: 'min-width: 15vw',
  },

  score: {
    name: 'score',
    label: m.evaluation_score(),
    field: 'score',
    display: true,
    sortable: true,
    align: 'left',
  },
}
