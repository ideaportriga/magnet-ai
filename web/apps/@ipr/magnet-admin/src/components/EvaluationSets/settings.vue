<template>
  <div>
    <km-section :title="m.common_type()" :sub-title="m.evaluationSets_typeDescription()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_type() }}</div>
      <km-select ref="typeRef" v-model="type" height="auto" min-height="36px" :placeholder="m.common_type()" :options="typeOptions" option-value="value" emit-value map-options />
    </km-section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { typeOptions } from '@/config/evaluation_sets/evaluation_sets'

const { draft, updateField } = useEntityDetail('evaluation_sets')

const type = computed({
  get() { return draft.value?.type || '' },
  set(value) { updateField('type', value) },
})
</script>
