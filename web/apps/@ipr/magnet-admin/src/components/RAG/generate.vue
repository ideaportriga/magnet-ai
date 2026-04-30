<template>
  <div>
    <km-section :title="m.common_promptTemplate()" :sub-title="m.subtitle_promptTemplate()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_promptTemplate() }}</div>
      <km-select v-model="generatePromptTemplate" height="30px" :placeholder="m.ragTools_standardQaPrompt()" :options="promptTemplatesOptions" has-dropdown-search emit-value map-options option-value="system_name" :option-show="(item) =&gt; item?.category === &quot;rag&quot;" />
      <div class="cluster mt-sm">
        <div class="flex-none">
          <km-btn flat simple :label="generatePromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="generatePromptTemplate ? navigate(`prompt-templates/${generatePromptTemplateId}`) : navigate(&quot;prompt-templates&quot;)" />
        </div>
      </div>
    </km-section>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  emits: ['openTest'],
  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('rag_tools')
    const { data: promptTemplateListData } = queries.promptTemplates.useList()
    return {
      m,
      activeVariant,
      updateVariantField,
      promptTemplateListData,
    }
  },
  computed: {
    promptTemplateItems() {
      return this.promptTemplateListData?.items ?? []
    },
    generatePromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.generatePromptTemplate)?.id
    },
    promptTemplatesOptions() {
      return (this.promptTemplateItems ?? []).map((item) => ({
        label: item.name,
        value: item.id,
        system_name: item.system_name,
        category: item?.category,
        id: item.id,
      }))
    },
    generatePromptTemplate: {
      get() {
        return this.activeVariant?.generate?.prompt_template
      },
      set(value) {
        this.updateVariantField('generate.prompt_template', value)
      },
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
