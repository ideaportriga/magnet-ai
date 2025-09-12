<template lang="pug">
template(v-if='isAnswered')
  .col
    km-chip.q-my-4(
      :label='row?.extra_data?.is_answered ? "Yes" : "No"',
      :color='row?.extra_data?.is_answered ? "like-bg" : "error-bg"',
      :class='row?.extra_data?.is_answered ? "text-like-text" : "text-error-text"'
    )
    .km-field {{ reason }}
template(v-else)
  .km-title.text-text-weak -
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    isAnswered() {
      return typeof this.row?.extra_data?.is_answered === 'boolean'
    },
    reason() {
      if (this.isAnswered && this.row?.extra_data?.is_answered) return ''
      if (this.row?.extra_data?.resolution === 'question_not_answered') {
        return 'Non-relevant content'
      }
      if (this.row?.extra_data?.resolution === 'no_results') {
        return 'No content retrieved'
      }
      return ''
    },
  },
}
</script>
