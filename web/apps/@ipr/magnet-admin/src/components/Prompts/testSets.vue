<template lang="pug">
test-sets-table(
  v-model:selectedTestSet='sampleTestSet',
  :activeRowInput='promptStore.testSetItem?.user_input',
  @selectRecord='promptStore.testSetItem = $event'
)
</template>

<script setup>
import { computed } from 'vue'
import { usePromptTemplateDetailStore } from '@/stores/entityDetailStores'
import TestSetsTable from '@/components/shared/TestSetsTable.vue'

const promptStore = usePromptTemplateDetailStore()

const sampleTestSet = computed({
  get: () => promptStore.activeVariant?.sample_test_set || '',
  set: (value) => promptStore.updateNestedVariantProperty({ path: 'sample_test_set', value }),
})
</script>
