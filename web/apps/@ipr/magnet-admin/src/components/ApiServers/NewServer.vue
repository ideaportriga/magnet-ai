<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newApiServer()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_addSecurityApiServer()" @confirm="createRecord" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_name() }}
      <div class="full-width">
        <km-input ref="nameRef" v-model="name" data-test="name-input" height="30px" :rules="[required()]" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_systemName() }}
      <div class="full-width">
        <km-input ref="system_nameRef" v-model="system_name" data-test="system_name-input" height="30px" :rules="[required()]" />
      </div>
      <div class="km-description text-secondary-text pb-xs">{{ m.hint_systemNameUniqueId() }}</div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.label_url() }}
      <div class="full-width">
        <km-input ref="urlRef" v-model="newRow.url" data-test="url-input" height="30px" :rules="[required()]" />
      </div>
    </div>
  </km-popup-confirm>
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { cloneDeep } from 'lodash'
import { required, minLength } from '@/utils/validationRules'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { validateRef } from '@/utils/validateRef'

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
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
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

