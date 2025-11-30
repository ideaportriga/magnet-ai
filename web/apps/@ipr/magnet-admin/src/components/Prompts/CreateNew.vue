<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Prompt Template',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to edit these and other settings after saving.',
  @confirm='createRow',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
    .full-width
      km-input(
        data-test='name-input',
        height='30px',
        placeholder='E.g. Demo Prompt Template',
        v-model='name',
        ref='nameRef',
        :rules='config.name.rules'
      )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(
        height='30px',
        placeholder='E.g. PROMPT_TEMPLATE_DEMO',
        v-model='system_name',
        ref='system_nameRef',
        :rules='config.system_name.rules'
      )
    .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Categories
    |
    km-select(
      data-test='select-category',
      height='auto',
      minHeight='36px',
      placeholder='Categories',
      :options='categoryOptions',
      v-model='newRow.category',
      ref='categoryRef',
      :rules='config.category.rules',
      emit-value,
      mapOptions
    )
</template>

<script>
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'
import { cloneDeep } from 'lodash' // Import lodash for deep cloning
import { toUpperCaseWithUnderscores } from '@shared'
import { categoryOptions } from '@/config/prompts/prompts'

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
    const { searchString, create, requiredFields, config, ...useCollection } = useChroma('promptTemplates')

    return {
      searchString,
      useCollection,
      requiredFields,
      config,
      create,
      createNew: ref(false),
      loadingRefresh: ref(false),
      newRow: reactive({
        name: '',
        description: '',
        system_name: '',
        caregory: 'generic',
        active_variant: 'variant_1',
        variants: [
          {
            variant: 'variant_1',
            topP: 1,
            temperature: 1,
            system_name_for_model: null,
            retrieve: {
              collection_system_names: [],
            },
          },
        ],
      }),
      autoChangeCode: ref(true),
      isMounted: ref(false),
      categoryOptions,
    }
  },
  computed: {
    defaultModel() {
      return this.$store.getters['chroma/model']?.items?.find((el) => el.is_default && el?.type === 'prompts')
    },
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
    currentRaw() {
      return this.$store.getters.promptTemplate
    },
    collectionSystemNames: {
      get() {
        return this.collections.filter((el) => (this.newRow?.variants[0].retrieve?.collection_system_names || []).includes(el?.id))
      },
      set(value) {
        value = (value || []).map((el) => {
          if (typeof el === 'string') {
            return el
          } else {
            return el?.id
          }
        })
        this.newRow.variants[0].retrieve.collection_system_names = value
      },
    },
  },
  mounted() {
    this.searchString = ''

    if (this.copy) {
      this.newRow = reactive(cloneDeep(this.currentRaw))
      this.newRow.name = this.newRow.name + '_COPY'
      this.newRow.description = this.newRow.description + '_COPY'
      this.newRow.system_name = this.newRow.system_name + '_COPY'
      delete this.newRow.id
    } else {
      this.newRow.variants[0].system_name_for_model = this.defaultModel?.system_name
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
    async createRow() {
      if (!this.validateFields()) return

      this.createNew = false
      const result = await this.create(JSON.stringify(this.newRow))

      if (!result?.id) {
        return
      }

      await this.useCollection.selectRecord(result.id)
      await this.$store.commit('setPromptTemplate', this.newRow)
      this.$router.push(`/prompt-templates/${result.id}`)
    },
    validation(row, notify = true) {
      const { name, description, system_name, category } = row

      if (!name || !description || !system_name || !category) {
        // Handle validation error

        if (notify) {
          this.$q.notify({
            message: `Name, Description, System name and Category are required`,
            color: 'error-text',
            position: 'top',
            timeout: 1000,
          })
        }
        return false
      }

      return true
    },

    async openDetails(row) {
      await this.$router.push(`/prompt-templates/${row.id}`)
    },

    async refreshTable() {
      this.loadingRefresh = true
      this.useCollection.get()
      this.loadingRefresh = false
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
