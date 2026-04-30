<template>
  <km-dialog
    v-model="value"
    position="top"
    persistent
    square
    @hide="clearError"
  >
    <div
      class="mt-0 bg-red text-white"
      style="inline-size: 640px; border-radius: 0px 0px 8px 8px !important"
    >
      <div
        class="cluster bg-red px-md py-sm"
        data-wrap="no"
        style="block-size: 48px"
      >
        <km-glyph
          class="mr-sm"
          name="error"
          size="28px"
        />
        <div class="flex-1">
          <div class="km-heading-6">
            {{ m.error_dialog() }}
          </div>
        </div>
        <km-btn
          icon="close"
          flat
          round
          dense
          @click="close"
        />
      </div>
      <div class="stack px-lg py-sm">
        <div
          v-if="!text &amp;&amp; !technicalError"
          class="my-xs km-body"
        >
          {{ m.error_unknownError() }}
        </div>
        <div
          v-if="text"
          class="my-xs km-body"
        >
          {{ errorMessage?.text }}
        </div>
        <div
          v-if="technicalError"
          class="mt-sm mb-xs km-chip"
        >
          {{ errorMessage?.technicalError }}
        </div>
        <div class="mt-md mb-sm self-end">
          <div>
            <km-btn
              tone="inverse"
              flat
              @click="close"
            >
              {{ m.common_ok() }}
            </km-btn>
          </div>
        </div>
      </div>
    </div>
  </km-dialog>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useMainStore } from '@/pinia'
export default {
  setup() {
    const mainStore = useMainStore()
    return {
      value: ref(true),
      mainStore,
      m,
    }
  },
  computed: {
    errorMessage() {
      return this.mainStore.errorMessage ?? {}
    },
    technicalError() {
      return this.errorMessage?.technicalError ?? ''
    },
    text() {
      return this.errorMessage?.text ?? ''
    },
  },
  methods: {
    close() {
      this.value = false
      this.clearError()
    },
    clearError() {
      this.mainStore.setErrorMessage(undefined)
    },
  },
}
</script>
