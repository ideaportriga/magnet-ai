<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Assistant Tool (API)',
  confirmButtonLabel='Create Assistant Tool',
  cancelButtonLabel='Cancel',
  @confirm='createTools',
  @cancel='$emit("cancel")',
  :loading='loading'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md API Provider
    .full-width
      km-select(
        height='30px',
        placeholder='API Provider',
        :options='[{ value: "siebel_test", label: "API Provider Siebel Test" }]',
        hasDropdownSearch,
        option-value='value',
        option-label='label',
        map-options,
        v-model='newRow.api_provider'
      )

  .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Specification
    q-file(outlined, label='File upload', ref='fileRef', v-model='newRow.file', dense)
      template(v-slot:append)
        q-icon(name='attach_file')

    .km-description.text-secondary-text.q-py-8 Upload API Specification to generate Assistant Tool. File format: JSON or YAML
</template>
<script>
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'
import { cloneDeep } from 'lodash'

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
    const { items, searchString, create, config, requiredFields, ...useCollection } = useChroma('assistant_tools')
    const { publicItems } = useChroma('collections')

    return {
      items,
      searchString,
      config,
      useCollection,
      create,
      createNew: ref(false),
      collections: publicItems,
      requiredFields,
      newRow: reactive({}),
      autoChangeCode: ref(true),
      loading: ref(false),
    }
  },
  computed: {
    currentRaw() {
      return this.$store.getters.assistant_tool
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
    async getConfigs() {
      const response = await this.$store.dispatch('getAssistantConfigFromFile', this.newRow)
      return response || []
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
              console.log(obj)
              await this.create(JSON.stringify(obj))
            })
          )

          this.$q.notify({
            position: 'top',
            message: 'New assistant tool(s) have been added',
            color: 'positive',
            textColor: 'black',
            timeout: 1000,
          })

          this.loading = false
          this.$emit('cancel')
        }
      } catch (error) {
        this.loading = false
        this.$q.notify({
          position: 'top',
          message: error.message,
          color: 'negative',
          textColor: 'black',
          timeout: 1000,
        })
      }
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
