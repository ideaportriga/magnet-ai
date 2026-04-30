import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import KmChip from './KmChip.vue'

describe('KmChip', () => {
  it('renders icons with the chip text color by default', () => {
    const wrapper = mount(KmChip, {
      props: {
        tone: 'brand',
        icon: 'magic',
        label: '3 Topics',
      },
    })

    const chip = wrapper.find('[data-test="km-chip"]')
    const icon = wrapper.find('[data-test="km-glyph"]')

    expect(chip.attributes('data-tone')).toBe('brand')
    expect(icon.attributes('data-tone')).toBe('current')
  })

  it('preserves explicit iconColor overrides', () => {
    const wrapper = mount(KmChip, {
      props: {
        tone: 'brand',
        icon: 'magic',
        iconColor: 'danger',
        label: '3 Topics',
      },
    })

    const icon = wrapper.find('[data-test="km-glyph"]')

    expect(icon.attributes('data-tone')).toBe('default')
    expect(icon.attributes('style')).toContain('--km-glyph-fallback-color')
  })
})