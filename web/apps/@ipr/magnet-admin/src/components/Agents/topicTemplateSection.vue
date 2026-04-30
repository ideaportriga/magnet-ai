<template>
  <div>
    <km-section :title="m.agents_topicSelectionPromptTemplate()" :sub-title="m.subtitle_topicSelection()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.section_promptTemplate() }}</div>
      <km-select v-model="topicSelectionPromptTemplate" height="30px" :placeholder="m.placeholder_selectPromptTemplate()" :options="promptTemplatesOptions" has-dropdown-search emit-value map-options option-value="system_name" :option-show="(item) =&gt; item?.category === &quot;agent&quot;" />
      <div class="km-description text-secondary-text pb-xs">{{ m.agents_promptTemplateMustSupportJson() }}</div>
      <div class="cluster mt-sm">
        <div class="flex-none">
          <km-btn flat simple :label="topicSelectionPromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="topicSelectionPromptTemplate ? navigate(`prompt-templates/${topicSelectionPromptTemplateId}`) : navigate(&quot;prompt-templates&quot;)" />
        </div>
      </div>
    </km-section>
  </div>
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  setup() {
    const queries = useEntityQueries()
    const { data: promptTemplateData } = queries.promptTemplates.useList()
    const promptTemplateItems = computed(() => promptTemplateData.value?.items ?? [])
    const { activeVariant, updateVariantField } = useAgentEntityDetail()

    return {
      m,
      activeVariant,
      updateVariantField,
      promptTemplateItems,
    }
  },
  computed: {
    promptTemplatesOptions() {
      return (this.promptTemplateItems ?? []).map((item) => ({
        label: item.name,
        value: item.id,
        system_name: item.system_name,
        category: item.category,
        id: item.id,
      }))
    },
    topicSelectionPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicSelectionPromptTemplate)?.id
    },
    topicSelectionPromptTemplate: {
      get() {
        return this.activeVariant?.value.prompt_templates?.classification
      },
      set(value) {
        this.updateVariantField('prompt_templates.classification', value)
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
