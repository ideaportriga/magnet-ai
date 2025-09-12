<template lang="pug">
.row.no-wrap.relative-position
  template(v-if='disable')
    .absolute.fit(style='z-index: 100; background: rgba(255, 255, 255, 0.3); pointer-events: none !important')

  .col(:class='{ "no-pointer-events": disable }')
    .km-button(
      :class='[{ "km-button-flat": flat }, contentClass, { "ba-border border-radius-6": inputLike }, { "km-button-link": link }, { "km-button-icon": (icon || svgIcon) && !label?.length }]',
      :style='contentStyle',
      @click='!dropdown && click()'
    )
      .row.full-height.items-center.relative-position.no-wrap
        slot
          template(v-if='icon')
            q-icon.col-auto(:name='icon', :size='iconSize', style='')
          template(v-if='svgIcon')
            km-icon.col-auto(:name='svgIcon', width='24', height='18')
          template(v-if='(icon || svgIcon) && label')
            .q-pl-sm
          .col.text-left.ellipsis(style='margin-bottom: 1px; line-height: normal', :class='labelTypographyClass') {{ label }}
          template(v-if='loading')
            q-spinner.text-primary.q-pl-xs(size='24px')
          template(v-else-if='dropdown')
            q-icon.q-pl-xs.col-auto(name='expand_more', size='24px')
              //- q-icon(name="expand_more" size="22px").q-ml-sm
          template(v-else-if='iconAfter')
            q-icon.q-pl-xs.col-auto(:name='iconAfter', :size='iconSize')
              //- q-icon(name="expand_more" size="22px").q-ml-sm

  template(v-if='dropdown')
    q-menu.km-shadow(v-model='menu', anchor='bottom right', self='top right', :offset='[0, 4]')
      template(v-for='opt in options')
        .dropdown-option-dense.row.items-center.q-px-12(@click='$emit("click-option", opt)', v-close-popup)
          template(v-if='opt?.svgIcon')
            km-icon.q-mr-sm(:name='opt.svgIcon', width='24', height='18')
          .km-button-text.text-primary {{ opt.label ?? opt }}

  template(v-if='tooltip')
    q-tooltip.bg-icon(:delay='100', :offset='[0, 4]', anchor='top middle', self='bottom middle', transition-show='jump-up', dense)
      .text-white.km-chip {{ tooltip }}
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    label: String,
    secondary: {
      type: Boolean,
      default: false,
    },
    flat: {
      type: Boolean,
      default: false,
    },
    simple: {
      type: Boolean,
      default: false,
    },
    dropdown: {
      type: Boolean,
      default: false,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    size: {
      type: String,
    },
    disable: {
      type: Boolean,
      default: false,
    },
    labelClass: {
      type: String,
    },
    tooltip: {
      type: String,
    },
    optionsClass: {
      type: String,
    },
    color: String,
    bg: String,
    hoverColor: String,
    hoverBg: String,
    icon: String,
    iconColor: String,
    iconSize: {
      type: String,
      default: '22px',
    },
    svgIcon: String,
    iconAfter: {
      type: String,
    },
    contentStyle: String,
    contentClass: String,
    options: Array,
    inputLike: {
      type: Boolean,
      default: false,
    },
    link: {
      type: Boolean,
      String: false,
    },
  },
  emits: ['click', 'click-option'],
  setup() {
    return {
      hover: ref(false),
    }
  },
  computed: {
    buttonHeight() {
      return this.size === 'sm' ? 'var(--button-sm)' : this.size === 'xs' ? 'var(--button-xs)' : this.size === 'auto' ? 'auto' : '34px'
    },
    labelTypographyClass() {
      return this.labelClass ?? (this.size === 'sm' ? 'km-button-sm-text' : 'km-button-text')
    },
    btnType() {
      return this.secondary ? 'secondary' : this.flat || this.link ? 'flat' : this.simple ? 'simple' : 'primary'
    },

    // BG

    bgVar() {
      return this.bg ? `var(--q-${this.bg}` : `var(--q-btn-${this.btnType}-bg)`
    },

    hoverBgVar() {
      return this.hoverBg ? `var(--q-${this.hoverBg})` : `var(--q-btn-${this.btnType}-hover-bg)`
    },

    activeBgVar() {
      return `var(--q-btn-${this.btnType}-active-bg)`
    },

    // COLOR

    colorVar() {
      return this.color ? `var(--q-${this.color}` : `var(--q-btn-${this.btnType}-text)`
    },

    hoverColorVar() {
      return this.hoverColor ? `var(--q-${this.hoverColor}` : `var(--q-btn-${this.btnType}-hover-text)`
    },

    activeColorVar() {
      return `var(--q-btn-${this.btnType}-active-text)`
    },

    // ICON

    iconColorVar() {
      // return this.flat || this.link ? `var(--q-btn-${this.btnType}-icon)` : `currentColor`
      return this.iconColor ? `var(--q-${this.iconColor}` : this.flat || this.link ? `var(--q-btn-${this.btnType}-icon)` : `currentColor`
    },

    iconColorHoverVar() {
      return this.flat || this.link ? `var(--q-btn-${this.btnType}-hover-icon)` : `currentColor`
    },

    iconColorActiveVar() {
      return this.flat || this.link ? `var(--q-btn-${this.btnType}-active-icon)` : `currentColor`
    },
  },
  methods: {
    click() {
      this.$emit('click', event)
    },
  },
}
</script>

<style lang="stylus" scoped>
$btn-height = v-bind(buttonHeight);
.km-button-link
  &:hover
      transition: all 200ms linear;
      color: v-bind(hoverColorVar)
      .q-icon
        color: v-bind(iconColorHoverVar)

    &:active
      transition: all 200ms linear;
      transform: translateY(0px);
      color: v-bind(activeColorVar)
      .q-icon
        color: v-bind(iconColorActiveVar)

    &:hover:before
      transition: all 200ms linear;
      background: v-bind(hoverBgVar) !important
      // transform: translateY(-2px);

    &:active:before
      transition: all 200ms linear;
      background: v-bind(activeBgVar) !important
      // transform: scale(0.98, 0.98)
  padding: 0 !important
  margin: 0 !important
.km-button
  display: inline-block;
  box-sizing: inherit;
  position: relative;
  cursor: pointer;
  user-select: none;
  transition: all 150ms linear;
  height: $btn-height !important
  padding-left: 12px;
  padding-right: 12px;
  text-align: center;
  background: transparent !important;
  white-space: nowrap;
  text-decoration: none !important;
  text-transform: none;
  appearance: none;
  outline: 0px !important;
  -webkit-text-size-adjust: 100%;
  -webkit-font-smoothing: antialiased;
  color: v-bind(colorVar)
  font-size: 14px
  font-family: var(--font-default) !important
  width: 100%
  // box-shadow: 2px 3px 10px #aaa;
  &:hover
    transition: all 200ms linear;
    color: v-bind(hoverColorVar)
    .q-icon
      color: v-bind(iconColorHoverVar)

  &:active
    transition: all 200ms linear;
    transform: translateY(0px);
    color: v-bind(activeColorVar)
    .q-icon
      color: v-bind(iconColorActiveVar)

  &:hover:before
    transition: all 200ms linear;
    background: v-bind(hoverBgVar) !important
    // transform: translateY(-2px);

  &:active:before
    transition: all 200ms linear;
    background: v-bind(activeBgVar) !important
    // transform: scale(0.98, 0.98)

  &::before
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    display: block;
    border-radius: 4px;
    background: v-bind(bgVar);
    width: 100%;
    height: 100%;

  .q-icon
    color: v-bind(iconColorVar)
</style>
