<template lang="pug">
test-sets-table(
  v-model:selectedTestSet='sampleTestSet',
  :activeRowInput='agentStore.testSetItem?.user_input',
  @selectRecord='agentStore.testSetItem = $event'
)
</template>

<script setup>
import { computed } from 'vue'
import { useAgentDetailStore } from '@/stores/agentDetailStore'
import TestSetsTable from '@/components/shared/TestSetsTable.vue'

const agentStore = useAgentDetailStore()

const sampleTestSet = computed({
  get: () => agentStore.activeVariant?.value?.sample_test_set || '',
  set: (value) => agentStore.updateNestedVariantProperty({ path: 'sample_test_set', value }),
})
</script>
