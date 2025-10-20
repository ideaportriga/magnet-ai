<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(style='max-width: 1200px; margin: 0 auto')
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md.q-mt-lg
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            knowledge-providers-table
</template>
<script setup>
import { ref } from 'vue'

</script>