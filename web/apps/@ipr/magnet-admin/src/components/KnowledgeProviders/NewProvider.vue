<template lang="pug">
    km-popup-confirm(
      :visible='showNewDialog',
      title='New Knowledge Source Provider',
      confirmButtonLabel='Save',
      cancelButtonLabel='Cancel',
      notification='You will be able to add security values and secrets later in Knowledge Source Provider settings.',
      @confirm='createModelProvider',
      @cancel='$emit("cancel")'
    )
      .column.q-gap-16   
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
          .full-width
            km-input(data-test='name-input', height='30px', v-model='name', ref='nameRef', :rules='[required()]')
    
        .col
          .km-field.text-secondary-text.q-pl-8 System name
          .full-width
            km-input(data-test='name-input', height='30px', v-model='system_name', ref='systemRef', :rules='[required()]')
          .km-description.text-secondary-text.q-pb-4.q-pl-8 System name serves as a unique record ID
    
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
          .full-width
            km-select(v-model='type', :options='[]')
    </template>
    
    <script setup>
    import { ref, watch } from 'vue'
    import { required } from '@shared'
    import { useChroma } from '@shared'
    import { useRouter } from 'vue-router'
    const props = defineProps({
      showNewDialog: {
        type: Boolean,
        required: true,
      },
    })
    
    const { create } = useChroma('mcp_servers')
    const router = useRouter()
    const name = ref('')
    const system_name = ref('')
    const url = ref('')
    const transport = ref('streamable-http')
    
    const emit = defineEmits(['cancel'])
    
    const nameRef = ref(null)
    const systemRef = ref(null)
    const urlRef = ref(null)
    
    
    watch(name, (newVal) => {
      if (newVal && !system_name.value) {
        system_name.value = newVal.toUpperCase().replace(/ /g, '_')
      }
    })
    
    const validateFields = () => {
      const validStates = [nameRef.value.validate(), systemRef.value.validate(), urlRef.value.validate()]
      return !validStates.includes(false)
    }

    const createModelProvider = async () => {
      emit('cancel')
    }
    </script>
    