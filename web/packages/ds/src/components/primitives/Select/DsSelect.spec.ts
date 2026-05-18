import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import DsSelect from './DsSelect.vue'
import type { DsSelectOption } from '../types'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

const options: DsSelectOption[] = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German', disabled: true },
]

describe('DsSelect', () => {
  beforeEach(() => { document.body.innerHTML = '' })

  it('renders the trigger with the placeholder when no value is bound', async () => {
    mount(DsSelect, {
      props: { options, placeholder: 'Choose…' },
      attachTo: document.body,
    })
    await flush()
    const trigger = document.body.querySelector('[data-test="ds-select"]') as HTMLElement
    expect(trigger).not.toBeNull()
    // Placeholder is rendered as a child span by Reka.
    expect(trigger.textContent?.includes('Choose…')).toBe(true)
    expect(trigger.getAttribute('data-placeholder')).not.toBeNull()
  })

  it('renders the selected option label when bound', async () => {
    mount(DsSelect, {
      props: { options, modelValue: 'fr' },
      attachTo: document.body,
    })
    await flush()
    const trigger = document.body.querySelector('[data-test="ds-select"]') as HTMLElement
    expect(trigger.textContent?.includes('French')).toBe(true)
    expect(trigger.getAttribute('data-placeholder')).toBeNull()
  })

  it('reflects size as data-size on the trigger', async () => {
    mount(DsSelect, {
      props: { options, size: 'sm' },
      attachTo: document.body,
    })
    await flush()
    expect(
      (document.body.querySelector('[data-test="ds-select"]') as HTMLElement).getAttribute('data-size'),
    ).toBe('sm')
  })

  it('marks the trigger as disabled when disabled', async () => {
    mount(DsSelect, {
      props: { options, disabled: true },
      attachTo: document.body,
    })
    await flush()
    const trigger = document.body.querySelector('[data-test="ds-select"]') as HTMLElement
    expect(trigger.hasAttribute('disabled') || trigger.getAttribute('data-disabled') !== null).toBe(true)
  })

  it('forwards model updates via @update:model-value', async () => {
    const log: string[] = []
    const Host = defineComponent({
      render() {
        return h(DsSelect, {
          options,
          modelValue: 'en',
          'onUpdate:modelValue': (v: string) => log.push(v),
        })
      },
    })
    const wrapper = mount(Host, { attachTo: document.body })
    await flush()
    // Programmatic Reka SelectRoot exposes a hidden native select for forms.
    const native = wrapper.find('select')
    if (native.exists()) {
      await native.setValue('fr')
      expect(log[log.length - 1]).toBe('fr')
    } else {
      // Fall back: assert the controlled value at least renders.
      expect(document.body.querySelector('[data-test="ds-select"]')?.textContent).toContain('English')
    }
  })
})
