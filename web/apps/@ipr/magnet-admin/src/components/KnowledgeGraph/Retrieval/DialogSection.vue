<template>
  <div class="dialog-section" :style="sectionStyle" @focusin="onFocusIn" @focusout="onFocusOut">
    <div class="inner-dialog-section" :style="innerSectionStyle">
      <div class="row q-gap-8 items-center q-pb-8" :style="headerStyle">
        <q-icon v-if="icon" :name="icon" size="18px" :color="color" />
        <span class="km-heading-8 text-weight-medium">{{ title }}</span>
        <slot name="title-badge" />
        <q-space />
        <slot name="header-actions" />
      </div>
      <div v-if="description" class="km-description text-secondary-text q-mt-xs q-mb-md">
        {{ description }}
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { colors } from 'quasar'

interface Props {
  title: string
  description?: string
  icon?: string
  color?: string
  borderColor?: string
  backgroundColor?: string
  focusHighlight?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  icon: '',
  color: 'primary',
  borderColor: '#e8e8e8',
  backgroundColor: '#fafafa',
  description: '',
  focusHighlight: false,
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
  borderColor: isFocused.value ? getPaletteColor(props.color) : 'transparent',
}))

const headerStyle = computed(() => ({
  borderBottom: `1px solid ${props.borderColor}`,
}))
</script>

<style scoped>
.dialog-section {
  border-radius: 8px;
}

.inner-dialog-section {
  border-radius: 8px;
  position: relative;
  margin: -1px -1px;
  border: 2px solid transparent;
  transition: border-color 0.36s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 16px;
}

:deep(.km-control), :deep(.km-select.km-open-popup) {
  background-color: white !important;
}
</style>
