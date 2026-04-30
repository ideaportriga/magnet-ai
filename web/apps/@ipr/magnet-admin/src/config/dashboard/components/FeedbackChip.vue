<template>
  <div>
    <template v-if="row?.extra_data?.answer_feedback?.type">
      <km-chip :label="title" :tone="tone" />
    </template>
    <template v-else>
      <div class="km-title text-text-weak">-</div>
      <!--km-chip.text-text-grey(label='N/A', color='in-progress')-->
    </template>
  </div>
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    title() {
      return this.row?.extra_data?.answer_feedback?.type === 'like' ? 'Like' : 'Dislike'
    },
    tone() {
      return this.row?.extra_data?.answer_feedback?.type === 'like' ? 'success' : 'danger'
    },
  },
}
</script>
