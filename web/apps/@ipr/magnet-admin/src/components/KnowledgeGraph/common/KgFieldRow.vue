<template>
  <div class="kg-field-row" :class="[`kg-field-row--cols-${cols}`, { 'kg-field-row--disabled': disabled }]">
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  cols?: 2 | 3 | 4
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  cols: 2,
  disabled: false,
})
</script>

<style scoped>
.kg-field-row {
  display: grid;
  gap: 24px;
  transition: opacity 0.2s ease;
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

.kg-field-row--disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* Column span utilities */
.kg-field-row :deep(.col-span-2) {
  grid-column: span 2;
}

.kg-field-row :deep(.col-span-3) {
  grid-column: span 3;
}

.kg-field-row :deep(.col-span-4) {
  grid-column: span 4;
}

@media (max-width: 768px) {
  .kg-field-row--cols-2,
  .kg-field-row--cols-3,
  .kg-field-row--cols-4 {
    grid-template-columns: 1fr;
  }
}
</style>
