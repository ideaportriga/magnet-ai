<template>
  <div class="stack" data-gap="0">
    <div v-if="prompt" class="cluster" data-gap="sm">
      <div class="km-paragraph">{{ prompt.display_name }}</div>
      <km-chip class="text-secondary-text" :label="variant" tone="neutral" round />
    </div>
    <div v-else class="cluster" data-gap="sm">
      <div class="km-paragraph">-</div>
    </div>
  </div>
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    prompt() {
      return this.row.prompt_template
    },
    variant() {
      if (!this.prompt) return ''
      return this.prompt.variant?.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
    },
  },
}
</script>
