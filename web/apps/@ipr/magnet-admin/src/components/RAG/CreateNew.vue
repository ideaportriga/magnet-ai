<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newRagTool()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_editAfterSaving()" @confirm="createRag" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_name() }}
      <div class="full-width">
        <km-input ref="nameRef" v-model="name" data-test="name-input" height="30px" :placeholder="m.placeholder_exampleDemoRagTool()" :rules="config.name.rules" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_systemName() }}
      <div class="full-width">
        <km-input ref="system_nameRef" v-model="system_name" data-test="system_name-input" height="30px" :placeholder="m.placeholder_exampleRagToolDemo()" :rules="config.system_name.rules" />
      </div>
      <div class="km-description text-secondary-text pb-xs">{{ m.hint_systemNameUniqueId() }}</div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm">
      {{ m.label_knowledgeSources() }}
      <km-select ref="sourecesRef" v-model="collectionSystemNames" data-test="knowledge-sources" height="auto" min-height="36px" :placeholder="m.common_selectKnowledgeSources()" multiple :options="collections" option-label="name" option-value="system_name" use-chips has-dropdown-search :rules="config.soureces.rules" />
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
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useSafeMutation } from '@/composables/useSafeMutation'

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
    const { config, requiredFields } = useEntityConfig('rag_tools')
    const queries = useEntityQueries()
    const { draft } = useVariantEntityDetail('rag_tools')
    const createRagTool = useSafeMutation(queries.rag_tools.useCreate())
    const { options: collections } = useCatalogOptions('collections')

    return {
      m,
      draft,
      config,
      createRagTool,
      createNew: ref(false),
      collections,
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
              chunk_context_window_expansion_size: 0,
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
      return this.draft
    },
    collectionSystemNames: {
      get() {
        return (this.collections || []).filter((el) => (this.newRow.variants[0]?.retrieve?.collection_system_names || []).includes(el?.system_name))
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
    async createRag() {
      if (!this.validateFields()) return

      this.createNew = false
      const { success, data } = await this.createRagTool.run(this.newRow)
      if (!success || !data?.id) return

      this.$router.push(`/rag-tools/${data.id}`)
    },
  },
}
</script>

