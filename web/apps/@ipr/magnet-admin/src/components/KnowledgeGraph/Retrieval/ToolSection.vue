<template>
  <q-card flat bordered class="tool-card cursor-pointer" :class="[variantClass, { 'tool-disabled': disabled }]" @click="$emit('click')">
    <q-card-section class="q-pa-sm q-pl-12 q-pr-md">
      <div class="row items-start q-gutter-x-sm">
        <!-- Icon -->
        <div class="column justify-center" style="height: 42px">
          <q-avatar :icon="icon" :color="iconColor" :text-color="iconTextColor" size="32px" font-size="18px" />
        </div>

        <!-- Content -->
        <div class="col">
          <div class="row items-center q-gutter-x-sm">
            <div class="km-heading-8 text-weight-medium">{{ label }}</div>
            <q-badge v-if="badge" :color="badgeColor" :text-color="badgeTextColor" :label="badge" class="text-weight-medium" />
          </div>
          <div class="q-mt-2 text-secondary-text" style="font-size: 0.8rem">{{ description || 'No description configured' }}</div>

          <!-- Stats Slot -->
          <div v-if="$slots.stats" class="row q-gutter-x-md q-mt-xs">
            <slot name="stats" />
          </div>
        </div>

        <!-- Toggle (optional) -->
        <div v-if="showToggle" class="col-auto self-center">
          <q-toggle :model-value="enabled" dense :disable="toggleDisabled" @click.stop @update:model-value="$emit('update:enabled', $event)" />
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface ToolCardProps {
  icon: string
  iconColor: string
  iconTextColor: string
  label: string
  description?: string
  variant: 'search' | 'exit'
  badge?: string
  badgeColor?: string
  badgeTextColor?: string
  showToggle?: boolean
  enabled?: boolean
  toggleDisabled?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<ToolCardProps>(), {
  description: '',
  badge: '',
  badgeColor: 'orange-1',
  badgeTextColor: 'orange-9',
  showToggle: false,
  enabled: false,
  toggleDisabled: false,
  disabled: false,
})

defineEmits<{
  (e: 'click'): void
  (e: 'update:enabled', value: boolean): void
}>()

const variantClass = computed(() => `tool-card--${props.variant}`)
</script>

<style scoped>
.tool-card {
  border-radius: 6px;
  transition: all 0.2s ease;
}

/* Search Tool Cards (Filter & Retrieval) */
.tool-card--search {
  border-color: #c5cae9;
  background: linear-gradient(135deg, #f5f7ff 0%, #ffffff 100%);
}

.tool-card--search:hover {
  border-color: var(--q-primary);
}

.tool-card--search.tool-disabled {
  background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
  border-color: #e0e0e0;
}

.tool-card--search.tool-disabled:hover {
  border-color: #bdbdbd;
}

/* Exit Tool Cards */
.tool-card--exit {
  border-color: #ffccbc;
  background: linear-gradient(135deg, #fff8f5 0%, #ffffff 100%);
}

.tool-card--exit:hover {
  border-color: #ff7043;
}

/* Disabled state for all variants */
.tool-disabled {
  opacity: 0.5;
  pointer-events: auto;
}

.tool-disabled :deep(.q-avatar) {
  filter: grayscale(50%);
}
</style>
