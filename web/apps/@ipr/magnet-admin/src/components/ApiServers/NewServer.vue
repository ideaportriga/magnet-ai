<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New API Server',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to add security values and secrets later in API Server settings.',
  @confirm='createRecord',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
    .full-width
      km-input(data-test='name-input', height='30px', v-model='name', ref='nameRef', :rules='[required()]')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(data-test='system_name-input', height='30px', v-model='system_name', ref='system_nameRef', :rules='[required()]')
    .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md URL
    .full-width
      km-input(data-test='url-input', height='30px', v-model='newRow.url', ref='urlRef', :rules='[required()]')
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { cloneDeep } from 'lodash'
import { required, minLength } from '@shared/utils/validationRules'
import { toUpperCaseWithUnderscores } from '@shared'
import { useApiServerDetailStore, useAiAppDetailStore } from '@/stores/entityDetailStores'

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
    const apiServerStore = useApiServerDetailStore()
    const aiAppStore = useAiAppDetailStore()
    const { mutateAsync: createEntity } = queries.api_servers.useCreate()
    const { data: apiServersData } = queries.api_servers.useList()

    const items = computed(() => apiServersData.value?.items ?? [])

    return {
      createEntity,
      apiServerStore,
      aiAppStore,
      items,
      createNew: ref(false),
      newRow: reactive({
        name: '',
        system_name: '',
        url: '',
      }),
      required,
      requiredFields: ['name', 'system_name', 'url'],
      autoChangeSystemName: ref(true),
    }
  },
  computed: {
    name: {
      get() {
        return this.newRow?.name || ''
      },
      set(val) {
        this.newRow.name = val
        if (this.autoChangeSystemName && this.isMounted) this.newRow.system_name = toUpperCaseWithUnderscores(val)
      },
    },
    system_name: {
      get() {
        return this.newRow?.system_name || ''
      },
      set(val) {
        this.newRow.system_name = val
        this.autoChangeSystemName = false
      },
    },
    currentRaw() {
      return this.aiAppStore.entity
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
    validateFields() {
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
      return !validStates.includes(false)
    },
    async createRecord() {
      if (!this.validateFields()) return

      this.createNew = false
      const { id } = await this.createEntity(this.newRow)
      const server = this.items.find((item) => item.id === id)
      this.apiServerStore.setEntity(server)
      this.$router.push(`/api-servers/${id}`)
      this.$emit('cancel')
    },
  },
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
