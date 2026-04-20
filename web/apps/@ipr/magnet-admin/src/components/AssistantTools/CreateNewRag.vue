<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.assistantTools_newAssistantToolRag()',
  :confirmButtonLabel='m.common_save()',
  :cancelButtonLabel='m.common_cancel()',
  @confirm='createTools',
  @cancel='$emit("cancel")',
  :loading='loading'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 RAG tool
    km-select(
      height='auto',
      minHeight='30px',
      :placeholder='m.assistantTools_selectRag()',
      :options='ragItems',
      v-model='rag',
      hasDropdownSearch,
      option-value='system_name',
      option-label='name',
      emit-value,
      map-options
    )
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { cloneDeep } from 'lodash'
import { fetchData } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { notify } from '@shared/utils/notify'

export default {
  props: {
    copy: {
      type: Boolean,
      default: false,
    },
    showNewDialog: {
      default: false,
      type: Boolean,
    },
  },
  emits: ['cancel'],
  setup() {
    const queries = useEntityQueries()
    const { mutateAsync: createEntity } = queries.assistant_tools.useCreate()
    const { options: ragItems } = useCatalogOptions('rag_tools')
    const { draft } = useEntityDetail('assistant_tools')
    const appStore = useAppStore()

    const entityConfig = useEntityConfig('assistant_tools')
    const config = computed(() => entityConfig.config || {})
    const requiredFields = computed(() => entityConfig.requiredFields || [])

    return {
      ragItems,
      createEntity,
      draft,
      appStore,
      config,
      requiredFields,
      createNew: ref(false),
      newRow: reactive({
        rag_tool: '',
      }),
      autoChangeCode: ref(true),
      loading: ref(false),
      m,
    }
  },
  computed: {
    rag: {
      get() {
        return this.newRow?.rag_tool || ''
      },
      set(value) {
        this.newRow.rag_tool = value
      },
    },
    currentRaw() {
      return this.draft
    },
  },
  watch: {},
  mounted() {
    if (this.copy) {
      this.newRow = reactive(cloneDeep(this.currentRaw))
      this.newRow.name = this.newRow.name + '_COPY'
      this.newRow.description = this.newRow.description + '_COPY'
      this.newRow.system_name = this.newRow.system_name + '_COPY'
      delete this.newRow.id
    }

    this.isMounted = true
  },
  beforeUnmount() {
    this.isMounted = false
    this.$emit('cancel')
  },
  methods: {
    async getConfigs() {
      const endpoint = this.appStore.config?.search?.endpoint
      const response = await fetchData({
        method: 'POST',
        endpoint,
        credentials: 'include',
        service: 'assistant_tools/generate-from-rag-tool',
        body: JSON.stringify(this.newRow),
        headers: { 'Content-Type': 'application/json' },
      })
      if (response.ok) return await response.json()
      if (response.error) throw response
      return []
    },
    validateFields() {
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
      return !validStates.includes(false)
    },
    async createTools() {
      try {
        if (this.validateFields()) {
          this.loading = true
          const response = await this.getConfigs()

          await this.createEntity(response)

          this.loading = false

          notify.success('New assistant tool(s) have been added')

          this.$emit('cancel')
        }
      } catch (error) {
        this.loading = false
        notify.error(error.message)
      }
    },
  },
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
