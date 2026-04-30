<template>
  <div>
    <km-section :title="m.section_changeTheme()" :sub-title="m.subtitle_changeAppearance()">
      <div style="inline-size: 220px">
        <km-select v-model="theme" :options="themeOptions" size="sm" :disable="false" />
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_showCloseButton()" :sub-title="m.subtitle_controlCloseButton()">
      <km-toggle v-model="show_close_button" size="sm" :disable="false" />
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_showLogo()" :sub-title="m.subtitle_showLogo()">
      <km-toggle v-model="isIconHide" size="sm" :disable="false" />
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_aiAppUrl()" :sub-title="m.subtitle_aiAppUrl()">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.section_aiAppUrl() }}</div>
      <div class="cluster">
        <div class="flex-1 mr-sm">
          <km-input ref="input" border-radius="8px" height="36px" :readonly="true" :model-value="appUrl" />
        </div>
        <div class="flex-none">
          <km-btn icon="copy" icon-size="16px" size="sm" flat :tooltip="m.common_copy()" @click="copy" />
        </div>
      </div>
    </km-section>
  </div>
</template>

<script>
import { copyToClipboard } from '@ds/utils/clipboard'
import { ref } from 'vue'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  setup() {
    const { draft, updateField } = useEntityDetail('ai_apps')
    return {
      m,
      draft,
      updateField,
      themeOptions: ref([
        { label: 'Oracle Redwood', value: 'siebel' },
        { label: 'Salesforce', value: 'salesforce' },
        { label: 'Magnet Dark', value: 'dark' },
      ]),
    }
  },
  computed: {
    appUrl() {
      let panelUrl = `${this.$appConfig?.panel?.baseUrl}/#/?ai_app=${this.system_name}`

      if (panelUrl.startsWith('/')) {
        panelUrl = `${window.location.origin}${panelUrl}`
      }

      return panelUrl
    },
    system_name() {
      return this.draft?.system_name || ''
    },
    show_close_button: {
      get() {
        return this.draft?.settings?.show_close_button || false
      },
      set(value) {
        this.updateField('settings.show_close_button', value)
      },
    },
    isIconHide: {
      get() {
        return !(this.draft?.settings?.is_icon_hide || false)
      },
      set(value) {
        this.updateField('settings.is_icon_hide', !value)
      },
    },
    theme: {
      get() {
        const theme = this.draft?.settings?.theme || 'siebel'
        return this.themeOptions.find((option) => option.value === theme)
      },
      set({ value }) {
        this.updateField('settings.theme', value)
      },
    },
  },
  methods: {
    copy() {
      copyToClipboard(this.appUrl || '')

      notify.success(m.common_copiedToClipboard())
    },
  },
}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
.card-hover:hover {
  background: var(--ds-color-background);
  cursor: pointer;
  border-color: var(--ds-color-primary);
}
</style>
