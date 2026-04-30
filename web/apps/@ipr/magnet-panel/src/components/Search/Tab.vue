<template>
  <div
    class="cluster full-height p-lg fit relative-position"
    data-wrap="no"
    data-justify="center"
  >
    <div
      class="stack search-container"
      data-gap="0"
    >
      <!--prompt-->
      <div class="bg-user-input-bg px-lg">
        <search-prompt
          ref="prompt"
          class="mt-md"
          hide-collection-picker
          :rag_code="rag_code"
          @on-load="scrollTop"
        />
      </div>
      <!--hints-->
      <template v-if="isShowHints">
        <div class="cluster mt-lg mb-sm">
          <div class="flex-1 km-heading-3">
            {{ m.common_youCanAskLikeThis() }}
          </div>
          <div class="flex-none">
            <km-btn
              flat
              tone="brand"
              @click="showHints = false"
            >
              <div class="km-button-text">
                {{ m.common_dontShowHints() }}
              </div>
            </km-btn>
          </div>
        </div>
        <template v-if="$theme === &quot;default&quot;">
          <template
            v-for="(item, index) in sampleQuestion"
            :key="index"
          >
            <km-btn
              flat
              @click="refine(item)"
            >
              <div class="wrapped-text">
                {{ item }}
              </div>
            </km-btn>
          </template>
        </template>
        <template v-else>
          <template
            v-for="(item, index) in sampleQuestion"
            :key="index"
          >
            <div class="flex">
              <km-btn
                class="hint"
                flat
                tone="brand"
                @click="refine(item)"
              >
                <div class="wrapped-text">
                  {{ item }}
                </div>
              </km-btn>
            </div>
          </template>
        </template>
      </template>
      <!--answers-->
      <template v-if="answers.length">
        <km-scroll-area
          ref="scroll"
          class="full-height flex-1"
        >
          <div
            class="stack mt-md"
            data-gap="lg"
          >
            <template
              v-for="(answer, index) in answers"
              :key="index"
            >
              <search-answer
                :answer="answer"
                :ui-settings="uiSettings"
                :is-last-message="index == 0"
                @refine="refine"
              />
            </template>
          </div>
        </km-scroll-area>
      </template>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useSearch, useAiApps } from '@/pinia'
import { storeToRefs } from 'pinia'
export default {
  props: {
    index: Number,
    open: Boolean,
    // eslint-disable-next-line vue/prop-name-casing
    rag_code: {
      type: String,
      default: '',
    },
  },
  setup() {
    const searchStore = useSearch()

    const { answers: storeAnswers, answersLoading: loading } = storeToRefs(searchStore)
    const aiAppsStore = useAiApps()
    const { app, displayTab } = storeToRefs(aiAppsStore)

    return {
      loading,
      storeAnswers,
      showHints: ref(true),
      searchStore,
      app,
      displayTab,
      m,
    }
  },
  computed: {
    answers() {
      return this.storeAnswers
    },
    allAnswers() {
      return [...this.answers].reverse()
    },
    panel() {
      return this.displayTab
    },
    tool() {
      return this.panel?.entityObject
    },
    systemName() {
      return this.tool?.system_name || ''
    },
    uiSettings() {
      return this.defaultRagActiveVariant?.ui_settings
    },
    isShowHints() {
      return (
        this.answers?.length == 0 &&
        this.showHints &&
        this.uiSettings?.sample_questions?.enabled &&
        (!!this.uiSettings?.sample_questions?.questions?.question1 ||
          !!this.uiSettings?.sample_questions?.questions?.question2 ||
          !!this.uiSettings?.sample_questions?.questions?.question3)
      )
    },
    defaultRagActiveVariant() {
      return this.tool?.active_variant
    },
    sampleQuestion() {
      return this.defaultRagActiveVariant?.ui_settings?.sample_questions?.questions
    },
  },
  watch: {
    systemName(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.clearAnswers()
      }
    },
  },
  created() {},
  mounted() {
    this.clearAnswers()
  },
  methods: {
    clearAnswers() {
      this.answers = []
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
@media (max-width: 500px) {
  .search-container {
    min-inline-size: unset;
    max-inline-size: unset;
  }
}
</style>
