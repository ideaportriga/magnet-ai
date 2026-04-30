import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import DsNumberField from './DsNumberField.vue'
import DsNumberFieldInput from './DsNumberFieldInput.vue'
import DsNumberFieldIncrement from './DsNumberFieldIncrement.vue'
import DsNumberFieldDecrement from './DsNumberFieldDecrement.vue'

const Host = defineComponent({
  props: {
    initial: { type: Number, default: 1 },
    min: Number,
    max: Number,
    disabled: Boolean,
  },
  setup(props) {
    const value = ref<number | undefined>(props.initial)
    return { value }
  },
  render() {
    return h(
      DsNumberField,
      {
        modelValue: this.value,
        min: this.min,
        max: this.max,
        disabled: this.disabled,
        'onUpdate:modelValue': (v: number | undefined) => (this.value = v),
      },
      {
        default: () => [
          h(DsNumberFieldDecrement, null, () => '-'),
          h(DsNumberFieldInput),
          h(DsNumberFieldIncrement, null, () => '+'),
        ],
      },
    )
  },
})

describe('DsNumberField', () => {
  it('renders the root, input, and step controls', () => {
    const wrapper = mount(Host)
    expect(wrapper.find('[data-test="ds-number-field"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="ds-number-field-input"]').exists()).toBe(true)
  })

  it('reflects the initial value in the input', () => {
    const wrapper = mount(Host, { props: { initial: 7 } })
    const input = wrapper.find('input').element as HTMLInputElement
    expect(input.value).toBe('7')
  })

  it('exposes the ds-number-field class on the root', () => {
    const wrapper = mount(Host)
    expect(wrapper.find('[data-test="ds-number-field"]').classes()).toContain('ds-number-field')
  })
})
