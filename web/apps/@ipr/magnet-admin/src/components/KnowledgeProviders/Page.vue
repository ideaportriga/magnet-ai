<template>
  <div class="stack full-height" data-gap="0">
    <div class="collection-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
      <template v-if="loading">
        <div class="flex flex-center full-height">
          <km-loader size="40px" />
        </div>
      </template>
      <template v-else>
        <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack" data-gap="0" style="min-block-size: 0">
          <knowledge-providers-table />
        </div>
      </template>
    </div>
  </div>
</template>
<script setup>
import { m } from '@/paraglide/messages'
import { ref } from 'vue'
const loading = ref(false)
</script>
