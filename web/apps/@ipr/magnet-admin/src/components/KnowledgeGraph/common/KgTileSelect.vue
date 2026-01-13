<template>
  <div class="kg-tile-grid" :style="{ '--kg-cols': props.cols }">
    <div v-for="option in options" :key="option.value">
      <q-card
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
        <q-card-section class="q-pa-md">
          <div class="row items-center q-gutter-x-sm q-mb-sm">
            <q-icon v-if="option.icon" :name="option.icon" :color="modelValue === option.value ? 'primary' : ''" size="20px" />
            <div class="text-weight-medium" :class="modelValue === option.value ? 'text-primary' : ''">
              {{ option.label }}
            </div>
          </div>
          <div class="text-caption text-secondary-text" :class="{ 'kg-tile-select__description--with-icon': option.icon }">
            {{ option.description }}
          </div>
        </q-card-section>
      </q-card>
    </div>
  </div>
</template>

<script setup lang="ts">
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
  transition: all 0.2s ease;
  border-color: #e0e0e0;
}

.kg-tile-select:hover,
.kg-tile-select--selected {
  color: var(--q-primary);
  border-color: var(--q-primary);
  background-color: color-mix(in srgb, var(--q-primary) 10%, white);
}

.kg-tile-select:hover :deep(.q-icon) {
  color: var(--q-primary);
}

.kg-tile-select:focus-visible {
  outline: 2px solid var(--q-primary);
  outline-offset: 2px;
}

.kg-tile-select__description--with-icon {
  padding-left: 28px;
}
</style>
