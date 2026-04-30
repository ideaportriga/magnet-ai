<template>
  <div
    v-if="selectedTab"
    class="bg-panel-main-bg full-height stack bl-border relative-position"
    data-gap="0"
  >
    <div
      class="cluster bg-header-bg px-md"
      style="block-size: 55px; min-block-size: 55px; flex-shrink: 0"
      data-justify="between"
    >
      <!--logo-->
      <div
        class="flex items-center justify-center"
        :style="{ width: &quot;32px&quot;, height: &quot;32px&quot;, borderRadius: &quot;50%&quot; }"
        :class="{ &quot;bg-white&quot;: !isIconHide }"
      >
        <km-icon
          v-if="!is_icon_hide"
          :name="&quot;magnet&quot;"
          width="21"
          height="23"
        />
      </div>
      <!--close button-->
      <div
        class="flex items-center justify-center"
        :style="{ width: &quot;32px&quot;, height: &quot;32px&quot;, borderRadius: &quot;50%&quot; }"
      >
        <li
          v-if="show_close_button"
          class="km-item"
          clickable
          dense
        >
          <km-glyph
            class="p-xs rounded-borders"
            name="close"
            rounded
            size="20px"
            tone="inverse"
            @click="hidePanel"
          />
        </li>
      </div>
    </div>
    <km-image
      v-if="$theme === &quot;siebel&quot;"
      class="redwood-strip"
      src="strip.png"
    />
    <!-- main scrollable content-->
    <div class="flex-1 overflow-auto">
      <agent-tab
        v-if="selectedTab"
        :agent="selectedTab.config.agent"
        :tab="selectedTab"
      />
    </div>
    <div
      class="cluster bg-footer-bg full-width footer"
      data-justify="center"
      style="flex-shrink: 0"
    >
      <div class="footer-text">
        {{ m.panel_poweredBy() }}
      </div>
    </div>
  </div>
</template>
<script setup>
import { m } from '@/paraglide/messages'
import { storeToRefs } from 'pinia'
import { useAiApps } from '@/pinia'
import { computed, watch } from 'vue'
import { getCurrentInstance } from 'vue'
const { appContext } = getCurrentInstance()
const aiApps = useAiApps()
const { selectedTab } = storeToRefs(aiApps)

const show_close_button = computed(() => selectedTab?.value?.entityObject?.channels?.web?.show_close_button || false)
const is_icon_hide = computed(() => selectedTab?.value?.entityObject?.channels?.web?.is_icon_hide || false)

const theme = computed(() => selectedTab?.value?.entityObject?.channels?.web?.theme || 'siebel')

watch(
  theme,
  (newVal) => {
    // §B.9 — $setTheme may be absent if the theming plugin isn't loaded
    // (happens in storybook / cypress harness). Silent no-op is fine.
    const setter = appContext.config.globalProperties.$setTheme
    if (typeof setter === 'function') setter(newVal)
  },
  { immediate: true }
)
// const channels = computed(() => selectedTab?.value?.entityObject?.channels)
</script>
