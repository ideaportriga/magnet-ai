<template lang="pug">
.km-picker.km-select.rounded-borders.ba-border.q-pl-12.q-pr-sm.center-flex-y(
  @validate='validate',
  :class='{ "km-open-popup": popupShow, "km-field-error": errorState, "shake-sideways": animateValidation }'
)
  .row.items-center.full-width
    .col
      template(v-if='modelValue')
        .km-label {{ modelValue }}
      template(v-else-if='placeholder')
        .km-label.text-placeholder {{ placeholder }}
    .col-auto
      q-icon(:class='{ rotate180: popupShow }', :color='errorState ? "status-rejected" : "seemless"', name='expand_more', size='24px')
  q-menu.km-shadow.border-radius-6(
    anchor='top right',
    self='bottom right',
    @update:modelValue='showPopup($event)',
    style='min-height: 418px; width: 340px',
    ref='menu'
  )
    .bg-white.q-pl-md.q-py-md
      //- Search
      .q-pr-md
        //- icon-before="search"
        km-input.full-width(
          icon-before='search',
          @input='search = $event',
          :model-value='search',
          autofocus,
          :placeholder='searchPlaceholder',
          clearable
        )

      //- Body

      .q-mt-md.q-pr-xs
        template(v-if='loading')
          .center-flex.fit
            q-spinner(size='30px', color='primary')
        template(v-else-if='options?.length')
          template(v-if='firstColumn?.title')
            .row.q-mb-md.full-width.q-pr-md
              .col.q-pr-sm.q-pl-xs
                .km-field.text-secondary-text {{ firstColumn?.title }}
              .col-auto.q-pl-sm(style='width: 120px')
                .km-field.text-secondary-text.text-right {{ secondColumn?.title }}

          q-scroll-area(style='height: 300px')
            .q-mr-md
              template(v-for='(opt, i) in internalOptions', :key='`option-${i}`')
                .dropdown-option.q-pl-sm.q-pr-xs.rounded-borders(@click='setValue(opt)', v-close-popup)
                  .row.q-py-xs.full-width
                    .col
                      div {{ Array.isArray(firstColumn?.display) ? firstColumn?.display.map((v) => opt[v]).join(' ') : firstColumn?.display }}
                    .col-auto.text-right(style='width: 120px', v-if='secondColumn?.display?.length')
                      .q-pr-xs {{ Array.isArray(secondColumn?.display) ? secondColumn?.display.map((v) => opt[v]).join(' ') : secondColumn?.display }}
                  .row.bb-border.q-pb-xs
                    .text-secondary-text(v-if='firstColumn.subValue') {{ opt[firstColumn.subValue] }}
      q-inner-loading(:showing='pickLoading', :label='`Please wait...`', label-class='seemless', label-style='font-size: 1.4em')
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    searchPlaceholder: {
      type: String,
      default: 'Search approver',
    },
    modelValue: String,
    label: String,
    loading: Boolean,
    pickLoading: Boolean,
    placeholder: String,
    disabled: Boolean,
    required: Boolean,
    options: {
      type: Array,
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
    showCount: {
      type: Boolean,
      default: false,
    },
    autofocus: {
      default: false,
      type: Boolean,
    },
    beforeIcon: {
      default: '',
      type: String,
    },
    searchFields: {
      type: Array,
    },
    firstColumn: {
      type: Object,
      default() {
        return {
          title: 'Approver name, position',
          display: ['Approver First Name', 'Approver Last Name'],
          subValue: 'Position',
        }
      },
    },
    secondColumn: {
      type: Object,
      default() {
        return {
          title: 'Approval limit',
          display: ['Approval Limit Formatted'],
        }
      },
    },
  },
  emits: ['update:modelValue', 'blur', 'clear', 'popupShow'],
  setup() {
    return {
      popupShow: ref(false),
      search: ref(''),
      menu: ref(null),
      showError: ref(false),
      animateValidation: ref(false),
    }
  },
  computed: {
    internalOptions() {
      if (this.search) {
        // if search fields are not provided - search in all fields
        let searchFields = this.searchFields ?? Object.keys(this.options?.[0] ?? {})

        return (
          this.options?.filter((opt) => {
            let searchString =
              Object.entries(opt)
                .filter(([key, val]) => searchFields.includes(key) && val)
                .map(([, val]) => `${val}`.toLowerCase().replace(/\s/g, ''))
                .join('') ?? ''
            // console.log('picker - searchString: ',searchString )
            return searchString.includes(this.search.toLowerCase().replace(/\s/g, ''))
          }) ?? []
        )
      } else return this.options
    },
    errorState() {
      return this.showError && !this.modelValue
    },
  },
  methods: {
    showPopup(val) {
      this.popupShow = val
      if (val) this.$emit('popupShow')
      else {
        this.search = ''
      }
    },
    setValue(opt) {
      this.$emit('update:modelValue', opt)
    },
    async validate() {
      this.showError = true
      const res = this.errorState
      if (res) {
        this.animateValidation = true
        await new Promise((done) => setTimeout(() => done(), 500))
        this.animateValidation = false
      }
      return !res
    },
  },
}
</script>

<style lang="stylus"></style>
