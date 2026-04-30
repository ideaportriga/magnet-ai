<template>
  <km-drawer-layout storage-key="drawer-ai-apps-preview" :default-width="520" :max-width="1200" no-scroll>
    <template #header>
      <div class="cluster">
        <div class="flex-1">{{ m.common_preview() }}</div>
        <div class="flex-none" />
      </div>
    </template>
    <div class="flex-1 relative-position full-height">
      <iframe v-if="iframeSrc" ref="iframe" class="absolute-full" :src="iframeSrc" width="100%" height="100%" frameborder="0" allowfullscreen :style="{ zIndex: 10 }" allow="clipboard-write" />
      <div class="flex absolute-center" :style="{ zIndex: 5 }">
        <km-loader size="62px" />
      </div>
    </div>
  </km-drawer-layout>
</template>

<script>
import { ref } from 'vue'
import { useLoading } from '@ds/composables/useLoading'
import { m } from '@/paraglide/messages'
import { useState } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
export default {
  setup() {
    const tab = ref('')
    const iframe = ref(null)
    const loading = useState('globalLoading')
    const { draft } = useEntityDetail('ai_apps')

    return { m, loading, tab, iframe, draft }
  },
  computed: {
    baseUrl() {
      let panel = this.$appConfig?.panel?.baseUrl || ''
      if (!panel.startsWith('http')) {
        panel = `https://${panel}`
      }
      let admin = this.$appConfig?.admin?.baseUrl || ''
      if (!admin.startsWith('http')) {
        admin = `https://${admin}`
      }

      return { admin, panel }
    },
    app() {
      return this.draft
    },
    iframeSrc() {
      let panelUrl = `${this.$appConfig?.panel?.baseUrl}/#/?ai_app=${this.app?.system_name}`

      if (panelUrl.startsWith('/')) {
        panelUrl = `${window.location.origin}${panelUrl}`
      }

      return panelUrl
    },
  },
  watch: {
    iframeSrc(val) {
      if (!this.$refs.iframe) return
      this.$refs.iframe.src = val
      this.$refs.iframe.contentWindow?.location.reload()
    },
    app: {
      immediate: true,
      deep: true,
      handler(val) {
        if (val) {
          this.sendMessage({ app: JSON.stringify(val) })
        }
      },
    },
    loading: {
      immediate: true,
      handler(val) {
        const ds = useLoading()
        if (val) {
          this._dsLoadingHide = ds.show()
        } else if (this._dsLoadingHide) {
          this._dsLoadingHide()
          this._dsLoadingHide = null
        }
      },
    },
    panels: {
      immediate: true,
      handler(val) {
        this.tab = (val || [])?.[0]?.name
      },
    },
  },
  mounted() {
    // §B.4 — bind the listener to a property so beforeUnmount can detach it.
    // Anonymous inline listener leaked on every drawer open.
    this._onWindowMessage = (event) => {
      if (event.origin !== this.baseUrl.panel && event.origin !== window.location.origin) return
      if (event.data.type === 'reload_app') {
        this.sendMessage({ app: JSON.stringify(this.app) })
      }
      if (event.data.type === 'reload_iframe') {
        const currentSrc = this.$refs.iframe?.src
        if (!currentSrc) return
        this.$refs.iframe.src = ''
        setTimeout(() => {
          if (this.$refs.iframe) {
            this.$refs.iframe.src = currentSrc
          }
        }, 100)
      }
    }
    window.addEventListener('message', this._onWindowMessage)
  },
  beforeUnmount() {
    if (this._onWindowMessage) {
      window.removeEventListener('message', this._onWindowMessage)
      this._onWindowMessage = null
    }
  },
  methods: {
    sendMessage(data) {
      this.$refs.iframe?.contentWindow?.postMessage(data, this.$appConfig?.panel?.baseUrl)
    },
    handleMessage(event) {
      if (event.data === 'reload') {
        location.reload()
      }
    },
  },
}
</script>
