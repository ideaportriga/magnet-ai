<template>
  <q-card
    class="source-type-card"
    :class="{ 'cursor-pointer': !disabled, 'source-type-card--disabled': disabled }"
    flat
    bordered
    clickable
    @click="!disabled && emit('select')"
  >
    <q-badge v-if="comingSoon" color="orange-1" text-color="orange-9" label="Coming Soon" class="coming-soon-badge text-weight-medium" />
    <q-card-section class="column items-center justify-center">
      <q-avatar :color="backgroundColor" square size="72px" class="border-radius-12">
        <q-img v-if="image" :src="image" width="48px" height="48px" no-spinner no-transition />
        <q-icon v-else-if="icon" :name="icon" :color="iconColor" size="48px" />
      </q-avatar>
      <div class="text-weight-medium q-mt-sm">{{ name }}</div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
defineProps<{
  name: string
  image?: string
  icon?: string
  iconColor?: string
  backgroundColor: string
  disabled?: boolean
  comingSoon?: boolean
}>()

const emit = defineEmits<{
  (e: 'select'): void
}>()
</script>

<style scoped>
.source-type-card {
  position: relative;
  width: 130px;
  height: 130px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  border: 1px solid #e0e0e0;

  &:hover:not(.source-type-card--disabled) {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    background-color: #fafafa;
    border-color: #bdbdbd;
    transform: translateY(-4px);
  }

  &:active:not(.source-type-card--disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.source-type-card--disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.coming-soon-badge {
  position: absolute;
  top: -7px;
  right: 20px;
  font-size: 12px;
  z-index: 1;
}

.border-radius-12 {
  border-radius: 12px;
}
</style>
