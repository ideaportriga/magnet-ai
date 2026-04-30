<template>
  <div class="ba-border bg-white border-radius-12 p-lg" style="min-inline-size: 300px">
    <km-section :title="m.common_promptTemplate()" :sub-title="m.subtitle_promptTemplate()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_promptTemplate() }}</div>
      <km-select v-model="generatePromptTemplate" height="30px" :placeholder="m.retrieval_standardQaPrompt()" :options="prompts" has-dropdown-search />
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
import { computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  emits: ['openTest'],
  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('retrieval')
    const { data: promptListData } = queries.promptTemplates.useList()
    const promptItems = computed(() => promptListData.value?.items ?? [])
    return { m, activeVariant, updateVariantField, promptItems }
  },
  computed: {
    promptsWithId() {
      return (this.promptItems ?? []).map((item) => ({ label: item.name, value: item.system_name, id: item.id }))
    },
    generatePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.activeVariant?.generate?.prompt_template)?.id
    },
    prompts() {
      return (this.promptItems ?? [])
        .map((item) => ({
          label: item.name,
          value: item.id,
          system_name: item.system_name,
          category: item.variants?.find((el) => el?.variant == item?.active_variant)?.category,
        }))
        .filter((el) => el.category === 'RAG')
    },
    propmt_name() {
      return (this.promptItems ?? []).find((el) => el.system_name === this.prompt_template)?.name
    },
    prompt_template() {
      return this.activeVariant?.generate?.prompt_template
    },
    generatePromptTemplate: {
      get() {
        return this.propmt_name
      },
      set(value) {
        this.updateVariantField('generate.prompt_template', value.system_name)
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
