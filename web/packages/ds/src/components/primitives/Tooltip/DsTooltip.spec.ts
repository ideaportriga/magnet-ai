import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import DsTooltip from './DsTooltip.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

describe('DsTooltip', () => {
  beforeEach(() => { document.body.innerHTML = '' })

  it('renders the trigger but no tooltip when not focused/hovered', async () => {
    mount(DsTooltip, {
      props: { text: 'Save' },
      slots: { trigger: () => h('button', { id: 'btn' }, 'Save') },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('#btn')).not.toBeNull()
    expect(document.body.querySelector('[data-test="ds-tooltip"]')).toBeNull()
  })

  it('shows tooltip content on focus', async () => {
    mount(DsTooltip, {
      props: { text: 'Save', delay: 0 },
      slots: { trigger: () => h('button', { id: 'btn' }, 'Save') },
      attachTo: document.body,
    })
    await flush()
    const trigger = document.body.querySelector('#btn') as HTMLButtonElement
    trigger.focus()
    await flush()
    const content = document.body.querySelector('[data-test="ds-tooltip"]')
    expect(content).not.toBeNull()
    expect(content?.textContent?.includes('Save')).toBe(true)
  })

  it('honours the disabled prop', async () => {
    mount(DsTooltip, {
      props: { text: 'Save', delay: 0, disabled: true },
      slots: { trigger: () => h('button', { id: 'btn' }, 'Save') },
      attachTo: document.body,
    })
    await flush()
    ;(document.body.querySelector('#btn') as HTMLButtonElement).focus()
    await flush()
    expect(document.body.querySelector('[data-test="ds-tooltip"]')).toBeNull()
  })

  it('renders rich content when default slot is supplied with named trigger', async () => {
    const Host = defineComponent({
      render() {
        return h(DsTooltip, { delay: 0 }, {
          trigger: () => h('button', { id: 'btn' }, 'Save'),
          default: () => h('strong', 'rich content'),
        })
      },
    })
    mount(Host, { attachTo: document.body })
    await flush()
    ;(document.body.querySelector('#btn') as HTMLButtonElement).focus()
    await flush()
    const content = document.body.querySelector('[data-test="ds-tooltip"]')
    expect(content?.querySelector('strong')?.textContent).toBe('rich content')
  })
})
