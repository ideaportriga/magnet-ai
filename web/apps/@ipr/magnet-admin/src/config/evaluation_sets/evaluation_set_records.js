import { required, minLength } from '@shared/utils/validationRules'
import TextWrap from './component/TextWrap.vue'
import { markRaw } from 'vue'

export const evaluationRecord = {
  rowsPerPage: 5,
  descending: false,
}

export const columnsSettings = {
  user_input: {
    name: 'user_input',
    code: 'user_input',
    display: true,
    label: 'Evaluation Input',
    field: 'user_input',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(1, 'Evaluation test set knowledge user_input must consist at least 1 source')],
    align: 'left',
    type: 'component',
    component: markRaw(TextWrap),
    headerStyle: 'min-width: 15vw',
  },
  expected_result: {
    name: 'expected_result',
    code: 'expected_result',
    display: true,
    label: 'Expected output',
    field: 'expected_result',
    readonly: true,
    columnNumber: 1,
    fromMetadata: false,
    ignorePatch: true,
    align: 'left',
    type: 'component',
    component: markRaw(TextWrap),
    headerStyle: 'min-width: 15vw',
  },
}
