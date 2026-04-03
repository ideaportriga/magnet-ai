<template lang="pug">
div
  km-section(:title='m.section_conversationClosureInterval()', :subTitle='m.subtitle_closureInterval()')
    q-btn-toggle(
      v-model='conversationClosureInterval',
      toggle-color='primary-light',
      :options='intervals',
      dense,
      text-color='text-weak',
      toggle-text-color='primary'
    )
  q-separator.q-my-lg
  km-section(:title='m.section_postProcessing()', :subTitle='m.subtitle_turnOnPostProcessing()')
    q-toggle(v-model='postProcessing', color='primary')
  q-separator.q-my-lg
  km-section(
    :title='m.agents_postProcessingPromptTemplate()',
    :subTitle='m.subtitle_postProcessing()'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_promptTemplate() }}
    km-select(
      height='30px',
      placeholder='Post-process Prompt',
      :options='promptTemplatesOptions',
      v-model='postProcessTemplate',
      hasDropdownSearch,
      emit-value,
      map-options,
      option-value='system_name',
      :option-show='(item) => item?.category === "agent"'
    )
    .row.q-mt-sm
      .col-auto
        km-btn(
          flat,
          simple,
          :label='postProcessTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
          iconSize='16px',
          icon='fas fa-comment-dots',
          @click='postProcessTemplate ? navigate(`prompt-templates/${postProcessTemplateId}`) : navigate("prompt-templates")'
        )
  q-separator.q-my-lg
  km-section(:title='m.section_messagePostProcessing()', :subTitle='m.subtitle_turnOnMessagePostProcessing()')
    .column
      .col.q-mb-md
        q-chip.km-small-chip(color='primary-light', text-color='primary', :label='m.common_upcomingFeature()')
      .col
        q-toggle(:model-value='false', disable, dense)
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

const intervals = [
  { label: '1 day', value: '1D' },
  { label: '3 day', value: '3D' },
  { label: '1 week', value: '7D' },
]

export default {
  setup() {
    const { activeVariant, updateVariantField } = useAgentEntityDetail()
    const queries = useEntityQueries()
    const { data: promptTemplateData } = queries.promptTemplates.useList()
    const promptTemplateItems = computed(() => promptTemplateData.value?.items ?? [])

    // Jobs list with filter - TQ auto-fetches
    queries.jobs.useList()

    return {
      m,
      activeVariant,
      updateVariantField,
      promptTemplateItems,
      intervals,
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
    postProcessTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.postProcessTemplate)?.id
    },
    postProcessTemplate: {
      get() {
        return this.activeVariant?.value.post_processing?.template
      },
      set(value) {
        this.updateVariantField('post_processing.template', value)
      },
    },
    postProcessing: {
      get() {
        return this.activeVariant?.value?.post_processing?.enabled || false
      },
      set(value) {
        this.updateVariantField('post_processing.enabled', value)
      },
    },
    conversationClosureInterval: {
      get() {
        return this.activeVariant?.value?.settings?.conversation_closure_interval || '1D'
      },
      set(value) {
        this.updateVariantField('settings.conversation_closure_interval', value)
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
