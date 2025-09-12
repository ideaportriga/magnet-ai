<template lang="pug">
.bg-light-grey.q-px-xl.q-py-lg.ba-border.border-radius-12(style='max-width: 400px')
  .row.justify-center.q-mb-md
    q-icon.gradient(:name='icon', style='', size='2rem') 
  .row.justify-center.km-heading-7.q-mb-md {{ label }}
  .row.justify-center.km-label.q-mb-md.text-center {{ description }}
  .row.justify-center
    km-btn(:label='actionLabel', @click='$emit("click")' :data-test='actionLabel')
</template>

<script>
export default {
  name: 'EmptyState',
  props: {
    icon: {
      type: String,
      default: 'fas fa-wand-magic-sparkles',
    },
    label: {
      type: String,
      default: 'This AI App has no AI Tabs yet',
    },
    description: {
      type: String,
      default: 'Add AI Tabs to connect your AI tools.',
    },
    actionLabel: {
      type: String,
      default: 'New AI Tab',
    },
  },
}
</script>

<style lang="stylus">
.gradient {
  background: linear-gradient(121.5deg, #6840C2 9.69%, #E30052 101.29%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
