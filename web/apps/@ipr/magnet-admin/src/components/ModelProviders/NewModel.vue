<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Model',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to configure Model features and pricing on the details screen',
  @confirm='createModel',
  @cancel='$emit("cancel")'
)
  .column.q-gap-16
      
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
      .full-width
        km-input(data-test='name-input', height='30px', v-model='name', ref='nameRef', :rules='[required()]')
      .km-description.text-secondary-text.q-pb-4.q-pl-8 Name used by provider to identify the model

    .col
      .km-field.text-secondary-text.q-pl-8 Display name
      .full-width
        km-input(data-test='name-input', height='30px', v-model='display_name', ref='display_nameRef', :rules='[required()]')
      .km-description.text-secondary-text.q-pb-4.q-pl-8 Internal name used across Magnet AI 

    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Category
      .full-width
        km-select(v-model='category', :options='categoryOptions')
</template>

<script setup>
import { ref } from 'vue'
import { required } from '@shared'

const props = defineProps({
  showNewDialog: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits(['cancel'])

const stepper = ref(0)

const name = ref('')
const display_name = ref('')
const category = ref('')
const categoryOptions = ref([
  { label: 'Chat Completion', value: 'chat_completion' },
  { label: 'Vector Embedding', value: 'vector_embedding' },
  { label: 'Re-ranking', value: 're_ranking' },
])

const createModel = () => {
  console.log('createModel')
}
</script>

<style scoped>

</style>