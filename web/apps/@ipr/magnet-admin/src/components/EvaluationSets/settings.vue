<template lang="pug">
div
  km-section(:title='m.common_type()', :subTitle='m.evaluationSets_typeDescription()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_type() }}
    km-select(
      height='auto',
      minHeight='36px',
      :placeholder='m.common_type()',
      :options='typeOptions',
      v-model='type',
      ref='typeRef',
      option-value='value',
      emit-value,
      map-options
    )
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
