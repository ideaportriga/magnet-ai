<template lang="pug">
test-sets-table(
  v-model:selectedTestSet='sampleTestSet',
  :activeRowInput='retrievalStore.testSetItem?.user_input',
  @selectRecord='retrievalStore.testSetItem = $event'
)
</template>

<script setup>
import { computed } from 'vue'
import { useRetrievalDetailStore } from '@/stores/entityDetailStores'
import TestSetsTable from '@/components/shared/TestSetsTable.vue'

const retrievalStore = useRetrievalDetailStore()

const sampleTestSet = computed({
  get: () => retrievalStore.activeVariant?.sample_test_set || '',
  set: (value) => retrievalStore.updateNestedVariantProperty({ path: 'sample_test_set', value }),
})
</script>
