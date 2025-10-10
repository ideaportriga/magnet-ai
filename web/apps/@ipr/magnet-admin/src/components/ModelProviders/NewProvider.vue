<template lang="pug">
    km-popup-confirm(
      :visible='showNewDialog',
      title='New Model Provider',
      confirmButtonLabel='Save',
      cancelButtonLabel='Cancel',
      notification='You will be able to add security values and secrets later in Model Provider settings.',
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
            km-input(data-test='system-name-input', height='30px', v-model='system_name', ref='system_nameRef', :rules='[required()]')
          .km-description.text-secondary-text.q-pb-4.q-pl-8 System name serves as a unique record ID
    
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
          .full-width
            km-select(
              data-test='select-type',
              height='auto',
              minHeight='36px',
              placeholder='Select provider type',
              :options='typeOptions',
              v-model='newRow.type',
              ref='typeRef',
              :rules='[required()]',
              emit-value,
              mapOptions
            )
    
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Endpoint
          .full-width
            km-input(data-test='endpoint-input', height='30px', v-model='newRow.endpoint', placeholder='https://api.example.com')
          .km-description.text-secondary-text.q-pb-4.q-pl-8 Provider API endpoint URL. Warning: changing endpoint later will clear all secrets
    </template>
    
    <script>
    import { ref, reactive, computed } from 'vue'
    import { useChroma, required, toUpperCaseWithUnderscores } from '@shared'
    import { useRouter } from 'vue-router'
    
    export default {
      props: {
        showNewDialog: {
          type: Boolean,
          default: false,
        },
      },
      emits: ['cancel'],
      setup() {
        const { create, ...useCollection } = useChroma('provider')
        const router = useRouter()
    
        const typeOptions = [
          { label: 'OpenAI', value: 'openai' },
          { label: 'Azure OpenAI', value: 'azure_open_ai' },
          { label: 'Azure AI', value: 'azure_ai' },
          { label: 'Groq', value: 'groq' },
          { label: 'OCI', value: 'oci' },
          { label: 'OCI Llama', value: 'oci_llama' },
        ]
    
        return {
          create,
          useCollection,
          router,
          required,
          newRow: reactive({
            name: '',
            system_name: '',
            type: '',
            endpoint: '',
            connection_config: {},
            secrets_encrypted: {},
            metadata_info: {},
          }),
          autoChangeCode: ref(true),
          isMounted: ref(false),
          typeOptions,
        }
      },
      computed: {
        name: {
          get() {
            return this.newRow?.name || ''
          },
          set(val) {
            this.newRow.name = val
            if (this.autoChangeCode && this.isMounted) this.newRow.system_name = toUpperCaseWithUnderscores(val)
          },
        },
        system_name: {
          get() {
            return this.newRow?.system_name || ''
          },
          set(val) {
            this.newRow.system_name = val
            this.autoChangeCode = false
          },
        },
      },
      mounted() {
        this.isMounted = true
      },
      beforeUnmount() {
        this.isMounted = false
        this.$emit('cancel')
      },
      methods: {
        validateFields() {
          const validStates = [
            this.$refs.nameRef?.validate(),
            this.$refs.system_nameRef?.validate(),
            this.$refs.typeRef?.validate()
          ]
          return !validStates.includes(false)
        },
        async createModelProvider() {
          if (!this.validateFields()) return
    
          const result = await this.create(JSON.stringify(this.newRow))
    
          if (!result?.id) {
            return
          }
    
          await this.useCollection.selectRecord(result.id)
          this.$router.push(`/model-providers/${result.id}`)
        },
      },
    }
    </script>
    