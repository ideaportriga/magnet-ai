<template>
  <div class="row items-center q-mb-12 q-gutter-xs">
    <slot name="leading" />

    <div v-if="$slots.status" class="row items-center no-wrap q-ml-md q-gutter-x-sm">
      <slot name="status" />
    </div>

    <q-space />

    <slot name="trailing" />
  </div>
</template>
