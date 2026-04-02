<template lang="pug">
test-sets-table(
  v-model:selectedTestSet='sampleTestSet',
  :activeRowInput='testSetItem?.user_input',
  @selectRecord='onSelectRecord'
)
</template>

<script setup>
import { computed } from 'vue'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import TestSetsTable from '@/components/shared/TestSetsTable.vue'

const { activeVariant, updateVariantField, testSetItem } = useAgentEntityDetail()

const sampleTestSet = computed({
  get: () => activeVariant.value?.value?.sample_test_set || '',
  set: (value) => updateVariantField('sample_test_set', value),
})

const onSelectRecord = (event) => {
  testSetItem.value = event
}
</script>
