<template>
  <div class="stack bg-white ba-border px-lg pt-xs pb-2xl border-radius-12" data-gap="lg" :class="{ &quot;no-pointer-events prevent-select opaque&quot;: readonly }">
    <div class="km-heading-4 pt-2xl">{{ m.common_testPromptTemplate() }}</div>
    <div class="cluster mt-sm" data-gap="sm">
      <div class="flex-none pl-xs">
        <div class="circle-accent" />
      </div>
      <div class="flex-1">
        <div class="km-description text-secondary-text">{{ m.common_enterTextToTest() }}</div>
      </div>
    </div>
    <km-input ref="input" class="full-width" autogrow :placeholder="m.common_typeTextToTest()" :model-value="inputText" border-radius="8px" @input="inputText = $event" @keydown.enter="submit">
      <template #append>
        <div class="fit bottom-flex">
          <km-btn class="my-sm border-radius-6" :disabled="disabled" unelevated padding="7px 8px" @click="submit">
            <template #default>
              <km-glyph name="send" size="16px" />
            </template>
          </km-btn>
        </div>
      </template>
    </km-input>
    <template v-if="loading">
      <div class="cluster" data-justify="center">
        <km-loader size="62px" />
      </div>
    </template>
    <template v-else-if="text !== undefined">
      <div class="cluster pt-18" data-gap="lg" data-wrap="no">
        <div class="flex-none">
          <km-avatar tone="brand" size="36px">
            <km-icon :name="&quot;magnet&quot;" width="20" height="22" />
          </km-avatar>
        </div>
        <div class="flex-1 border-radius-12 bg-light pb-md">
          <div class="py-lg px-2xl">
            <div class="km-paretrievalraph text-pre-wrap">{{ text }}</div>
          </div>
          <div class="cluster pr-md" data-justify="end">
            <div class="flex-none">
              <km-btn icon="copy" icon-size="16px" size="sm" flat content-class="text-label" :label="m.common_copy()" @click="copy" />
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
import { ref } from 'vue'
import { useSpecificationsStore } from '@/stores/specificationsStore'

export default {
  props: ['prompt', 'readonly'],
  emits: ['onLoad'],
  setup() {
    const specsStore = useSpecificationsStore()
    return {
      m,
      specsStore,
      inputText: ref(''),
      text: ref(undefined),
    }
  },

  computed: {
    disabled() {
      return !this.inputText || this.loading
    },
    loading() {
      return this.specsStore.enhancedTextLoading
    },
  },
  created() {},
  mounted() {},
  methods: {
    async submit() {
      this.text = (await this.specsStore.enhanceText({ text: this.inputText, prompt: this.prompt.text })) || undefined
      this.$refs?.input.blur()
    },
  },
}
</script>

<style scoped>
.circle-accent {
  block-size: 16px;
  inline-size: 16px;
  border-radius: 50%;
  background: var(--ds-color-primary);
  opacity: 0.5;
}
.opaque {
  opacity: 0.5;
}
</style>
