import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import DsSwitch from './DsSwitch.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
}

describe('DsSwitch', () => {
  it('renders with the data-test hook and a label', () => {
    const wrapper = mount(DsSwitch, { props: { label: 'Notifications' } })
    expect(wrapper.find('[data-test="ds-switch"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Notifications')
  })

  it('reflects checked state via data-state', async () => {
    const wrapper = mount(DsSwitch, { props: { modelValue: true } })
    await flush()
    const root = wrapper.find('[data-test="ds-switch"]')
    expect(root.attributes('data-state')).toBe('checked')

    await wrapper.setProps({ modelValue: false })
    await flush()
    expect(root.attributes('data-state')).toBe('unchecked')
  })

  it('emits update:modelValue when clicked', async () => {
    const Host = defineComponent({
      setup() {
        const enabled = ref(false)
        return { enabled }
      },
      render() {
        return h(DsSwitch, {
          modelValue: this.enabled,
          'onUpdate:modelValue': (v: boolean) => (this.enabled = v),
        })
      },
    })
    const wrapper = mount(Host)
    await flush()
    await wrapper.find('[data-test="ds-switch"]').trigger('click')
    await flush()
    expect((wrapper.vm as unknown as { enabled: boolean }).enabled).toBe(true)
  })

  it('does not toggle when disabled', async () => {
    const Host = defineComponent({
      setup() {
        const enabled = ref(false)
        return { enabled }
      },
      render() {
        return h(DsSwitch, {
          modelValue: this.enabled,
          disabled: true,
          'onUpdate:modelValue': (v: boolean) => (this.enabled = v),
        })
      },
    })
    const wrapper = mount(Host)
    await wrapper.find('[data-test="ds-switch"]').trigger('click')
    expect((wrapper.vm as unknown as { enabled: boolean }).enabled).toBe(false)
  })

  it('reflects size as data-size on the wrapper label', () => {
    expect(mount(DsSwitch, { props: { size: 'sm' } }).element.getAttribute('data-size')).toBe('sm')
    expect(mount(DsSwitch, { props: { size: 'lg' } }).element.getAttribute('data-size')).toBe('lg')
  })

  it('marks the wrapper with data-disabled', () => {
    const wrapper = mount(DsSwitch, { props: { disabled: true } })
    expect(wrapper.element.getAttribute('data-disabled')).toBe('true')
  })
})
