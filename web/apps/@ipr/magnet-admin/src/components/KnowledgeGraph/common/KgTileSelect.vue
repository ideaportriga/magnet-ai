<template>
  <div class="kg-tile-grid" :style="{ '--kg-cols': props.cols }">
    <div v-for="option in options" :key="option.value">
      <km-card
        flat
        bordered
        class="kg-tile-select cursor-pointer full-height"
        :class="{ 'kg-tile-select--selected': modelValue === option.value }"
        tabindex="0"
        role="radio"
        :aria-checked="modelValue === option.value"
        @click="$emit('update:modelValue', option.value)"
        @keydown.enter.prevent="$emit('update:modelValue', option.value)"
        @keydown.space.prevent="$emit('update:modelValue', option.value)"
      >
        <div class="km-card-section p-md">
          <div class="cluster mb-sm gap-x-sm">
            <km-glyph v-if="option.icon" :name="option.icon" :tone="modelValue === option.value ? 'brand' : undefined" size="20px" />
            <div class="text-weight-medium" :class="modelValue === option.value ? 'text-primary' : ''">
              {{ option.label }}
            </div>
          </div>
          <div class="text-caption text-secondary-text" :class="{ 'kg-tile-select__description--with-icon': option.icon }">
            {{ option.description }}
          </div>
        </div>
      </km-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
export interface TileOption {
  value: string
  label: string
  icon?: string
  description: string
}

const props = withDefaults(
  defineProps<{
    modelValue: string
    options: TileOption[]
    cols?: 2 | 3 | 4
  }>(),
  {
    cols: 3,
  }
)

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>

<style scoped>
.kg-tile-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (min-width: 1024px) {
  .kg-tile-grid {
    grid-template-columns: repeat(var(--kg-cols), 1fr);
  }
}

.kg-tile-select {
  transition: var(--ds-transition-colors);
  border-color: var(--ds-color-border);
}

.kg-tile-select:hover,
.kg-tile-select--selected {
  color: var(--ds-color-primary);
  border-color: var(--ds-color-primary);
  background-color: var(--ds-color-primary-transparent);
}

.kg-tile-select:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

.kg-tile-select__description--with-icon {
  padding-inline-start: 28px;
}
</style>
