<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Retrieval Tool',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to edit these and other settings after saving.',
  @confirm='createRetrieval',
  @cancel='$emit("cancel")'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
    .full-width
      km-input(height='30px', placeholder='E.g. Demo Retrieval Tool', v-model='name', ref='nameRef', :rules='config.name.rules')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(height='30px', placeholder='E.g. RETRIEVAL_TOOL_DEMO', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
    .km-description.text-secondary-text.q-pb-4 System name serves as a unique record ID
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Knowledge sources
  km-select(
    height='auto',
    minHeight='36px',
    placeholder='Select knowledge sources',
    multiple,
    :options='collections',
    v-model='collectionSystemNames',
    use-chips,
    hasDropdownSearch,
    ref='sourecesRef',
    :rules='config.soureces.rules'
  )
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
    const { items, searchString, create, config, requiredFields, ...useCollection } = useChroma('retrieval')
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
      newRow: reactive({
        name: '',
        description: '',
        system_name: '',
        active_variant: 'variant_1',
        variants: [
          {
            variant: 'variant_1',
            retrieve: {
              similarity_score_threshold: 0.75,
              max_chunks_retrieved: 5,
              chunk_context_window_expansion_size: 1,
              collection_system_names: [],
            },
            generate: {
              prompt_template: 'QA_SYSTEM_PROMPT_TEMPLATE',
            },
            language: {
              detect_question_language: {
                enabled: false,
                prompt_template: 'RAG_TOOL_DETECT_LANGUAGE',
              },
              multilanguage: {
                enabled: false,
                source_language: 'English',
                prompt_template_translation: 'RAG_TOOL_TRANSLATE_TEXT',
              },
            },
            post_process: {
              answered_check: {
                prompt_template: 'Q&A_RESPONSE_CHECK',
              },
              check_is_hallucinate: {
                prompt_template: 'QA_HALLUCINATION_CHECK',
              },
              detect_question_language: {
                prompt_template: 'RAG_TOOL_DETECT_LANGUAGE',
              },
            },
          },
        ],
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
      return this.$store.getters.retrieval
    },
    collectionSystemNames: {
      get() {
        return this.collections.filter((el) => (this.newRow.variants[0]?.retrieve?.collection_system_names || []).includes(el?.system_name))
      },
      set(value) {
        value = (value || []).map((el) => {
          if (typeof el === 'string') {
            return el
          } else {
            return el?.system_name
          }
        })
        this.newRow.variants[0].retrieve.collection_system_names = value
      },
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
    async createRetrieval() {
      if (!this.validateFields()) return

      this.createNew = false
      const { id } = await this.create(JSON.stringify(this.newRow))
      await this.useCollection.selectRecord(id)
      this.$store.commit('setRetrieval', this.newRow)
      this.$router.push(`/retrieval/${id}`)
    },
    validation(retrieval, notify = true) {
      const { name, description, system_name, retrieve } = retrieval
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
