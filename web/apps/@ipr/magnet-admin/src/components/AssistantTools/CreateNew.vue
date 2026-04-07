<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.dialog_newAssistantToolApi()',
  :confirmButtonLabel='m.dialog_createAssistantTool()',
  :cancelButtonLabel='m.common_cancel()',
  @confirm='createTools',
  @cancel='$emit("cancel")',
  :loading='loading'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.label_apiProvider() }}
    .full-width
      km-select(
        height='30px',
        :placeholder='m.label_apiProvider()',
        :options='[{ value: "siebel_test", label: "API Provider Siebel Test" }]',
        hasDropdownSearch,
        option-value='value',
        option-label='label',
        map-options,
        v-model='newRow.api_provider'
      )

  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_apiSpecification() }}
    q-file(outlined, :label='m.common_uploadFile()', ref='fileRef', v-model='newRow.file', dense)
      template(v-slot:append)
        q-icon(name='attach_file')

    .km-description.text-secondary-text.q-py-8 {{ m.hint_uploadApiSpecification() }}
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
    const { draft } = useEntityDetail('assistant_tools')
    const appStore = useAppStore()

    const entityConfig = useEntityConfig('assistant_tools')
    const config = computed(() => entityConfig.config || {})
    const requiredFields = computed(() => entityConfig.requiredFields || [])

    return {
      m,
      createEntity,
      draft,
      appStore,
      config,
      requiredFields,
      createNew: ref(false),
      newRow: reactive({}),
      autoChangeCode: ref(true),
      loading: ref(false),
    }
  },
  computed: {
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
      const formData = new FormData()
      const payload = { ...this.newRow }

      if (payload.file) {
        formData.append('file', payload.file)
      }
      delete payload.file

      const response = await fetchData({
        method: 'POST',
        endpoint,
        credentials: 'include',
        service: 'assistant_tools/generate-from-openapi',
        body: formData,
        headers: {},
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

          await Promise.all(
            response.map(async (obj) => {
              await this.createEntity(obj)
            })
          )

          this.$q.notify({
            color: 'green-9', textColor: 'white',
            icon: 'check_circle',
            group: 'success',
            message: 'New assistant tool(s) have been added',
            timeout: 1000,
          })

          this.loading = false
          this.$emit('cancel')
        }
      } catch (error) {
        this.loading = false
        this.$q.notify({
          color: 'red-9', textColor: 'white',
          icon: 'error',
          group: 'error',
          message: error.message,
          timeout: 1000,
        })
      }
    },
  },
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
