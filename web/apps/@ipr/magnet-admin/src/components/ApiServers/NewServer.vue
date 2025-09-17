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
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'
import { cloneDeep } from 'lodash'
import { required, minLength } from '@shared/utils/validationRules'
import { toUpperCaseWithUnderscores } from '@shared'

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
    const { create, items, ...useApiServers } = useChroma('api_servers')
    return {
      create,
      useApiServers,
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
      return this.$store.getters.ai_app
    },
  },
  watch: {},
  mounted() {
    this.searchString = ''

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
      console.log(this.newRow)
      const { inserted_id } = await this.create(JSON.stringify(this.newRow))
      await this.useApiServers.selectRecord(inserted_id)
      const server = this.items.find((item) => item.id === inserted_id)
      console.log('server', server)
      this.$store.commit('setApiServer', server)
      this.$router.push(`/api-servers/${inserted_id}`)
      this.$emit('cancel')
    },
  },
}
</script>

<style lang="stylus">
.collection-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
.km-input:not(.q-field--readonly) .q-field__control::before
  background: #fff !important;
</style>
