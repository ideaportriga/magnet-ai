<template>
  <div>
    <div class="km-button-text">{{ m.agents_userConfirmation() }}</div>
    <km-separator class="mb-lg" />
    <div class="cluster pb-xs">
      <div class="km-label text-label">{{ m.agents_requireConfirmationLabel() }}</div>
      <km-toggle v-model="requires_confirmation" label-class="text-label" />
    </div>
    <div class="km-description text-label">{{ m.agents_requireConfirmationDesc() }}</div>
    <div v-if="requires_confirmation" class="flex-1">
      <div class="cluster pl-sm pb-xs pt-lg" data-gap="xs">
        <div class="km-field text-label">{{ m.agents_customActionDescription() }}</div>
      </div>
      <km-input v-model="action_message_llm_description" border-radius="8px" height="36px" type="textarea" rows="3" />
      <div class="km-description text-label pl-sm pt-xs">{{ m.agents_instructionsOverrideGlobal() }}</div>
      <div class="cluster" @click="openGlobalInstructions = !openGlobalInstructions">
        <km-btn class="mt-sm mb-sm" :label="m.agents_viewGlobalInstructions()" flat simple dropdown />
      </div>
      <km-input v-if="openGlobalInstructions" :model-value="globalIntructions" border-radius="8px" height="36px" type="textarea" rows="3" readonly />
    </div>
    <div class="km-button-text mt-lg">
      {{ m.agents_other() }}
      <km-separator class="mb-lg" />
    </div>
    <div class="cluster pb-xs">
      <div class="km-label text-label">{{ m.agents_useResponseAsAssistantMessage() }}</div>
      <km-toggle v-model="use_response_as_assistant_message" label-class="text-label" />
    </div>
    <div class="km-description text-label">{{ m.agents_useResponseAsAssistantMessageDesc() }}</div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  props: {
    action: {
      type: Object,
      required: true,
    },
  },
  setup() {
    const { activeVariant, updateNestedListItemBySystemName } = useAgentEntityDetail()
    const openGlobalInstructions = ref(false)
    const globalIntructions = ref(
      'A short natural-language action summary to show the user. It should clearly state what the action will do, including relevant argument values. Focus on action, not the result.'
    )
    return { m, activeVariant, updateNestedListItemBySystemName, openGlobalInstructions, globalIntructions }
  },
  computed: {
    topic() {
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    routeParams() {
      return this.$route.params
    },
    display_name: {
      get() {
        return this.action?.display_name
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            display_name: value,
          },
        })
      },
    },
    requires_confirmation: {
      get() {
        return this.action?.requires_confirmation
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            requires_confirmation: value,
          },
        })
      },
    },
    use_response_as_assistant_message: {
      get() {
        return this.action?.use_response_as_assistant_message
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            use_response_as_assistant_message: value,
          },
        })
      },
    },
    action_message_llm_description: {
      get() {
        return this.action?.action_message_llm_description
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.action?.system_name,
          data: {
            action_message_llm_description: value,
          },
        })
      },
    },
  },
}
</script>
