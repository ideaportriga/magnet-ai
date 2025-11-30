<template lang="pug">
q-select.km-control.km-select.ba-border(
  :bg-color='bgColor',
  dropdown-icon='expand_more',
  :placeholder='placeholder',
  borderless,
  rounded,
  :multiple='multiple',
  :use-chips='useChips',
  dense,
  :model-value='modelValue',
  @update:modelValue='onUpdate',
  :options='filteredOptions',
  options-dense,
  options-selected-class='bg-primary-bg',
  popup-content-class='km-shadow border-radius-6 select-options',
  @popup-show='showPopup()',
  @popup-hide='hidePopup()',
  :class='{ "km-select-multiple-chips": useChips, "km-open-popup": popupShow, "text-overflow": maxWidth != "none", "km-error-select": errorMessage !== undefined }',
  :style='{ maxWidth, "--field-height": height, "--field-max-height": height, "--field-min-height": minHeight }',
  :disable='disabled',
  :emit-value='emitValue',
  :map-options='mapOptions',
  :option-value='optionValue',
  :option-label='optionLabel',
  v-bind='$attrs'
)
  template(#prepend, v-if='iconBefore || (!modelValue && placeholder) || permanentPlaceholder')
    template(v-if='iconBefore')
      q-icon(:name='iconBefore', color='icon')
    template(v-if='!modelValue && placeholder')
      .km-label.text-placeholder(:class='{ "q-pl-6": iconBefore }') {{ placeholder }}
    template(v-if='permanentPlaceholder')
      .km-label.text-placeholder(:class='{ "q-pl-6": iconBefore }') {{ permanentPlaceholder }}:
  template(#no-option)
    q-item(v-if='hasDropdownSearch')
      km-input.full-width(ref='searchInput', placeholder='Search', iconBefore='search', v-model='needle', @input='handleSearch')
    template(else)
      .km-label.q-pa-md.text-placeholder {{ noOptionText }}

  template(#before-options)
    q-item(v-if='multiple && selectAll')
      km-checkbox(:model-value='isAllSelected', @update:model-value='toggleSelectAll', color='primary') Select All
    q-separator
    q-item(v-if='hasDropdownSearch')
      km-input.full-width(ref='searchInput', placeholder='Search', iconBefore='search', v-model='needle', @input='handleSearch') 
    q-separator

  template(v-slot:selected='scope', v-if='multiple && !useChips')
    template(v-if='!useChips')
      template(v-if='modelValue?.length === 1')
        div {{ modelValue?.[0]?.label }}
      template(v-else-if='modelValue?.length')
        div {{ modelValue?.length }} selected
      template(v-else)
        div nothing selected

  template(#selected-item='scope', v-if='useChips')
    q-chip.q-my-none(text-color='primary', color='primary-light', square, size='12px', :tabindex='scope.tabindex') 
      .row.fit.items-center
        .col.text-center {{ optionLabel ? scope.opt[optionLabel] : scope.opt.label }}
        .col-auto.q-ml-xs
          q-icon.q-my-auto(name='fa fa-times', @click.stop.prevent='handleRemove(scope, $event)')

  template(v-slot:option='{ itemProps, opt, selected, toggleOption }')
    template(v-if='$slots.option')
      slot(name='option', :itemProps='itemProps', :opt='opt', :selected='selected', :toggleOption='toggleOption', :data-test='"options"')
    template(v-else-if='$theme === "default"')
      q-item.ba-border(data-test='options', v-bind='itemProps', dense)
        q-item-section(side='', v-if='multiple')
          km-checkbox(:model-value='selected', @update:model-value='toggleOption(opt)', color='primary')
        q-item-section
          q-item-label.km-label(v-html='optionLabel ? opt[optionLabel] : opt.label ? opt.label : opt')
    template(v-else)
      q-item.bg-picker-list-bg.select-option(data-test='options', v-bind='itemProps', dense)
        q-item-section(side='', v-if='multiple')
          km-checkbox(:model-value='selected', @update:model-value='toggleOption(opt)', color='primary')
        q-item-section
          q-item-label.km-label.text-secondary-text(v-html='optionLabel ? opt[optionLabel] : opt.label ? opt.label : opt')

template(v-if='errorMessage')
  .km-small-chip.q-pa-4.q-pl-8.text-error-text {{ errorMessage }}
</template>

<script>
import { toRefs, ref } from 'vue'
import { useValidation, validationProps } from '@shared'

export default {
  props: {
    optionShow: {
      type: [String, Function],
      default: '',
    },
    label: String,
    maxWidth: {
      default: 'none',
    },
    modelValue: {},
    placeholder: String,
    permanentPlaceholder: String,
    disabled: Boolean,
    required: Boolean,
    options: {
      type: Array,
    },
    optionValue: {
      type: String,
    },
    optionLabel: {
      type: String,
    },
    emitValue: {
      type: Boolean,
      default: false,
    },
    mapOptions: {
      type: Boolean,
      default: false,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    maxLength: {
      type: String,
      default: '',
    },
    clearable: Boolean,
    noOptionText: {
      type: String,
      default: 'No Options available',
    },
    showCount: {
      type: Boolean,
      default: false,
    },
    autofocus: {
      default: false,
      type: Boolean,
    },
    multiple: {
      default: false,
      type: Boolean,
    },
    useChips: {
      default: false,
      type: Boolean,
    },
    iconBefore: {
      default: '',
      type: String,
    },
    height: {
      default: '34px',
      type: String,
    },
    minHeight: {
      default: '34px',
      type: String,
    },
    bgColor: {
      default: 'none',
      type: String,
    },
    hasDropdownSearch: {
      default: false,
      type: Boolean,
    },
    selectAll: {
      default: false,
      type: Boolean,
    },
    ...validationProps(),
  },
  emits: ['update:modelValue', 'blur', 'clear', 'popupShow', 'update:error'],
  setup(props) {
    const { modelValue, rules } = toRefs(props)
    return {
      popupShow: ref(false),
      ...useValidation(modelValue, rules),
      needle: ref(''),
    }
  },
  computed: {
    isAllSelected() {
      return this.modelValue?.length === this.options?.length
    },
    filteredOptions() {
      let visibleOptions = this.options

      if (this.optionShow) {
        visibleOptions = visibleOptions.filter((item) => {
          if (typeof this.optionShow === 'string') {
            return item[this.optionShow]
          } else if (typeof this.optionShow === 'function') {
            return this.optionShow(item)
          }
          return true
        })
      }

      if (visibleOptions?.[0]?.modified_at) {
        return visibleOptions
          .filter(
            (item) =>
              this.needle === '' || (item?.[this.optionLabel] || item?.label || item).toLowerCase().indexOf(this.needle.toLocaleLowerCase()) > -1
          )
          .sort((a, b) => new Date(b.modified_at) - new Date(a.modified_at))
      }

      return visibleOptions?.filter(
        (item) => this.needle === '' || (item?.[this.optionLabel] || item?.label || item).toLowerCase().indexOf(this.needle.toLocaleLowerCase()) > -1
      )
    },
  },
  methods: {
    handleSearch(event) {
      this.needle = event
      this.$nextTick(() => {
        this.$refs.searchInput?.focus()
      })
    },
    toggleSelectAll(value) {
      if (value) {
        const allOptions = this.filteredOptions.map((option) => (this.emitValue ? option[this.optionValue] : option))
        this.$emit('update:modelValue', allOptions)
      } else {
        this.$emit('update:modelValue', [])
      }
    },
    onUpdate($event) {
      this.$emit('update:modelValue', $event)
      this.$emit('update:error', false)
    },
    showPopup() {
      this.$emit('popupShow')
      this.popupShow = true
    },
    hidePopup() {
      this.popupShow = false
    },
    handleRemove(scope, event) {
      event.stopPropagation()
      scope.removeAtIndex(scope.index)
    },
  },
}
</script>

<style lang="stylus">
.km-select .q-field__control .q-field__native{
  }
.text-overflow .q-field__control-container span {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  // color: var(--q-secondary-text)
}
</style>
