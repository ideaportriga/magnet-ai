import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DsLabel from './DsLabel.vue'

describe('DsLabel', () => {
  it('renders a <label> with the data-test hook', () => {
    const wrapper = mount(DsLabel, { slots: { default: 'Email' } })
    expect(wrapper.element.tagName).toBe('LABEL')
    expect(wrapper.attributes('data-test')).toBe('ds-label')
    expect(wrapper.text()).toBe('Email')
  })

  it('forwards `for` so clicking focuses the associated control', () => {
    const wrapper = mount(DsLabel, {
      props: { for: 'email' },
      slots: { default: 'Email' },
    })
    expect(wrapper.attributes('for')).toBe('email')
  })

  it('exposes the ds-label class for styling hooks', () => {
    const wrapper = mount(DsLabel, { slots: { default: 'X' } })
    expect(wrapper.classes()).toContain('ds-label')
  })
})
