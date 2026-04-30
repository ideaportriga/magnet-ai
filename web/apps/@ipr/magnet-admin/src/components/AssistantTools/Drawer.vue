<template>
  <km-drawer-layout storage-key="drawer-assistant-tools">
    <template #header>
      <div v-if="!showChunkInfo" class="km-heading-7">{{ m.assistantTools_toolDefinition() }}</div>
    </template>
    <div v-if="!showChunkInfo">
      <km-codemirror :model-value="definition" :readonly="true" language="json" />
    </div>
  </km-drawer-layout>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { storeToRefs } from 'pinia'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useSearchStore } from '@/stores/searchStore'

export default {
  props: ['open'],
  setup() {
    const { draft } = useEntityDetail('assistant_tools')
    const searchStore = useSearchStore()
    const { answers, answersLoading: loading } = storeToRefs(searchStore)
    return {
      loading,
      answers,
      draft,
      searchStore,
      m,
      showHints: ref(true),
      selectedAnswer: ref({}),
      showChunkInfo: ref(false),
      showNewDialog: ref(false),
      showEvaluationCreateDialog: ref(false),
      evaluationId: ref(''),
    }
  },
  computed: {
    definition: {
      get() {
        return JSON.stringify(this.draft?.definition, null, 2) || ''
      },
    },
  },
  watch: {},
  mounted() {},
  methods: {
    createEvaluation(obj) {
      this.evaluationId = obj?.id
      this.showNewDialog = false
      if (this.evaluationId) this.showEvaluationCreateDialog = true
    },
    navigate(path = '') {
      if (this.$route?.path !== `/${path}`) {
        this.$router?.push(`/${path}`)
      }
    },
    setDetailInfo(info) {
      this.selectedAnswer = info
      this.showChunkInfo = true
    },
    clearAnswers() {
      this.searchStore.clearAnswers()
    },
    refine(question) {
      this.$refs?.prompt?.refine(question)
    },
    scrollTop() {
      this.$refs?.scroll?.setScrollPosition?.('vertical', 0, 200)
    },
  },
}
</script>

<style scoped>
.search-container {
  min-inline-size: 450px;
  max-inline-size: 800px;
  inline-size: 100%;
}
</style>
