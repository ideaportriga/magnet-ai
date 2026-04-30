<template>
  <div
    class="stack search-prompt-container border-radius-12 mb-lg full-width"
    data-gap="sm"
  >
    <div class="cluster">
      <km-input
        ref="input"
        class="full-width"
        autogrow
        :placeholder="m.placeholder_typeQuestionHere()"
        :model-value="prompt"
        border-radius="8px"
        height="var(--prompt-input-height)"
        @input="prompt = $event"
        @keydown.enter="submit"
      >
        <template #append="{ height }">
          <div
            class="self-end center-flex"
            :style="{ height }"
          >
            <km-btn
              class="border-radius-6"
              unelevated
              :padding="$theme != &quot;salesforce&quot; ? &quot;6px 7px&quot; : &quot;9px 17px 9px 17px&quot;"
              @click="getAnswer"
            >
              <template #default>
                <km-glyph
                  name="search"
                  size="var(--prompt-input-icon-size)"
                />
              </template>
            </km-btn>
          </div>
        </template>
      </km-input>
    </div>
  </div>
</template>

<script>
import { useSearch } from '@/pinia'
import { storeToRefs } from 'pinia'
import { m } from '@/paraglide/messages'

export default {
  expose: ['refine'],
  props: {
    hideCollectionPicker: {
      default: false,
      type: Boolean,
    },
    rag: {
      default: false,
      type: Boolean,
    },
    // eslint-disable-next-line vue/prop-name-casing
    rag_code: {
      type: String,
      default: '',
    },
  },
  emits: ['onLoad'],
  setup() {
    const searchStore = useSearch()
    const { searchPrompt: prompt, answersLoading: loading } = storeToRefs(searchStore)

    return {
      prompt,
      loading,
      searchStore,
      m,
    }
  },
  computed: {},
  watch: {},
  created() {},
  mounted() {},
  methods: {
    refine(question) {
      this.prompt = question
      this.$refs?.input.focus()
    },
    submit(event) {
      if (!event.shiftKey) {
        event.preventDefault()
        this.getAnswer()
      }
    },
    async getAnswer() {
      this.searchStore.getAnswerRagExecute(this.rag_code)

      this.prompt = ''
      this.$refs?.input.blur()
      this.$emit('onLoad')
    },
  },
}
</script>

<style scoped>
.search-prompt-container {
  min-inline-size: 450px;
  max-inline-size: 800px;
  inline-size: 100%;
}
@media (max-width: 500px) {
  .search-prompt-container {
    min-inline-size: unset;
    max-inline-size: unset;
  }
}
</style>
