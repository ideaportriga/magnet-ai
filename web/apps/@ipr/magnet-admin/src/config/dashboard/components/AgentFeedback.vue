<template>
  <div class="stack" data-gap="xs">
    <template v-if="like">
      <div class="flex-1">
        <km-chip class="block" :label="likesLabel" tone="success" round />
      </div>
    </template>
    <template v-if="dislike">
      <div class="flex-1">
        <km-chip class="block" :label="dislikesLabel" tone="danger" round />
      </div>
    </template>
  </div>
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
