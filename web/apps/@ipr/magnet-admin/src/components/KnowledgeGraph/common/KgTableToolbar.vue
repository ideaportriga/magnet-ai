<template>
  <div class="cluster mb-md" data-gap="xs">
    <slot name="leading" />

    <div v-if="$slots.status" class="cluster ml-md gap-x-sm" data-wrap="no">
      <slot name="status" />
    </div>

    <div class="km-space" />

    <slot name="trailing" />
  </div>
</template>
