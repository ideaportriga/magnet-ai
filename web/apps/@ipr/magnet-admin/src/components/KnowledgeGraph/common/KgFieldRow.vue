<template>
  <div class="kg-field-row-wrapper">
    <div v-if="label" class="kg-field-row-label">
      <span>{{ label }}</span>
      <span v-if="suffix" class="text-grey-6 text-weight-regular">{{ suffix }}</span>
      <q-icon v-if="hint" name="o_info" size="14px" color="grey-6" class="cursor-pointer">
        <q-tooltip self="top middle" :offset="[0, 8]">
          {{ hint }}
        </q-tooltip>
      </q-icon>
    </div>
    <div class="kg-field-row" :class="[`kg-field-row--cols-${validatedCols}`]" :style="{ gap: gap }">
      <slot />
    </div>
    <div v-if="error" class="kg-field-row-error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  cols?: number
  gap?: string
  label?: string
  suffix?: string
  hint?: string
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  cols: 1,
  gap: '24px',
  label: undefined,
  suffix: undefined,
  hint: undefined,
  error: undefined,
})

const validatedCols = computed(() => {
  const colsValue = props.cols ?? 1
  if (colsValue <= 0 || colsValue > 6) {
    console.error(`KgFieldRow: Invalid cols value "${colsValue}". Must be between 1 and 6. Using default value 1.`)
    return 1
  }
  return colsValue
})
</script>

<style scoped>
.kg-field-row-wrapper {
  display: flex;
  flex-direction: column;
}

.kg-field-row-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 10px;
  line-height: 1.4;
  letter-spacing: -0.01em;
}

.kg-field-row-label-hint-icon {
  opacity: 0.6;
  cursor: help;
  color: #6b7b8a;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
}

.kg-field-row-label-hint-icon:hover {
  opacity: 1;
  color: #4a5568;
}

.kg-field-row {
  display: grid;
  transition: opacity 0.2s ease;
}

.kg-field-row-error {
  font-size: 11px;
  color: var(--q-error-text);
  margin-top: 4px;
  padding: 4px 8px;
}

.kg-field-row--cols-1 {
  grid-template-columns: repeat(1, 1fr);
}

.kg-field-row--cols-2 {
  grid-template-columns: repeat(2, 1fr);
}

.kg-field-row--cols-3 {
  grid-template-columns: repeat(3, 1fr);
}

.kg-field-row--cols-4 {
  grid-template-columns: repeat(4, 1fr);
}

.kg-field-row--cols-5 {
  grid-template-columns: repeat(5, 1fr);
}

.kg-field-row--cols-6 {
  grid-template-columns: repeat(6, 1fr);
}

/* Column span utilities */
.kg-field-row :deep(.col-span-1) {
  grid-column: span 1;
}

.kg-field-row :deep(.col-span-2) {
  grid-column: span 2;
}

.kg-field-row :deep(.col-span-3) {
  grid-column: span 3;
}

.kg-field-row :deep(.col-span-4) {
  grid-column: span 4;
}

.kg-field-row :deep(.col-span-5) {
  grid-column: span 5;
}

.kg-field-row :deep(.col-span-6) {
  grid-column: span 6;
}

@media (max-width: 768px) {
  .kg-field-row--cols-1,
  .kg-field-row--cols-2,
  .kg-field-row--cols-3,
  .kg-field-row--cols-4,
  .kg-field-row--cols-5,
  .kg-field-row--cols-6 {
    grid-template-columns: 1fr;
  }
}
</style>
