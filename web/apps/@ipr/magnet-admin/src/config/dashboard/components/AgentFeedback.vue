<template lang="pug">
.column.q-gap-4
  template(v-if='like')
    .col
      km-chip.text-like-text.block(:label='likesLabel', color='like-bg', round)
  template(v-if='dislike')
    .col
      km-chip.text-error-text.block(:label='dislikesLabel', color='error-bg', round)
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    like() {
      return this.row.conversation_data?.likes ?? 0
    },
    dislike() {
      return this.row.conversation_data?.dislikes ?? 0
    },
    likesLabel() {
      if (!this.like) return '-'
      if (this.like == 1) return `1 Like`
      return `${this.like} Likes`
    },
    dislikesLabel() {
      if (!this.dislike) return '-'
      if (this.dislike == 1) return `1 Dislike`
      return `${this.dislike} Dislikes`
    },
  },
}
</script>
