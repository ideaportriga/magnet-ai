<template>
  <div>
    <km-section :title="m.section_conversationClosureInterval()" :sub-title="m.subtitle_closureInterval()">
      <km-btn-toggle v-model="conversationClosureInterval" :options="intervals" dense />
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_postProcessing()" :sub-title="m.subtitle_turnOnPostProcessing()">
      <km-toggle v-model="postProcessing" />
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.agents_postProcessingPromptTemplate()" :sub-title="m.subtitle_postProcessing()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_promptTemplate() }}</div>
      <km-select v-model="postProcessTemplate" height="30px" :placeholder="m.agents_postProcessPromptPlaceholder()" :options="promptTemplatesOptions" has-dropdown-search emit-value map-options option-value="system_name" :option-show="(item) =&gt; item?.category === &quot;agent&quot;" />
      <div class="cluster mt-sm">
        <div class="flex-none">
          <km-btn flat simple :label="postProcessTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="postProcessTemplate ? navigate(`prompt-templates/${postProcessTemplateId}`) : navigate(&quot;prompt-templates&quot;)" />
        </div>
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_messagePostProcessing()" :sub-title="m.subtitle_turnOnMessagePostProcessing()">
      <div class="stack" data-gap="0">
        <div class="flex-1 mb-md">
          <km-chip tone="brand" class="km-small-chip" :label="m.common_upcomingFeature()" />
        </div>
        <div class="flex-1">
          <km-toggle :model-value="false" disable dense />
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

const intervals = [
  { label: m.agents_interval1Day(), value: '1D' },
  { label: m.agents_interval3Days(), value: '3D' },
  { label: m.agents_interval1Week(), value: '7D' },
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
