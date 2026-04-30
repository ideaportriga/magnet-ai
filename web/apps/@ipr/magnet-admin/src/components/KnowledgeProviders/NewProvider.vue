<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newKnowledgeSourceProvider()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_addSecurityKsp()" @confirm="createKnowledgeProvider" @cancel="$emit(&quot;cancel&quot;)">
    <div class="stack" data-gap="lg">
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_name() }}</div>
        <div class="full-width">
          <km-input ref="nameRef" v-model="name" data-test="name-input" height="30px" :rules="[required()]" />
        </div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pl-sm">{{ m.common_systemName() }}</div>
        <div class="full-width">
          <km-input ref="system_nameRef" v-model="system_name" data-test="system-name-input" height="30px" :rules="[required()]" />
        </div>
        <div class="km-description text-secondary-text pb-xs pl-sm">{{ m.hint_systemNameUniqueId() }}</div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.label_sourceType() }}</div>
        <div class="full-width">
          <km-select ref="typeRef" v-model="newRow.type" data-test="select-type" height="auto" min-height="36px" :placeholder="m.modelProviders_selectSourceType()" :options="typeOptions" :rules="[required()]" emit-value map-options />
        </div>
      </div>
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.label_endpoint() }}</div>
        <div class="full-width">
          <km-input v-model="newRow.endpoint" data-test="endpoint-input" height="30px" :placeholder="m.placeholder_exampleApiEndpoint()" />
        </div>
        <div class="km-description text-secondary-text pb-xs pl-sm">{{ m.hint_endpointWarning() }}</div>
      </div>
    </div>
  </km-popup-confirm>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { required } from '@/utils/validationRules'
import { useEntityQueries } from '@/queries/entities'
import { useRouter } from 'vue-router'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { validateRef } from '@/utils/validateRef'

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
      const validStates = [validateRef(this.$refs.nameRef), validateRef(this.$refs.system_nameRef), validateRef(this.$refs.typeRef)]
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
