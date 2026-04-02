<template lang="pug">
div
  km-section(title='Change Theme', subTitle='Change appearance of AI App panel')
    div(style='width: 220px')
      km-select(v-model='theme', :options='themeOptions', color='primary', size='sm', :disable='false')
  q-separator.q-my-lg
  km-section(title='Show Close button', subTitle='Control if Close button is displayed inside the app')
    q-toggle(v-model='show_close_button', color='primary', size='sm', :disable='false')
  q-separator.q-my-lg
  km-section(title='Show Logo', subTitle='Show logo in AI App panel')
    q-toggle(v-model='isIconHide', color='primary', size='sm', :disable='false')
  q-separator.q-my-lg
  km-section(title='AI App URL', subTitle='URL to embed the AI App')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 AI App URL
    .row
      .col.q-mr-sm
        km-input(ref='input', border-radius='8px', height='36px', :readonly='true', :model-value='appUrl')
      .col-auto
        km-btn(icon='fas fa-copy', iconSize='16px', size='sm', flat, @click='copy', tooltip='Copy')
</template>

<script>
import { copyToClipboard } from 'quasar'
import { ref } from 'vue'
import { useEntityDetail } from '@/composables/useEntityDetail'

export default {
  setup() {
    const { draft, updateField } = useEntityDetail('ai_apps')
    return {
      draft,
      updateField,
      themeOptions: ref([
        { label: 'Oracle Redwood', value: 'siebel' },
        { label: 'Salesforce', value: 'salesforce' },
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

      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: 'AI App URL has been copied to clipboard',
        timeout: 1000,
      })
    },
  },
}
</script>

<style lang="stylus">

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}

.card-hover:hover  {
  background: var(--q-background)
  cursor pointer
  border-color: var(--q-primary)
}
</style>
