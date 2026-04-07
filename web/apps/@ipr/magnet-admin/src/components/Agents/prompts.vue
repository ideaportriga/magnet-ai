<template lang="pug">
div
  km-section(
    :title='m.agents_topicSelectionPromptTemplate()',
    :subTitle='m.subtitle_topicSelection()'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_promptTemplate() }}
    km-select(
      height='30px',
      :placeholder='m.agents_standardQaPrompt()',
      :options='promptTemplatesOptions',
      v-model='topicSelectionPromptTemplate',
      hasDropdownSearch,
      emit-value,
      map-options,
      option-value='system_name',
      :option-show='(item) => item?.category === "agent"'
    )
    .km-description.text-secondary-text.q-pb-4 {{ m.agents_promptTemplateMustSupportJson() }}
    .row.q-mt-sm
      .col-auto
        km-btn(
          flat,
          simple,
          :label='topicSelectionPromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
          iconSize='16px',
          icon='fas fa-comment-dots',
          @click='topicSelectionPromptTemplate ? navigate(`prompt-templates/${topicSelectionPromptTemplateId}`) : navigate("prompt-templates")'
        )
  q-separator.q-my-lg
  km-section(
    :title='m.agents_topicProcessingPromptTemplate()',
    :subTitle='m.subtitle_topicProcessing()'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_promptTemplate() }}
    km-select(
      height='30px',
      :options='promptTemplatesOptions',
      v-model='topicProcessingPromptTemplate',
      hasDropdownSearch,
      emit-value,
      map-options,
      option-value='system_name',
      :option-show='(item) => item?.category === "agent"'
    )
    .km-description.text-secondary-text.q-pb-4 {{ m.agents_promptTemplateMustSupportToolCalling() }}
    .row.q-mt-sm
      .col-auto
        km-btn(
          flat,
          simple,
          :label='topicProcessingPromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
          iconSize='16px',
          icon='fas fa-comment-dots',
          @click='topicProcessingPromptTemplate ? navigate(`prompt-templates/${topicProcessingPromptTemplateId}`) : navigate("prompt-templates")'
        )
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  emits: ['openTest'],
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

    topicProcessingPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicProcessingPromptTemplate)?.id
    },

    topicSelectionPromptTemplate: {
      get() {
        return this.activeVariant?.value.prompt_templates?.classification
      },
      set(value) {
        this.updateVariantField('prompt_templates.classification', value)
      },
    },
    topicProcessingPromptTemplate: {
      get() {
        return this.activeVariant?.value.prompt_templates?.topic_processing
      },
      set(value) {
        this.updateVariantField('prompt_templates.topic_processing', value)
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
