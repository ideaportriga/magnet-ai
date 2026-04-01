<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New AI App',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to edit these and other settings after saving.',
  @confirm='createRecord',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
    .full-width
      km-input(data-test='name-input', height='30px', placeholder='E.g. Service AI App', v-model='name', ref='nameRef', :rules='config.name.rules')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(
        data-test='system_name-input',
        height='30px',
        placeholder='E.g. SERVICE_AI_APP',
        v-model='system_name',
        ref='system_nameRef',
        :rules='config.system_name.rules'
      )
    .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
</template>
<script>
import { ref, reactive } from 'vue'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { cloneDeep } from 'lodash'
import { useEntityQueries } from '@/queries/entities'
import { useAiAppDetailStore } from '@/stores/entityDetailStores'

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
    const { config, requiredFields } = useEntityConfig('ai_apps')
    const queries = useEntityQueries()
    const aiAppStore = useAiAppDetailStore()
    const { mutateAsync: createAiApp } = queries.ai_apps.useCreate()

    return {
      config,
      createAiApp,
      aiAppStore,
      createNew: ref(false),
      requiredFields,
      newRow: reactive({
        name: '',
        description: '',
        system_name: '',
      }),
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
      const { id } = await this.createAiApp(this.newRow)
      this.aiAppStore.setEntity(this.newRow)
      this.$router.push(`/ai-apps/${id}`)
    },
  },
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
