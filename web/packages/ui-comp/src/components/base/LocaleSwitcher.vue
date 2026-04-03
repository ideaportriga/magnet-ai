<template lang="pug">
.relative-position
  .locale-trigger.row.items-center.q-gap-6.cursor-pointer.q-px-sm.q-py-xs
    q-icon(name='fas fa-globe', size='14px', color='secondary-text')
    span.km-title {{ currentLabel }}
    q-icon(name='expand_more', size='14px', color='secondary-text')
  q-menu(anchor='bottom middle', self='top middle', :offset='[0, 4]')
    q-list(dense, padding, style='min-width: 120px')
      q-item(
        v-for='opt in localeOptions',
        :key='opt.value',
        clickable,
        v-close-popup,
        dense,
        @click='setLocale(opt.value)',
        :active='opt.value === locale',
        active-class='locale-active'
      )
        q-item-section
          .km-title {{ opt.label }}
</template>

<script setup>
import { computed } from 'vue'
import { useLocale } from '@shared/i18n'

const { locale, setLocale, locales } = useLocale()

const localeLabels = {
  en: 'EN',
  ru: 'RU',
}

const localeFullLabels = {
  en: 'English',
  ru: 'Русский',
}

const currentLabel = computed(() => localeLabels[locale.value] || locale.value)

const localeOptions = computed(() =>
  locales.map((loc) => ({
    value: loc,
    label: localeFullLabels[loc] || loc,
  }))
)
</script>

<style lang="stylus" scoped>
.locale-trigger
  border-radius 6px
  transition background 0.15s ease
  &:hover
    background var(--q-primary-bg, rgba(0, 0, 0, 0.04))

.locale-active
  color var(--q-primary) !important
  font-weight 500
</style>
