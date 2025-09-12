<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Test Set',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  @confirm='createEvaluationSet',
  @cancel='$emit("cancel")',
  :loading='loading'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
    .full-width
      km-input(height='30px', placeholder='E.g. My first Test Set', v-model='name', ref='nameRef', :rules='config.name.rules')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Description
    .full-width
      km-input(
        height='30px',
        placeholder='E.g. My first test set for RAG',
        v-model='newRow.description',
        ref='descriptionRef',
        :rules='config.description.rules'
      )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(height='30px', placeholder='E.g. MY_FIRST_TEST_SET', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
    .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Type
    km-select(
      minHeight='30px',
      maxHeight='30px',
      placeholder='Type',
      :options='[ { value: "rag_tool", label: "RAG" }, { value: "prompt_template", label: "Prompt Template" }, ]',
      v-model='newRow.type',
      ref='typeRef',
      option-value='value',
      emit-value,
      map-options,
      :rules='config.type.rules'
    )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8(v-if='!copy') File
    q-file.km-control.km-input.rounded-borders(
      style='height: 30px',
      outlined,
      label='File upload',
      ref='fileRef',
      v-model='newRow.file',
      accept='.xlsx, .xls',
      dense
    )
      template(v-slot:append)
        q-icon(name='attach_file')

    .km-description.text-secondary-text.q-pb-4 Accept only .xlsx files. The file should contain the following columns: the first column for 'Evaluation input', and the second column for 'Expected output'
    //- template(v-slot:prepend)
    //-   q-icon(name='attach_file')
    //- template(v-slot:append)
      //- q-icon(name='close', @click="newRow.file = null", color='icon', size='24px')
</template>
<script>
import { ref, reactive } from 'vue'
import { useChroma } from '@shared'
import { cloneDeep } from 'lodash'
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
    const { items, searchString, create, config, requiredFields, ...useCollection } = useChroma('evaluation_sets')
    const { publicItems } = useChroma('collections')

    return {
      items,
      searchString,
      config,
      useCollection,
      create,
      loading: ref(false),
      createNew: ref(false),
      collections: publicItems,
      requiredFields,
      newRow: reactive({
        name: '',
        description: '',
        system_name: '',
      }),
      autoChangeCode: ref(true),
    }
  },
  computed: {
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
      return this.$store.getters.evaluation_set
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
    async createEvaluationSet() {
      if (!this.validateFields()) return

      this.createNew = false
      this.loading = true
      const { id:inserted_id } = await this.create(this.newRow)
      await this.useCollection.selectRecord(inserted_id)
      this.$store.commit('setEvaluationSet', this.newRow)
      this.loading = false
      this.$router.push(`/evaluation-sets/${inserted_id}`)
    },
    validation(rag, notify = true) {
      const { name, description, system_name, retrieve } = rag
      const { collection_system_names } = retrieve

      if (!name || !description || !system_name || !collection_system_names.length) {
        // Handle validation error

        if (notify) {
          this.$q.notify({
            message: `Name, Description, System name and Knowledge sources are required`,
            color: 'error-text',
            position: 'top',
            timeout: 1000,
          })
        }
        return false
      }
      return true
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
