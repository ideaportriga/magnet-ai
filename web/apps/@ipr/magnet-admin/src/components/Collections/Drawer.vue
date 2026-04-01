<template lang="pug">
km-drawer-layout(storageKey="drawer-collections", noScroll)
  template(#header)
    .km-heading-7(v-if='!showChunkInfo') Preview
  .column.full-height(v-if='!showChunkInfo')
    .col.column.no-wrap.q-pb-md.relative-position.q-px-16
      retrieval-metadata-filter(v-model='metadataFilter', :sources='[knowledgeSystemName]')
      q-separator.q-mt-md.q-mb-md
      .column.search-prompt-container.border-radius-12.q-mb-16.full-width.q-gap-8
        .row
          km-input.full-width(
            ref='input',
            autogrow,
            border-radius='8px',
            height='36px',
            :model-value='prompt',
            @input='prompt = $event',
            @keydown.enter='submit'
          )
            template(#append='{ height }')
              .self-end.center-flex(:style='{ height }')
                q-btn.border-radius-6(color='primary', @click='getAnswer', unelevated, padding='6px 7px')
                  template(v-slot:default)
                    q-icon(name='fas fa-search', size='16px')
          .km-description.text-secondary-text.q-mt-xs Perform semantic search for your search term. Returns best 15 results

      template(v-if='answers.length || loading')
        q-scroll-area.full-height.col(ref='scroll')
          .column.q-gap-16
            template(v-if='loading')
              .row.justify-center.ba-border.border-radius-12.bg-white.q-pa-16.q-gap-16
                q-spinner-dots(size='62px', color='primary')
            template(v-for='answer in answers')
              collections-answer(:answer='answer', @refine='refine', @selectAnswer='setDetailInfo')

  template(v-if='showChunkInfo')
    collections-drawer-chunk(:selectedRow='selectedAnswer', @close='showChunkInfo = false')
</template>

<script>
import { fetchData } from '@shared'
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useCollectionDetailStore } from '@/stores/entityDetailStores'
import { useAppStore } from '@/stores/appStore'
import { useSearchStore } from '@/stores/searchStore'

export default {
  props: ['open'],
  emits: ['onLoad'],
  setup() {
    const collectionStore = useCollectionDetailStore()
    const appStore = useAppStore()
    const searchStore = useSearchStore()
    const {
      semanticSearchAnswers: answers,
      semanticSearchLoading: loading,
      semanticSearch: prompt,
      metadataFilter,
    } = storeToRefs(searchStore)

    function clearSemanticSearchAnswers() {
      answers.value = []
    }

    return {
      loading,
      answers,
      prompt,
      metadataFilter,
      collectionStore,
      appStore,
      showHints: ref(true),
      showChunkInfo: ref(false),
      selectedAnswer: ref({}),
      clearSemanticSearchAnswers,
    }
  },
  computed: {
    knowledgeId() {
      return this.collectionStore.entity?.id || ''
    },
    knowledgeSystemName() {
      return this.collectionStore.entity?.system_name || ''
    },
  },
  watch: {
    knowledgeId(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.prompt = ''
        this.metadataFilter = []
      }
    },
  },
  created() {},
  mounted() {
    this.prompt = ''
    this.metadataFilter = []
  },
  methods: {
    setDetailInfo(info) {

      this.selectedAnswer = info
      this.showChunkInfo = true
    },
    clearAnswers() {
      this.clearSemanticSearchAnswers()
    },
    refine(question) {
      this.prompt = question
      this.$refs?.input.focus()
    },
    scrollTop() {
      this.$refs?.scroll?.setScrollPosition?.('vertical', 0, 200)
    },
    submit(event) {
      if (!event.shiftKey) {
        event.preventDefault()
        this.getAnswer()
      }
    },
    async getAnswer() {
      const { convertFiltersToFilterObject } = await import('@shared')
      const prompt = this.prompt
      const metadataFilter = convertFiltersToFilterObject(this.metadataFilter)
      const collection_id = this.collectionStore.entity?.system_name
      const collection_display_name = this.collectionStore.entity?.name
      const endpoint = this.appStore.config?.documentSemanticSearch?.endpoint
      const service = `${this.appStore.config?.documentSemanticSearch?.service}` || ''
      const credentials = this.appStore.config?.documentSemanticSearch?.credentials

      this.loading = true
      const response = await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
        body: JSON.stringify({
          collection_id,
          collection_display_name,
          user_message: prompt,
          metadata_filter: metadataFilter,
        }),
        headers: { 'Content-Type': 'application/json' },
      })
      this.loading = false

      if (!response?.error) {
        const answer = await response.json()
        this.answers = [{ prompt, collection: collection_id, ...answer }, ...this.answers]
      }

      this.prompt = ''
      this.$refs?.input.blur()
      this.$emit('onLoad')
    },
  },
}
</script>

<style lang="stylus" scoped>
.search-container {
  min-width: 450px;
  max-width: 800px;
  width: 100%;
}
</style>
