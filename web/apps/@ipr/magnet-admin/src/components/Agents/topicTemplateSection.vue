<template lang="pug">
div
  km-section(
    :title='m.agents_topicSelectionPromptTemplate()',
    :subTitle='m.subtitle_topicSelection()'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.section_promptTemplate() }}
    km-select(
      height='30px',
      :placeholder='m.placeholder_selectPromptTemplate()',
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
          :label='topicSelectionPromptTemplate ? m.agents_openPromptTemplate() : m.agents_openPromptTemplatesLibrary()',
          iconSize='16px',
          icon='fas fa-comment-dots',
          @click='topicSelectionPromptTemplate ? navigate(`prompt-templates/${topicSelectionPromptTemplateId}`) : navigate("prompt-templates")'
        )
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
