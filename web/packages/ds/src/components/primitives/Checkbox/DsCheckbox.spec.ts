import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import DsCheckbox from './DsCheckbox.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
}

describe('DsCheckbox', () => {
  it('renders with the data-test hook and a label', () => {
    const wrapper = mount(DsCheckbox, { props: { label: 'Accept' } })
    expect(wrapper.find('[data-test="ds-checkbox"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Accept')
  })

  it('reflects checked state via data-state', async () => {
    const wrapper = mount(DsCheckbox, { props: { modelValue: true } })
    await flush()
    const root = wrapper.find('[data-test="ds-checkbox"]')
    expect(root.attributes('data-state')).toBe('checked')

    await wrapper.setProps({ modelValue: false })
    await flush()
    expect(root.attributes('data-state')).toBe('unchecked')
  })

  it('reflects indeterminate state', async () => {
    const wrapper = mount(DsCheckbox, { props: { modelValue: 'indeterminate' } })
    await flush()
    expect(wrapper.find('[data-test="ds-checkbox"]').attributes('data-state')).toBe('indeterminate')
  })

  it('emits update:modelValue when clicked', async () => {
    const Host = defineComponent({
      setup() {
        const checked = ref(false)
        return { checked }
      },
      render() {
        return h(DsCheckbox, {
          modelValue: this.checked,
          'onUpdate:modelValue': (v: boolean | 'indeterminate') => (this.checked = v as boolean),
        })
      },
    })
    const wrapper = mount(Host)
    await flush()
    await wrapper.find('[data-test="ds-checkbox"]').trigger('click')
    await flush()
    expect((wrapper.vm as unknown as { checked: boolean }).checked).toBe(true)
  })

  it('does not toggle when disabled', async () => {
    const Host = defineComponent({
      setup() {
        const checked = ref(false)
        return { checked }
      },
      render() {
        return h(DsCheckbox, {
          modelValue: this.checked,
          disabled: true,
          'onUpdate:modelValue': (v: boolean | 'indeterminate') => (this.checked = v as boolean),
        })
      },
    })
    const wrapper = mount(Host)
    await wrapper.find('[data-test="ds-checkbox"]').trigger('click')
    expect((wrapper.vm as unknown as { checked: boolean }).checked).toBe(false)
  })

  it('reflects size as data-size on the wrapper label', () => {
    const wrapper = mount(DsCheckbox, { props: { size: 'lg' } })
    expect(wrapper.element.getAttribute('data-size')).toBe('lg')
  })
})
