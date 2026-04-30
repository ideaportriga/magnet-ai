import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import DsRadioGroup from './DsRadioGroup.vue'

const options = [
  { value: 'a', label: 'Alpha' },
  { value: 'b', label: 'Beta' },
  { value: 'c', label: 'Gamma', disabled: true },
]

describe('DsRadioGroup', () => {
  it('renders one item per option with labels', () => {
    const wrapper = mount(DsRadioGroup, { props: { options } })
    expect(wrapper.find('[data-test="ds-radio-group"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Alpha')
    expect(wrapper.text()).toContain('Beta')
    expect(wrapper.text()).toContain('Gamma')
  })

  it('marks the active option with data-state="checked"', () => {
    const wrapper = mount(DsRadioGroup, { props: { options, modelValue: 'b' } })
    const items = wrapper.findAll('.ds-radio__root')
    const states = items.map((i) => i.attributes('data-state'))
    expect(states).toEqual(['unchecked', 'checked', 'unchecked'])
  })

  it('emits update:modelValue with the selected option value', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('a')
        return { value }
      },
      render() {
        return h(DsRadioGroup, {
          options,
          modelValue: this.value,
          'onUpdate:modelValue': (v: string) => (this.value = v),
        })
      },
    })
    const wrapper = mount(Host)
    const items = wrapper.findAll('.ds-radio__root')
    await items[1].trigger('click')
    expect((wrapper.vm as unknown as { value: string }).value).toBe('b')
  })

  it('keeps disabled options non-interactive', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('a')
        return { value }
      },
      render() {
        return h(DsRadioGroup, {
          options,
          modelValue: this.value,
          'onUpdate:modelValue': (v: string) => (this.value = v),
        })
      },
    })
    const wrapper = mount(Host)
    const items = wrapper.findAll('.ds-radio__root')
    await items[2].trigger('click')
    expect((wrapper.vm as unknown as { value: string }).value).toBe('a')
  })

  it('disables every option when group disabled prop is set', () => {
    const wrapper = mount(DsRadioGroup, { props: { options, disabled: true } })
    const items = wrapper.findAll('.ds-radio__root')
    items.forEach((i) => {
      expect(i.attributes('data-disabled')).toBe('')
    })
  })

  it('reflects orientation', () => {
    const horizontal = mount(DsRadioGroup, { props: { options, orientation: 'horizontal' } })
    const vertical = mount(DsRadioGroup, { props: { options, orientation: 'vertical' } })
    expect(horizontal.find('[data-test="ds-radio-group"]').classes()).toContain('cluster')
    expect(vertical.find('[data-test="ds-radio-group"]').classes()).toContain('stack')
  })
})
