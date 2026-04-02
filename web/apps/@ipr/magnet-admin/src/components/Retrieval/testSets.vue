<template lang="pug">
test-sets-table(
  v-model:selectedTestSet='sampleTestSet',
  :activeRowInput='testSetItem?.user_input',
  @selectRecord='testSetItem = $event'
)
</template>

<script setup>
import { computed } from 'vue'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import TestSetsTable from '@/components/shared/TestSetsTable.vue'

const { activeVariant, updateVariantField, testSetItem } = useVariantEntityDetail('retrieval')

const sampleTestSet = computed({
  get: () => activeVariant.value?.sample_test_set || '',
  set: (value) => updateVariantField('sample_test_set', value),
})
</script>
