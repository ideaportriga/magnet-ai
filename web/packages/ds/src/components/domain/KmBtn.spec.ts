import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import KmBtn from './KmBtn.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
}

describe('KmBtn', () => {
  it('renders with the data-test hook and a label', () => {
    const wrapper = mount(KmBtn, { props: { label: 'Save' } })
    expect(wrapper.find('[data-test="km-btn"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Save')
  })

  it('maps `flat` legacy prop to DsButton variant="ghost"', () => {
    const wrapper = mount(KmBtn, { props: { label: 'Edit', flat: true } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-variant')).toBe('ghost')
  })

  it('maps `simple` legacy prop to DsButton variant="secondary"', () => {
    const wrapper = mount(KmBtn, { props: { label: 'Edit', simple: true } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-variant')).toBe('secondary')
  })

  it('maps `secondary` legacy prop to DsButton variant="secondary"', () => {
    const wrapper = mount(KmBtn, { props: { label: 'Edit', secondary: true } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-variant')).toBe('secondary')
  })

  it('maps `link` legacy prop to DsButton variant="link"', () => {
    const wrapper = mount(KmBtn, { props: { label: 'More', link: true } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-variant')).toBe('link')
  })

  it('explicit `variant` prop wins over legacy adjective props', () => {
    const wrapper = mount(KmBtn, { props: { label: 'X', flat: true, variant: 'primary' } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-variant')).toBe('primary')
  })

  it('uses icon-only sizing when only an icon is supplied', () => {
    const wrapper = mount(KmBtn, { props: { icon: 'add' } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-size')).toBe('icon')
  })

  it('supports explicit compact icon sizing', () => {
    const wrapper = mount(KmBtn, { props: { icon: 'send', size: 'icon-xs' } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-size')).toBe('icon-xs')
  })

  it('preserves caller data-test attrs', () => {
    const wrapper = mount(KmBtn, {
      props: { icon: 'send', size: 'icon-xs' },
      attrs: { 'data-test': 'preview-btn' },
    })

    expect(wrapper.find('[data-test="preview-btn"]').exists()).toBe(true)
  })

  it('maps `dense` to small size', () => {
    const wrapper = mount(KmBtn, { props: { label: 'X', dense: true } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-size')).toBe('sm')
  })

  it('forwards `justify` prop as `data-justify` attribute on the rendered button', () => {
    const wrapper = mount(KmBtn, { props: { label: 'X', justify: 'start' } })
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-justify')).toBe('start')
  })

  it('forwards `block` prop as a presence-only `data-block` attribute', () => {
    const wrapper = mount(KmBtn, { props: { label: 'X', block: true } })
    const btn = wrapper.find('[data-test="km-btn"]')
    expect(btn.attributes('data-block')).toBe('')
  })

  it('reflects `disable` as the native `disabled` attribute', () => {
    const wrapper = mount(KmBtn, { props: { label: 'X', disable: true } })
    const btn = wrapper.find('[data-test="km-btn"]').element as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    expect(wrapper.find('[data-test="km-btn"]').attributes('data-state')).toBe('disabled')
  })

  it('emits click events', async () => {
    const wrapper = mount(KmBtn, { props: { label: 'Hit' } })
    await wrapper.find('[data-test="km-btn"]').trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('does not emit click when disabled', async () => {
    const wrapper = mount(KmBtn, { props: { label: 'X', disable: true } })
    await wrapper.find('[data-test="km-btn"]').trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })

  it('renders default slot content over the props-driven children', () => {
    const wrapper = mount(KmBtn, {
      props: { label: 'ignored' },
      slots: { default: '<span class="custom">Custom</span>' },
    })
    expect(wrapper.find('.custom').exists()).toBe(true)
    expect(wrapper.text()).toContain('Custom')
    expect(wrapper.text()).not.toContain('ignored')
  })

  it('dropdown variant emits click-option when an item is selected', async () => {
    const Host = defineComponent({
      props: { selected: { type: Object, default: null } },
      emits: ['select'],
      render() {
        return h(KmBtn, {
          label: 'Actions',
          dropdown: true,
          options: [{ label: 'Edit' }, { label: 'Delete' }],
          'onClick-option': (opt: { label: string }) => this.$emit('select', opt),
        })
      },
    })
    const wrapper = mount(Host, { attachTo: document.body })
    await flush()
    const trigger = document.body.querySelector('[data-test="km-btn"]') as HTMLButtonElement
    trigger.focus()
    trigger.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
    await flush()
    const items = document.body.querySelectorAll('.km-btn__menu-item')
    expect(items.length).toBe(2)
    ;(items[0] as HTMLElement).click()
    await flush()
    const emitted = wrapper.emitted('select') as Array<Array<{ label: string }>> | undefined
    expect(emitted?.[0]?.[0]?.label).toBe('Edit')
  })
})
