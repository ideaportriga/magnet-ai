<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    template(v-if='loading')
      .flex.flex-center.full-height
        q-spinner(size='40px', color='primary')
    template(v-else)
      .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
        knowledge-providers-table
</template>
<script setup>
import { m } from '@/paraglide/messages'
import { ref } from 'vue'
const loading = ref(false)
</script>
