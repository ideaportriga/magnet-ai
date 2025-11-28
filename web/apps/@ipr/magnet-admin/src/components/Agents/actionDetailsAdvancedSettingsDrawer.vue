<template lang="pug">
div
  .km-button-text User Confirmation
  q-separator.q-mb-16
  .row.items-center.q-pb-xs
    .km-label.text-label Require confirmation
    km-toggle(v-model='requires_confirmation', label-class='text-label')
  .km-description.text-label Require user confirmation before executing this Action
  .col(v-if='requires_confirmation')
    .row.items-center.q-pl-8.q-gap-4.q-pb-xs.q-pt-lg
      .km-field.text-label Custom action description
    km-input(v-model='action_message_llm_description', border-radius='8px', height='36px', type='textarea', rows='3')
    .km-description.text-label.q-pl-8.q-pt-xs Instructions from this field will override global instructions for this Action.
    .row.items-center(@click='openGlobalInstructions = !openGlobalInstructions')
      km-btn.q-mt-8.q-mb-6(label='View global instructions', flat, simple, dropdown)
    km-input(
      :model-value='globalIntructions',
      border-radius='8px',
      height='36px',
      type='textarea',
      rows='3',
      readonly,
      v-if='openGlobalInstructions'
    )

  .km-button-text.q-mt-lg Other
    q-separator.q-mb-16
  .row.items-center.q-pb-xs
    .km-label.text-label Use response as assistant message
    km-toggle(v-model='use_response_as_assistant_message', label-class='text-label')
  .km-description.text-label Uses the action response as assistant message without additional topic processing step. Only applicable if the action is not called in parallel with other actions.
        
  //- .km-button-text.q-pt-md End user display options
  //- q-separator.q-mb-lg
  //- .row.items-center.q-pl-8.q-gap-4.q-pb-xs
  //-   .km-field.text-label End user name
  //-   q-icon.col-auto(name='o_info', color='secondary')
  //-     q-tooltip.bg-white.block-shadow.km-description(self='top middle', :offset='[-50, -50]')
  //-       .text-secondary-text This name will be displayed for the end user when the action is selected by an Agent. Keep it short and non-technical.
  //- km-input(v-model='display_name', border-radius='8px', height='36px', type='text')
</template>

<script>
import { ref } from 'vue'

export default {
  props: {
    action: {
      type: Object,
      required: true,
    },
  },
  setup() {
    const openGlobalInstructions = ref(false)
    const globalIntructions = ref(
      'A short natural-language action summary to show the user. It should clearly state what the action will do, including relevant argument values. Focus on action, not the result.'
    )
    return { openGlobalInstructions, globalIntructions }
  },
  computed: {
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    routeParams() {
      return this.$route.params
    },
    display_name: {
      get() {
        return this.action?.display_name
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
