<template lang="pug">
template(v-if='row?.extra_data?.answer_feedback?.type')
  km-chip(:label='title', :color='color', :class='class')
template(v-else)
  .km-title.text-text-weak -
  //km-chip.text-text-grey(label='N/A', color='in-progress')
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    title() {
      return this.row?.extra_data?.answer_feedback?.type === 'like' ? 'Like' : 'Dislike'
    },
    color() {
      return this.row?.extra_data?.answer_feedback?.type === 'like' ? 'like-bg' : 'error-bg'
    },
    class() {
      return this.row?.extra_data?.answer_feedback?.type === 'like' ? 'text-like-text' : 'text-error-text'
    },
  },
}
</script>
