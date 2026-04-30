<template>
  <div class="cluster overflow-hidden full-height details-layout" data-wrap="no">
    <div class="flex-1 no-wrap full-height fit px-md pt-sm pb-lg km-flex-min-0" :style="contentContainerStyle">
      <!-- Outer .flex-1 fills 100% of the space between the sidebar and the
           drawer; the inner .details-layout__content stack carries the
           max-width so the actual entity card sits centered between them. -->
      <div class="stack full-height km-flex-min-0 mx-auto details-layout__content" data-gap="0">
        <slot name="breadcrumbs">
          <div />
        </slot>
        <div v-if="!noHeader" class="full-width mb-sm bg-white border-radius-8 py-md px-lg">
          <div v-if="$slots.header" class="cluster full-width" data-wrap="no">
            <div class="flex-1 km-flex-min-w-0">
              <slot name="header" />
            </div>
            <div v-if="$slots[&quot;header-actions&quot;]" class="flex-none cluster ml-md" data-align="start" data-wrap="no" data-gap="sm">
              <slot name="header-actions" />
            </div>
          </div>
          <layouts-details-header v-else :name="name" :description="description" :system-name="systemName" :system-name-rules="systemNameRules" :info-text="infoText" :show-description="showDescription" :show-record-info="showRecordInfo" :created-at="createdAt" :updated-at="updatedAt" :created-by="createdBy" :updated-by="updatedBy" :updated-label="updatedLabel" @update:name="(value) =&gt; $emit(&quot;update:name&quot;, value)" @update:description="(value) =&gt; $emit(&quot;update:description&quot;, value)" @update:system-name="(value) =&gt; $emit(&quot;update:systemName&quot;, value)">
            <template v-if="$slots[&quot;header-actions&quot;]" #actions>
              <slot name="header-actions" />
            </template>
          </layouts-details-header>
          <slot v-if="$slots.subheader || variants?.length &gt; 0" name="subheader">
            <layouts-details-sub-header :variants="variants" :selected-variant="selectedVariant" :active-variant="activeVariant" @activate-variant="emit(&quot;activateVariant&quot;)" @add-variant="emit(&quot;addVariant&quot;)" @delete-variant="emit(&quot;deleteVariant&quot;)" @select-variant="emit(&quot;selectVariant&quot;, $event)" @update-variant-property="emit(&quot;updateVariantProperty&quot;, $event)" />
          </slot>
        </div>
        <div class="flex-1 overflow-hidden no-wrap stack km-flex-min-0" data-gap="0" :class="noContentWrapper ? '' : 'ba-border bg-white border-radius-8 p-lg'">
          <slot name="content">
            <div>Content</div>
          </slot>
        </div>
      </div>
    </div>
    <div class="flex-none full-height">
      <slot name="drawer" />
    </div>
  </div>
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
  systemNameRules: {
    type: Array,
    default: () => [],
  },
  showDescription: {
    type: Boolean,
    default: true,
  },
  showRecordInfo: {
    type: Boolean,
    default: false,
  },
  createdAt: {
    type: [String, Number, Date],
    default: '',
  },
  updatedAt: {
    type: [String, Number, Date],
    default: '',
  },
  createdBy: {
    type: String,
    default: '',
  },
  updatedBy: {
    type: String,
    default: '',
  },
  updatedLabel: {
    type: String,
    default: '',
  },
  noHeader: {
    type: Boolean,
    default: false,
  },
  noContentWrapper: {
    type: Boolean,
    default: false,
  },
  variants: {
    type: Array,
    default: () => [],
  },
  selectedVariant: {
    type: [String, Object],
    default: '',
  },
  activeVariant: {
    type: String,
    default: '',
  },
  contentContainerStyle: {
    type: Object,
    default: () => ({}),
  },
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

<style>
.details-layout__content {
  inline-size: 100%;
  max-inline-size: 1200px;
}
</style>
