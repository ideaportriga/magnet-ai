<template>
  <km-btn-dropdown class="km-export-dropdown" flat tone="subtle" :label="m.common_export()" no-caps icon="export">
    <ul class="km-list">
      <li class="km-item" clickable @click="$emit(&quot;exportToCsv&quot;)">
        <div class="km-item-section">
          <span class="km-item-label">Export as CSV</span>
        </div>
      </li>
      <li class="km-item" clickable @click="$emit(&quot;exportToJson&quot;)">
        <div class="km-item-section">
          <span class="km-item-label">Export as JSON</span>
        </div>
      </li>
    </ul>
  </km-btn-dropdown>
</template>
<script>
import { m } from '@/paraglide/messages'
export default {
  emits: ['exportToCsv', 'exportToJson'],
  setup() {
    return { m }
  },
}
</script>
<style>
.km-export-dropdown .fa-file-export {
  font-size: var(--ds-font-size-body-lg) !important;
  color: var(--ds-color-btn-flat-icon);
}
</style>
