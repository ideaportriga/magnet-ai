<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Knowledge Source Provider',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to add security values and secrets later in Knowledge Source Provider settings.',
  @confirm='createKnowledgeProvider',
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
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Source Type
      .full-width
        km-select(
          data-test='select-type',
          height='auto',
          minHeight='36px',
          placeholder='Select Source Type',
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useChroma, required, toUpperCaseWithUnderscores } from '@shared'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'

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
    const store = useStore()

    // Static fallback options
    const staticTypeOptions = [
      { label: 'Oracle Knowledge', value: 'oracle_knowledge' },
      { label: 'Sharepoint', value: 'sharepoint' },
      { label: 'Confluence', value: 'confluence' },
      { label: 'Salesforce', value: 'salesforce' },
      { label: 'Hubspot', value: 'hubspot' },
      { label: 'RightNow', value: 'rightnow' },
      { label: 'Fluid Topics', value: 'fluid_topics' },
    ]

    // Get plugins from store
    const plugins = computed(() => store.state.chroma?.plugins?.items || [])

    // Build type options from plugins in store
    const typeOptions = computed(() => {
      if (plugins.value.length > 0) {
        return plugins.value.map((plugin) => ({
          label: plugin.name,
          value: plugin.source_type,
        }))
      }
      return staticTypeOptions
    })

    return {
      create,
      useCollection,
      router,
      required,
      newRow: reactive({
        name: '',
        system_name: '',
        type: '',
        category: 'knowledge', // Set category for Knowledge Providers
        endpoint: '',
        connection_config: {},
        secrets_encrypted: {},
        metadata_info: {},
      }),
      autoChangeCode: ref(true),
      isMounted: ref(false),
      typeOptions,
      plugins,
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
      const validStates = [this.$refs.nameRef?.validate(), this.$refs.system_nameRef?.validate(), this.$refs.typeRef?.validate()]
      return !validStates.includes(false)
    },
    async createKnowledgeProvider() {
      if (!this.validateFields()) return

      const result = await this.create(JSON.stringify(this.newRow))

      if (!result?.id) {
        return
      }

      await this.useCollection.selectRecord(result.id)
      this.$router.push(`/knowledge-providers/${result.id}`)
    },
  },
}
</script>
