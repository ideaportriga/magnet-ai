<template>
  <div>
    <template v-if="isAnswered">
      <div class="flex-1">
        <km-chip class="my-xs" :label="row?.extra_data?.is_answered ? &quot;Yes&quot; : &quot;No&quot;" :tone="row?.extra_data?.is_answered ? &quot;success&quot; : &quot;danger&quot;" />
        <div class="km-field">{{ reason }}</div>
      </div>
    </template>
    <template v-else>
      <div class="km-title text-text-weak">-</div>
    </template>
  </div>
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
