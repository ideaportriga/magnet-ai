<template>
  <div class="kg-dialog-section" :style="sectionStyle" @focusin="onFocusIn" @focusout="onFocusOut">
    <div class="kg-dialog-section__inner" :style="innerSectionStyle">
      <!-- Header -->
      <div class="kg-dialog-section__header" :style="headerStyle">
        <div class="row q-gap-8 items-center">
          <q-icon v-if="icon" :name="icon" size="18px" :color="iconColor" />
          <span class="km-heading-8 text-weight-medium">{{ title }}</span>
          <slot name="title-badge" />
        </div>
        <slot name="header-actions" />
      </div>

      <!-- Description -->
      <div v-if="description" class="kg-dialog-section__description">
        {{ description }}
      </div>

      <!-- Content -->
      <div class="kg-dialog-section__content" :class="{ 'kg-dialog-section__content--disabled': disabled }">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { colors } from 'quasar'
import { computed, ref } from 'vue'

interface Props {
  title: string
  description?: string
  icon?: string
  iconColor?: string
  borderColor?: string
  backgroundColor?: string
  focusHighlight?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  icon: '',
  iconColor: 'primary',
  borderColor: '#e8e8e8',
  backgroundColor: '#fafafa',
  description: '',
  focusHighlight: false,
  disabled: false,
})

const { getPaletteColor } = colors

const isFocused = ref(false)

const onFocusIn = () => {
  if (props.focusHighlight) isFocused.value = true
}

const onFocusOut = () => {
  if (props.focusHighlight) isFocused.value = false
}

const sectionStyle = computed(() => ({
  background: props.backgroundColor,
  border: `1px solid ${props.borderColor}`,
}))

const innerSectionStyle = computed(() => ({
  borderColor: isFocused.value ? getPaletteColor(props.iconColor) : 'transparent',
}))

const headerStyle = computed(() => ({
  borderBottom: `1px solid ${props.borderColor}`,
}))
</script>

<style scoped>
.kg-dialog-section {
  border-radius: 8px;
}

.kg-dialog-section__inner {
  border-radius: 8px;
  position: relative;
  margin: -1px;
  border: 2px solid transparent;
  transition: border-color 0.36s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 16px;
}

.kg-dialog-section__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
}

.kg-dialog-section__description {
  font-size: 12px;
  color: var(--q-secondary-text);
  line-height: 1.4;
  margin-top: 4px;
  margin-bottom: 16px;
}

.kg-dialog-section__content--disabled {
  opacity: 0.5;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

/* Ensure form controls inside section have white background */
:deep(.km-control),
:deep(.km-select.km-open-popup) {
  background-color: white !important;
}

:deep(.km-input:not(.q-field--readonly).q-field--outlined.q-field--highlighted .q-field__control::before) {
  background-color: white !important;
}

:deep(.q-field--outlined .q-field__control:before) {
  border-color: var(--q-control-border) !important;
  transition: all 600ms;
}
</style>

