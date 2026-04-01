<template lang="pug">
test-sets-table(
  v-model:selectedTestSet='sampleTestSet',
  :activeRowInput='ragStore.testSetItem?.user_input',
  @selectRecord='ragStore.testSetItem = $event'
)
</template>

<script setup>
import { computed } from 'vue'
import { useRagDetailStore } from '@/stores/entityDetailStores'
import TestSetsTable from '@/components/shared/TestSetsTable.vue'

const ragStore = useRagDetailStore()

const sampleTestSet = computed({
  get: () => ragStore.activeVariant?.sample_test_set || '',
  set: (value) => ragStore.updateNestedVariantProperty({ path: 'sample_test_set', value }),
})
</script>
