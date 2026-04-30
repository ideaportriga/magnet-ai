import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import KmTabs from './KmTabs.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
}

const items = [
  { value: 'overview', label: 'Overview' },
  { value: 'details', label: 'Details' },
  { value: 'admin', label: 'Admin', disabled: true },
]

describe('KmTabs', () => {
  it('renders one trigger per item with the data-test hook', () => {
    const wrapper = mount(KmTabs, { props: { items, modelValue: 'overview' } })
    expect(wrapper.find('[data-test="km-tabs"]').exists()).toBe(true)
    const triggers = wrapper.findAll('[data-test="ds-tabs-trigger"]')
    expect(triggers).toHaveLength(3)
    expect(triggers.map((t) => t.text())).toEqual(['Overview', 'Details', 'Admin'])
  })

  it('marks the active trigger with data-state="active"', async () => {
    const wrapper = mount(KmTabs, { props: { items, modelValue: 'details' } })
    await flush()
    const triggers = wrapper.findAll('[data-test="ds-tabs-trigger"]')
    expect(triggers[0].attributes('data-state')).toBe('inactive')
    expect(triggers[1].attributes('data-state')).toBe('active')
  })

  it('emits update:modelValue when a different tab is clicked', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('overview')
        return { value }
      },
      render() {
        return h(KmTabs, {
          items,
          modelValue: this.value,
          'onUpdate:modelValue': (v: string) => (this.value = v),
        })
      },
    })
    const wrapper = mount(Host)
    await flush()
    const triggers = wrapper.findAll('[data-test="ds-tabs-trigger"]')
    await triggers[1].trigger('mousedown')
    await triggers[1].trigger('click')
    await flush()
    expect((wrapper.vm as unknown as { value: string }).value).toBe('details')
  })

  it('does not activate disabled tabs on click', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('overview')
        return { value }
      },
      render() {
        return h(KmTabs, {
          items,
          modelValue: this.value,
          'onUpdate:modelValue': (v: string) => (this.value = v),
        })
      },
    })
    const wrapper = mount(Host)
    await flush()
    const triggers = wrapper.findAll('[data-test="ds-tabs-trigger"]')
    await triggers[2].trigger('click')
    await flush()
    expect((wrapper.vm as unknown as { value: string }).value).toBe('overview')
  })
})
