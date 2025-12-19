<template>
  <div
    class="kg-toggle-field"
    :class="{
      'kg-toggle-field--active': modelValue,
      'kg-toggle-field--disabled': disabled,
    }"
    @click="toggle"
  >
    <div class="full-width row items-center no-wrap">
      <div class="col">
        <div class="kg-toggle-field__title">{{ title }}</div>
        <div v-if="description" class="kg-toggle-field__description">{{ description }}</div>
      </div>
      <q-toggle
        :model-value="modelValue"
        :disable="disabled"
        dense
        color="primary"
        class="q-ml-6"
        @update:model-value="$emit('update:modelValue', $event)"
        @click.stop
      />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  title: string
  description?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const toggle = () => {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}
</script>

<style scoped>
.kg-toggle-field {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border: 1px solid var(--q-control-border);
  border-radius: 4px;
  cursor: pointer;
  transition:
    background 0.3s ease,
    border-color 0.3s ease;
}

.kg-toggle-field:hover:not(.kg-toggle-field--disabled) {
  border-color: var(--q-control-hover-border);
  background: #fafafa;
}

.kg-toggle-field--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.kg-toggle-field__title {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  line-height: 1.3;
}

.kg-toggle-field__description {
  font-size: 12px;
  color: #757575;
  line-height: 1.4;
  margin-top: 2px;
}
</style>
