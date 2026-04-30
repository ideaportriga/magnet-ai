import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import KmDropdownSelect from './KmDropdownSelect.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

const openMenu = async () => {
  const trigger = document.body.querySelector('[data-test="km-dropdown-select-trigger"]') as HTMLButtonElement
  trigger.focus()
  trigger.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  await flush()
}

describe('KmDropdownSelect', () => {
  beforeEach(() => { document.body.innerHTML = '' })

  it('renders the selected label in the trigger', () => {
    const wrapper = mount(KmDropdownSelect, {
      props: {
        modelValue: 'variant_2',
        options: [
          { label: 'Variant 1', value: 'variant_1' },
          { label: 'Variant 2', value: 'variant_2' },
        ],
      },
    })

    expect(wrapper.find('[data-test="km-dropdown-select-trigger"]').text()).toContain('Variant 2')
  })

  it('marks the selected item and emits value plus option on select', async () => {
    const wrapper = mount(KmDropdownSelect, {
      props: {
        modelValue: 'variant_1',
        options: [
          { label: 'Variant 1', value: 'variant_1', badgeLabel: 'Active', badgeIcon: 'check' },
          { label: 'Variant 2', value: 'variant_2' },
        ],
      },
      attachTo: document.body,
    })

    await flush()
    await openMenu()

    const items = document.body.querySelectorAll('[data-test="ds-dropdown-menu-item"]')
    expect(items).toHaveLength(2)
    expect(items[0].getAttribute('data-selected')).toBe('true')
    expect(items[0].textContent).toContain('Active')

    ;(items[1] as HTMLElement).click()
    await flush()

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['variant_2'])
    expect(wrapper.emitted('select')?.[0]?.[0]).toBe('variant_2')
    expect(wrapper.emitted('select')?.[0]?.[1]).toMatchObject({ label: 'Variant 2', value: 'variant_2' })
  })

  it('applies custom test ids to the trigger and exposes validation', async () => {
    const wrapper = mount(KmDropdownSelect, {
      props: {
        modelValue: '',
        options: [{ label: 'Generic', value: 'generic' }],
        rules: [(value: unknown) => value ? true : 'Required'],
      },
      attrs: {
        'data-test': 'select-category',
      },
    })

    expect(wrapper.find('[data-test="select-category"]').exists()).toBe(true)
    expect((wrapper.vm as unknown as { validate: () => boolean }).validate()).toBe(false)
    await nextTick()
    expect(wrapper.text()).toContain('Required')

    await wrapper.setProps({ modelValue: 'generic' })
    expect((wrapper.vm as unknown as { validate: () => boolean }).validate()).toBe(true)
  })
})
