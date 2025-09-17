<template lang="pug">
q-icon(v-if='row?.[name]', name='fas fa-check')
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row', 'name'],
})
</script>
