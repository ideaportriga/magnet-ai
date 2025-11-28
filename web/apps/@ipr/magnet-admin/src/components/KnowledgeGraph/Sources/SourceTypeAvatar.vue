<template>
  <q-card class="source-type-card cursor-pointer" flat bordered clickable @click="emit('select')">
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
}>()

const emit = defineEmits<{
  (e: 'select'): void
}>()
</script>

<style scoped>
.source-type-card {
  width: 140px;
  height: 140px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  border: 1px solid #e0e0e0;

  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    background-color: #fafafa;
    border-color: #bdbdbd;
    transform: translateY(-4px);
  }

  &:active {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.border-radius-12 {
  border-radius: 12px;
}
</style>
