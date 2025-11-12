<template lang="pug">
q-stepper.full-width(:model-value='stepper', :vertical='vertical', flat, alternative-labels)
  q-step(v-for='(step, index) in steps', :key='index', :name='index', :title='step.description', :icon='getIcon(index)', :done='index < stepper')
</template>
<script>
export default {
  props: {
    vertical: {
      type: Boolean,
      default: false,
    },
    steps: {
      type: Array,
      required: true,
    },
    stepper: {
      type: Number,
      default: 0,
    },
  },
  methods: {
    getIcon(index) {
      if (index === this.stepper) return 'pen'
      if (index < this.stepper) return 'check'
      return 'circle'
    },
  },
}
</script>
