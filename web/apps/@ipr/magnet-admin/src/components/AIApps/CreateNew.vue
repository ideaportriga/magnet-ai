<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newAiApp()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_editAfterSaving()" @confirm="createRecord" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_name() }}
      <div class="full-width">
        <km-input ref="nameRef" v-model="name" data-test="name-input" height="30px" :placeholder="m.placeholder_exampleServiceAiApp()" :rules="config.name.rules" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_systemName() }}
      <div class="full-width">
        <km-input ref="system_nameRef" v-model="system_name" data-test="system_name-input" height="30px" :placeholder="m.placeholder_exampleSystemNameAiApp()" :rules="config.system_name.rules" />
      </div>
      <div class="km-description text-secondary-text pb-xs">{{ m.hint_systemNameUniqueId() }}</div>
    </div>
  </km-popup-confirm>
</template>
<script>
import { ref, reactive } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { validateRef } from '@/utils/validateRef'
import { cloneDeep } from 'lodash'
import { useEntityQueries } from '@/queries/entities'
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
    const { config, requiredFields } = useEntityConfig('ai_apps')
    const queries = useEntityQueries()
    const { draft } = useEntityDetail('ai_apps')
    const { mutateAsync: createAiApp } = queries.ai_apps.useCreate()

    return {
      m,
      config,
      createAiApp,
      draft,
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
    validateFields() {
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
      return !validStates.includes(false)
    },
    async createRecord() {
      if (!this.validateFields()) return

      this.createNew = false
      const { id } = await this.createAiApp(this.newRow)
      this.$router.push(`/ai-apps/${id}`)
    },
  },
}
</script>

