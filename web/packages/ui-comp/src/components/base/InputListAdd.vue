<template lang="pug">
div
  q-list.bordered.q-gutter-sm
    template(v-for='(item, index) in recordsModel', :key='index')
      .row
        km-input.col(
          :model-value='recordsModel[index]',
          @update:model-value='(val) => updateRecord(val, index)',
          @blur='validateField(index)',
          label='Enter a record',
          hint='Type something and press +',
          filled,
          dense,
          :error='errors[index]',
          :error-message='errors[index] ? "Please enter a valid record" : ""'
        )
        .col-auto.q-ml-sm
          km-btn.q-mx-xs(flat, icon='far fa-trash-can', iconSize='16px', size='13px', @click.stop='removeRecord(index)')

  .col-auto.q-mt-sm
    .row.col-auto
      km-btn(
        icon='fas fa-plus',
        iconColor='icon',
        hoverColor='primary',
        labelClass='km-title',
        flat,
        iconSize='14px',
        :label='btnLabel',
        :disable='hasValidationError',
        @click='addRecord'
      )
</template>

<script>
export default {
  name: 'RecordListAdder',
  props: {
    btnLabel: {
      type: String,
      default: 'Add URL',
    },
    modelValue: {
      type: Array,
      default: () => [],
    },
    validateRecord: {
      type: Function,
      default: (value) => value.trim().length >= 3,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      errors: [],
    }
  },
  computed: {
    recordsModel: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      },
    },
    hasValidationError() {
      return this.recordsModel.some((_, index) => this.errors[index])
    },
  },
  methods: {
    addRecord() {
      const lastIndex = this.recordsModel.length - 1
      if (this.recordsModel.length === 0 || !this.errors[lastIndex]) {
        this.recordsModel = [...this.recordsModel, '']
        this.errors.push(false)
      } else {
        this.errors[lastIndex] = true
      }
    },
    removeRecord(index) {
      const updatedRecords = [...this.recordsModel]
      const updatedErrors = [...this.errors]
      updatedRecords.splice(index, 1)
      updatedErrors.splice(index, 1)
      this.recordsModel = updatedRecords
      this.errors = updatedErrors
    },
    updateRecord(newVal, index) {
      this.recordsModel[index] = newVal
      this.validateField(index)
    },
    validateField(index) {
      this.errors[index] = !this.validateRecord(this.recordsModel[index])
    },
  },
}
</script>

<style scoped>
.q-card {
  max-width: 400px;
  margin: 0 auto;
}
</style>
