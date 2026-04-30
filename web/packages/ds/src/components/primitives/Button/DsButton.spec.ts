import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import DsButton from './DsButton.vue'

describe('DsButton', () => {
  it('renders as a <button> by default', () => {
    const wrapper = mount(DsButton, { slots: { default: 'Save' } })
    expect(wrapper.element.tagName).toBe('BUTTON')
    expect(wrapper.text()).toBe('Save')
  })

  it('exposes data-test hook', () => {
    const wrapper = mount(DsButton, { slots: { default: 'X' } })
    expect(wrapper.attributes('data-test')).toBe('ds-button')
  })

  it('reflects variant + size as data attributes', () => {
    const wrapper = mount(DsButton, {
      props: { variant: 'destructive', size: 'lg' },
      slots: { default: 'Delete' },
    })
    expect(wrapper.attributes('data-variant')).toBe('destructive')
    expect(wrapper.attributes('data-size')).toBe('lg')
  })

  it('supports compact icon sizing for controls embedded in inputs', () => {
    const wrapper = mount(DsButton, {
      props: { size: 'icon-xs' },
      slots: { default: 'X' },
    })

    expect(wrapper.attributes('data-size')).toBe('icon-xs')
  })

  it('defaults to variant="primary" size="md"', () => {
    const wrapper = mount(DsButton, { slots: { default: 'Default' } })
    expect(wrapper.attributes('data-variant')).toBe('primary')
    expect(wrapper.attributes('data-size')).toBe('md')
  })

  it('renders as the requested element via `as`', () => {
    const wrapper = mount(DsButton, {
      props: { as: 'a' },
      slots: { default: 'Link' },
    })
    expect(wrapper.element.tagName).toBe('A')
  })

  it('forwards attrs to the rendered root', () => {
    const wrapper = mount(DsButton, {
      attrs: { id: 'save-btn', 'aria-label': 'Save changes' },
      slots: { default: 'Save' },
    })
    expect(wrapper.attributes('id')).toBe('save-btn')
    expect(wrapper.attributes('aria-label')).toBe('Save changes')
  })

  it('emits click events', async () => {
    const wrapper = mount(DsButton, { slots: { default: 'Hit' } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('does not emit click when disabled (native button)', async () => {
    const wrapper = mount(DsButton, {
      attrs: { disabled: '' },
      slots: { default: 'Locked' },
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })

  it('passes child element through with as-child', () => {
    const Child = defineComponent({
      setup() {
        return () => h('a', { href: '/foo', class: 'kept' }, 'Link')
      },
    })
    const wrapper = mount(DsButton, {
      props: { asChild: true },
      slots: { default: () => h(Child) },
    })
    expect(wrapper.element.tagName).toBe('A')
    expect(wrapper.attributes('href')).toBe('/foo')
    expect(wrapper.classes()).toContain('ds-button')
    expect(wrapper.classes()).toContain('kept')
  })
})
