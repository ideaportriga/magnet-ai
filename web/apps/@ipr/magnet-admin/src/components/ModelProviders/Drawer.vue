<template>
  <km-drawer-layout storage-key="drawer-model-providers" no-scroll>
    <template #tabs>
      <div class="cluster full-width px-lg" data-wrap="no">
        <km-tabs v-model="tab" class="full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
          <template v-for="t in tabs" :key="t">
            <km-tab :name="t.name" :label="t.label" />
          </template>
          <div class="fit" />
        </km-tabs>
      </div>
    </template>
    <div v-if="tab == 'parameters'" class="stack fit" data-gap="lg">
      <div class="km-title">General settings</div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_providerName() }}</div>
        <km-input :model-value="provider?.name" @update:model-value="updateProviderProperty(&quot;name&quot;, $event)" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_displayName() }}</div>
        <km-input :model-value="provider?.name" @update:model-value="updateProviderProperty(&quot;name&quot;, $event)" />
      </div>
      <div>
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_description() }}</div>
        <km-input :model-value="provider?.description" @update:model-value="updateProviderProperty(&quot;description&quot;, $event)" />
      </div>
      <div>
        <km-checkbox :label="m.common_default()" :model-value="false" disabled />
      </div>
      <km-separator />
      <div class="km-title">Capabilities</div>
      <km-checkbox :label="m.common_jsonMode()" :model-value="false" disabled />
      <km-checkbox :label="m.common_jsonSchema()" :model-value="false" disabled />
      <km-checkbox :label="m.common_toolCalling()" :model-value="false" disabled />
      <km-checkbox :label="m.common_reasoning()" :model-value="false" disabled />
    </div>
    <div v-if="tab == 'pricing'" class="stack fit" data-gap="lg">
      <div class="km-title">Pricing</div>
    </div>
  </km-drawer-layout>
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'

export default {
  setup() {
    const { draft, updateField } = useEntityDetail('provider')
    return {
      m,
      draft,
      updateField,
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'pricing', label: 'Pricing' },
      ]),
    }
  },
  computed: {
    provider() {
      return this.draft
    },
  },
  methods: {
    updateProviderProperty(key, value) {
      this.updateField(key, value)
    },
  },
}
</script>
