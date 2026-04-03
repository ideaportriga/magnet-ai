<template lang="pug">
div
  km-section(title='Type', subTitle='Type of objects that the Test Set will be used for')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
    km-select(
      height='auto',
      minHeight='36px',
      placeholder='Type',
      :options='[ { value: "rag_tool", label: "RAG" }, { value: "prompt_template", label: "Prompt Template" }, ]',
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

const { draft, updateField } = useEntityDetail('evaluation_sets')

const type = computed({
  get() { return draft.value?.type || '' },
  set(value) { updateField('type', value) },
})
</script>
