<script setup lang="ts">
/**
 * `<km-locale-switcher>` — language picker. Reads/writes locale through
 * `@shared/i18n` (paraglide-backed). Drop-in replacement for the legacy
 * Quasar-menu version.
 */

import { computed } from 'vue'
import { DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger } from 'reka-ui'
import { useLocale } from '@shared/i18n'
import KmGlyph from './KmGlyph.vue'

const { locale, setLocale, locales } = useLocale()

const localeLabels: Record<string, string> = {
  en: 'EN', ru: 'RU', lv: 'LV', es: 'ES', fr: 'FR', de: 'DE', it: 'IT',
}
const localeFullLabels: Record<string, string> = {
  en: 'English', ru: 'Русский', lv: 'Latviešu', es: 'Español', fr: 'Français', de: 'Deutsch', it: 'Italiano',
}
const localeOrder = ['en', 'lv', 'es', 'fr', 'de', 'ru', 'it']

const currentLabel = computed(() => localeLabels[locale.value] ?? locale.value)

const localeOptions = computed(() =>
  localeOrder
    .filter((loc) => (locales as readonly string[]).includes(loc))
    .concat((locales as readonly string[]).filter((loc) => !localeOrder.includes(loc)))
    .map((loc) => ({
      value: loc,
      label: localeFullLabels[loc] ?? loc,
    })),
)
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger as-child>
      <button class="km-locale-switcher" type="button" data-test="km-locale-switcher">
        <KmGlyph name="globe" size="14px" tone="subtle" />
        <span class="km-locale-switcher__label">{{ currentLabel }}</span>
        <KmGlyph name="chevron-down" size="14px" tone="subtle" />
      </button>
    </DropdownMenuTrigger>

    <DropdownMenuPortal>
      <DropdownMenuContent
        class="ds-menu km-locale-switcher__menu"
        side="bottom"
        align="center"
        :side-offset="4"
      >
        <DropdownMenuItem
          v-for="opt in localeOptions"
          :key="opt.value"
          class="ds-menu__item"
          :data-active="opt.value === locale ? 'true' : undefined"
          @select="setLocale(opt.value)"
        >
          {{ opt.label }}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>

<style>
.km-locale-switcher {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-2xs);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-md);
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-locale-switcher:hover { background: var(--ds-color-primary-bg); }

.km-locale-switcher__label {
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-medium);
}

.km-locale-switcher__menu { min-inline-size: 8rem; }
.ds-menu__item[data-active='true'] {
  color: var(--ds-color-primary);
  font-weight: var(--ds-font-weight-medium);
}
</style>
