<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.dialog_newKnowledgeSourceProvider()',
  :confirmButtonLabel='m.common_save()',
  :cancelButtonLabel='m.common_cancel()',
  :notification='m.hint_addSecurityKsp()',
  @confirm='createKnowledgeProvider',
  @cancel='$emit("cancel")'
)
  .column.q-gap-16
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_name() }}
      .full-width
        km-input(data-test='name-input', height='30px', v-model='name', ref='nameRef', :rules='[required()]')

    .col
      .km-field.text-secondary-text.q-pl-8 {{ m.common_systemName() }}
      .full-width
        km-input(data-test='system-name-input', height='30px', v-model='system_name', ref='system_nameRef', :rules='[required()]')
      .km-description.text-secondary-text.q-pb-4.q-pl-8 {{ m.hint_systemNameUniqueId() }}

    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_sourceType() }}
      .full-width
        km-select(
          data-test='select-type',
          height='auto',
          minHeight='36px',
          :placeholder='m.modelProviders_selectSourceType()',
          :options='typeOptions',
          v-model='newRow.type',
          ref='typeRef',
          :rules='[required()]',
          emit-value,
          mapOptions
        )

    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_endpoint() }}
      .full-width
        km-input(data-test='endpoint-input', height='30px', v-model='newRow.endpoint', :placeholder='m.placeholder_exampleApiEndpoint()')
      .km-description.text-secondary-text.q-pb-4.q-pl-8 {{ m.hint_endpointWarning() }}
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { useEntityQueries } from '@/queries/entities'
import { useRouter } from 'vue-router'
import { useSafeMutation } from '@/composables/useSafeMutation'

export default {
  props: {
    showNewDialog: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['cancel'],
  setup() {
    const queries = useEntityQueries()
    const createEntity = useSafeMutation(queries.provider.useCreate())
    const { data: pluginsData } = queries.plugins.useList()
    const router = useRouter()

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

    // Get plugins from TanStack Query
    const plugins = computed(() => pluginsData.value?.items ?? [])

    // Build type options from plugins
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
      m,
      createEntity,
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

      const { success, data } = await this.createEntity.run(this.newRow)
      if (!success || !data?.id) return

      this.$router.push(`/knowledge-providers/${data.id}`)
    },
  },
}
</script>
