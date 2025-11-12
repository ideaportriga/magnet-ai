<template lang="pug">
q-timeline-entry(:key='step.started_at', :icon='step.icon', :color='isExpanded ? "status-ready-text" : "primary"')
  template(v-slot:subtitle)
    .row.items-center.justify-between(style='text-transform: none !important')
      .col.q-mr-md
        km-chip(
          iconColor='icon',
          hoverColor='primary',
          labelClass='km-heading-2',
          flat,
          dense,
          iconSize='16px',
          hoverBg='primary-bg',
          @click='step.type === "classification" || (step.type === "topic_completion" && !step?.details?.action_call_requests) ? null : toggleExpand()'
        )
          .row.items-center.justify-center.full-width
            q-icon(
              v-if='!(step.type === "classification" || (step.type === "topic_completion" && !step?.details?.action_call_requests))',
              name='fas fa-chevron-right',
              flat,
              :style='{ transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)", transition: "0.2s" }'
            )
            .q-ml-sm.text-secondary-text.cursor-pointer {{ step?.typeLabel }}

      .col-auto.q-mr-md.km-field {{ step?.duration_seconds }}
  .column.q-gap-8
    template(v-if='step.type === "classification"')
      .col
        .row
          .col-1.q-mr-md
            .km-field.text-secondary-text Intent
          .col
            km-chip(:label='step.details.intent', color='light')
      .col(v-if='step.details?.topic')
        .row
          .col-1.q-mr-md
            .km-field.text-secondary-text Topic
          .col
            km-chip(:label='step.details?.topic', color='light')
      .col
        .row
          .col-auto.q-mr-md
            .km-field.text-secondary-text Reason
          .col-auto
            | {{ step.details.reason }}
    template(v-else-if='step.type === "topic_completion"')
      .col
        .row
          .col-auto.q-mr-md
            .km-field.text-secondary-text Topic
          .col {{ step.details.topic.name }}
      .col
        .row
          .col-auto.q-mr-md
            .km-field.text-secondary-text Topic Description
          .col-auto {{ step.details.topic.description }}

        .q-mt-sm(v-if='step.details?.action_call_requests')
          .q-mt-sm(v-if='isExpanded && step.details?.action_call_requests')
            .text-secondary-text(v-for='rq in step.details?.action_call_requests')
              .row.q-mb-sm.items-center
                km-chip(:label='rq.action_type', color='light')
                .q-ml-sm {{ rq.function_name }}
              .km-field.text-secondary-text Request
              km-codemirror(:model-value='stringify(rq?.arguments)', readonly, style='min-height: 100px')

    template(v-else-if='step.type === "topic_action_call"')
      .q-mt-sm(v-if='step.details')
        .text-secondary-text
          .row.q-mb-sm.items-center
            km-chip(:label='step.details.request.action_type', color='light')
            .q-ml-sm {{ step.details.request.function_name }}
          .km-field.text-secondary-text(v-if='step.details?.request && !isExpanded') Request
            km-codemirror(:model-value='stringify(step.details.request.arguments)', readonly, style='min-height: 50px')
      div(v-if='step.details')
        q-slide-transition
          div(v-if='step.details?.request && isExpanded')
            .km-field.text-secondary-text Request
            km-codemirror(:model-value='stringify(step?.details?.request)', readonly, style='min-height: 100px')
            .km-field.text-secondary-text Response
            km-codemirror(:model-value='stringify(step?.details?.response)', readonly, style='min-height: 100px')

    teplate(v-else)
      km-codemirror(v-model='step.detailsJSON', style='max-height: 300px', readonly)
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    step: Object,
  },
  setup() {
    return {
      isExpanded: ref(false),
    }
  },
  methods: {
    stringify(obj) {
      return JSON.stringify(obj, null, 2)
    },
    toggleExpand() {
      this.isExpanded = !this.isExpanded
    },
  },
}
</script>
