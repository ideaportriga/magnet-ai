<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newPromptTemplate()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :notification="m.hint_editAfterSaving()" @confirm="createRow" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_name() }}
      <div class="full-width">
        <km-input ref="nameRef" v-model="name" data-test="name-input" height="30px" :placeholder="m.placeholder_exampleDemoPromptTemplate()" :rules="config.name.rules" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_systemName() }}
      <div class="full-width">
        <km-input ref="system_nameRef" v-model="system_name" data-test="system-name-input" height="30px" :placeholder="m.placeholder_examplePromptTemplateDemo()" :rules="config.system_name.rules" />
      </div>
      <div class="km-description text-secondary-text pb-xs">{{ m.hint_systemNameUniqueId() }}</div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm">
      {{ m.label_categories() }}
      <km-dropdown-select ref="categoryRef" v-model="newRow.category" class="full-width" data-test="select-category" :placeholder="m.label_categories()" :options="categoryOptions" :rules="config.category.rules" />
    </div>
  </km-popup-confirm>
</template>

<script>
import { ref, reactive } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { validateRef } from '@/utils/validateRef'
import { cloneDeep } from 'lodash' // Import lodash for deep cloning
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { categoryOptions } from '@/config/prompts/prompts'
import { notify } from '@shared/utils/notify'
import KmDropdownSelect from '@ds/components/domain/KmDropdownSelect.vue'

export default {
  components: { KmDropdownSelect },
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
    const { config, requiredFields } = useEntityConfig('promptTemplates')
    const queries = useEntityQueries()
    const { draft } = useVariantEntityDetail('promptTemplates')
    const { mutateAsync: createPromptTemplate } = queries.promptTemplates.useCreate()
    const { data: modelListData } = queries.model.useList()

    return {
      m,
      draft,
      modelListData,
      requiredFields,
      config,
      createPromptTemplate,
      createNew: ref(false),
      newRow: reactive({
        name: '',
        description: '',
        system_name: '',
        category: 'generic',
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
      return (this.modelListData?.items ?? []).find((el) => el.is_default && el?.type === 'prompts')
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
      return this.draft
    },
    collectionSystemNames: {
      get() {
        return (this.collections || []).filter((el) => (this.newRow?.variants[0].retrieve?.collection_system_names || []).includes(el?.id))
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
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
      return !validStates.includes(false)
    },
    async createRow() {
      if (!this.validateFields()) return

      this.createNew = false
      const result = await this.createPromptTemplate(this.newRow)

      if (!result?.id) {
        return
      }

      this.$router.push(`/prompt-templates/${result.id}`)
    },
    validation(row, showNotify = true) {
      const { name, description, system_name, category } = row

      if (!name || !description || !system_name || !category) {
        if (showNotify) {
          notify.error(m.validation_required())
        }
        return false
      }

      return true
    },

    async openDetails(row) {
      await this.$router.push(`/prompt-templates/${row.id}`)
    },

  },
}
</script>

