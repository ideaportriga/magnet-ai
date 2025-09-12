<template lang="pug">
  div
    km-section(
      title='Conversation closure interval',
      subTitle='Interval after which inactive conversations will be marked as closed'
    )
      q-btn-toggle(
        v-model='conversationClosureInterval',
        toggle-color='primary-light',
        :options='intervals',
        dense,
        text-color='text-weak',
        toggle-text-color='primary'
      )
    q-separator.q-my-lg
    km-section(
      title="Post-processing",
      subTitle="Turn on post-processing for advanced Agent analysis and monitoring"
    )
      q-toggle(
        v-model="postProcessing",
        color="primary",
      )
    q-separator.q-my-lg
    km-section(
      title='Post-processing Prompt Template',
      subTitle='Prompt Template that controls the post-processing of Agent, including summary, language detection and case resolution check'
    )
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
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
            :label='postProcessTemplate ? "Open Prompt Template" : "Open Prompt Templates Library"',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='postProcessTemplate ? navigate(`prompt-templates/${postProcessTemplateId}`) : navigate("prompt-templates")'
          )
    q-separator.q-my-lg
    km-section(
      title='Message post-processing',
      subTitle='Turn on post-processing on message level'
    )
      .column
          .col.q-mb-md
            q-chip.km-small-chip(color='primary-light', text-color='primary', label='Upcoming feature')
          .col
            q-toggle(:model-value='false', disable, dense)
  
  </template>
  
  <script>
  import { useChroma } from '@shared'
  import { onMounted } from 'vue'
  
  const intervals = [
    { label: '1 day', value: '1D' },
    { label: '3 day', value: '3D' },
    { label: '1 week', value: '7D' },
  ]
  
  export default {
    setup() {
      const { items: promptTemplateItems } = useChroma('promptTemplates')
      const { getPaginated } = useChroma('jobs')

      onMounted(() => {
        console.log('mounted 123')
        getPaginated({
          page: 1,
          limit: 1,
          filter: {
            'definition.run_configuration': { $eq: 'post_processing_conversations' },
            'definition.run_configuration.params.is_system': { $eq: true },
          },
        })
      })

      return {
        promptTemplateItems,
        intervals,
        getPaginated
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
          return this.$store.getters.agentDetailVariant?.value.post_processing?.template
        },
        set(value) {
          this.$store.dispatch(
            'updateNestedAgentDetailProperty',
            { path: 'post_processing.template', value }
          )
        },
      },
      postProcessing: {
        get() {
          return this.$store.getters.agentDetailVariant?.value?.post_processing?.enabled || false
        },
        set(value) {
          this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'post_processing.enabled', value })
        },
      },
      conversationClosureInterval: {
        get() {
          return this.$store.getters.agentDetailVariant?.value?.settings?.conversation_closure_interval || '1D'
        },
        set(value) {
          this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.conversation_closure_interval', value })
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