<script setup lang="ts">
/**
 * `<km-input-list-add>` — list of free-form text records that the user adds
 * one at a time. Each row is a `KmInput` with its own validation; an "Add"
 * button appends a new empty row, a delete button removes the row.
 *
 * Drop-in for the legacy InputListAdd: same `btnLabel`, `modelValue`,
 * `validateRecord` props and `update:modelValue` emit.
 */

import { computed, ref, watch } from 'vue'
import KmBtn from './KmBtn.vue'
import KmInput from './KmInput.vue'

const props = withDefaults(
  defineProps<{
    btnLabel?: string
    modelValue?: string[]
    /** Returns true when the record is acceptable. */
    validateRecord?: (value: string) => boolean
  }>(),
  {
    btnLabel: 'Add URL',
    modelValue: () => [],
    validateRecord: (value: string) => value.trim().length >= 3,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const errors = ref<boolean[]>(props.modelValue.map(() => false))

watch(
  () => props.modelValue,
  (next) => {
    if (errors.value.length !== next.length) {
      errors.value = next.map((_, i) => errors.value[i] ?? false)
    }
  },
)

const records = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const hasValidationError = computed(() => records.value.some((_, i) => errors.value[i]))

function validateField(index: number) {
  errors.value[index] = !props.validateRecord(records.value[index] ?? '')
}

function updateRecord(value: string, index: number) {
  const next = records.value.slice()
  next[index] = value
  records.value = next
  validateField(index)
}

function removeRecord(index: number) {
  const next = records.value.slice()
  next.splice(index, 1)
  errors.value.splice(index, 1)
  records.value = next
}

function addRecord() {
  const lastIdx = records.value.length - 1
  if (records.value.length === 0 || !errors.value[lastIdx]) {
    records.value = [...records.value, '']
    errors.value.push(false)
    return
  }
  errors.value[lastIdx] = true
}
</script>

<template>
  <div class="km-input-list-add stack" data-gap="sm" data-test="km-input-list-add">
    <div
      v-for="(_item, index) in records"
      :key="index"
      class="km-input-list-add__row cluster gap-sm"
      data-align="start"
      data-wrap="no"
    >
      <KmInput
        class="grow"
        :model-value="records[index]"
        label="Enter a record"
        :error-message="errors[index] ? 'Please enter a valid record' : ''"
        @update:model-value="(value) => updateRecord(String(value ?? ''), index)"
        @blur="validateField(index)"
      />
      <KmBtn
        flat
        icon="delete"
        icon-size="16px"
        @click.stop="removeRecord(index)"
      />
    </div>

    <div>
      <KmBtn
        flat
        icon="add"
        interaction-tone="brand"
        icon-size="14px"
        :label="btnLabel"
        :disable="hasValidationError"
        @click="addRecord"
      />
    </div>
  </div>
</template>
