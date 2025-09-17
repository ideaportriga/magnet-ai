<template lang="pug">
.row.no-wrap.overflow-hidden.full-height.details-layout
  .col.no-wrap.full-height.justify-center.fit.q-px-md.no-wrap.q-py-lg(:style='contentContainerStyle')
    .column.full-height.no-wrap
      slot(name='breadcrumbs')
        div
      .items-center.q-gap-12.no-wrap.full-width.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16(v-if='!noHeader')
        slot(name='header')
          layouts-details-header(
            :name='name',
            @update:name='(value) => $emit("update:name", value)',
            :description='description',
            @update:description='(value) => $emit("update:description", value)',
            :systemName='systemName',
            @update:systemName='(value) => $emit("update:systemName", value)',
            :infoText='infoText'
          )
        slot(name='subheader', v-if='variants?.length > 0')
          layouts-details-sub-header(
            :variants='variants',
            :selectedVariant='selectedVariant',
            :activeVariant='activeVariant',
            @activateVariant='emit("activateVariant")',
            @addVariant='emit("addVariant")',
            @deleteVariant='emit("deleteVariant")',
            @selectVariant='emit("selectVariant", $event)',
            @updateVariantProperty='emit("updateVariantProperty", $event)'
          )
      .ba-border.bg-white.border-radius-8.q-pa-16.overflow-hidden.no-wrap.column
        slot(name='content')
          div Content
  .col-auto
    slot(name='drawer')
</template>

<script setup>
/* eslint-disable */
const props = defineProps({
  name: {
    type: String,
  },
  description: {
    type: String,
  },
  systemName: {
    type: String,
  },
  infoText: {
    type: String,
    default: 'It is highly recommended to fill in system name only once and not change it later.',
  },
  noHeader: {
    type: Boolean,
    default: false,
  },
  variants: {
    type: Array,
    default: () => [],
  },
  selectedVariant: {
    type: Object,
    default: () => {},
  },
  activeVariant: {
    type: String,
    default: '',
  },
  contentContainerStyle: {},
})
const emit = defineEmits([
  'update:name',
  'update:description',
  'update:systemName',
  'activateVariant',
  'addVariant',
  'deleteVariant',
  'selectVariant',
  'updateVariantProperty',
])
</script>
