<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.dialog_newApiServer()',
  :confirmButtonLabel='m.common_save()',
  :cancelButtonLabel='m.common_cancel()',
  :notification='m.hint_addSecurityApiServer()',
  @confirm='createRecord',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_name() }}
    .full-width
      km-input(data-test='name-input', height='30px', v-model='name', ref='nameRef', :rules='[required()]')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_systemName() }}
    .full-width
      km-input(data-test='system_name-input', height='30px', v-model='system_name', ref='system_nameRef', :rules='[required()]')
    .km-description.text-secondary-text.q-pb-4 {{ m.hint_systemNameUniqueId() }}
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.label_url() }}
    .full-width
      km-input(data-test='url-input', height='30px', v-model='newRow.url', ref='urlRef', :rules='[required()]')
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { cloneDeep } from 'lodash'
import { required, minLength } from '@shared/utils/validationRules'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'

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
    const { draft: aiAppDraft } = useEntityDetail('ai_apps')
    const { mutateAsync: createEntity } = queries.api_servers.useCreate()

    return {
      m,
      createEntity,
      aiAppDraft,
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
      return this.aiAppDraft
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
