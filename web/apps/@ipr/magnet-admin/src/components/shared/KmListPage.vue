<template>
  <div class="stack full-height" data-gap="0">
    <div class="collection-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
      <slot name="tabs" />
      <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack min-h-0" data-gap="0">
        <div v-if="$slots.toolbar" class="cluster mb-md">
          <slot name="toolbar" />
        </div>
        <div class="flex-1 min-h-0">
          <slot />
        </div>
      </div>
    </div>
    <slot name="overlays" />
  </div>
</template>
