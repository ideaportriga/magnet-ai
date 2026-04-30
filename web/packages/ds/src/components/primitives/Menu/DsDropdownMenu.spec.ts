import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import DsDropdownMenu, { type DsDropdownMenuItem } from './DsDropdownMenu.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

const Host = defineComponent({
  props: { items: { type: Array as () => DsDropdownMenuItem[], required: true } },
  render() {
    return h(DsDropdownMenu, { items: this.items as DsDropdownMenuItem[] }, {
      trigger: () => h('button', { id: 'trigger', 'data-test': 'trigger' }, 'Open'),
    })
  },
})

const openMenu = async () => {
  const trigger = document.body.querySelector('#trigger') as HTMLButtonElement
  // Reka uses keydown/Enter to open via keyboard.
  trigger.focus()
  trigger.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  await flush()
}

describe('DsDropdownMenu', () => {
  beforeEach(() => { document.body.innerHTML = '' })

  it('does not render menu items until opened', async () => {
    mount(Host, {
      props: { items: [{ label: 'Edit' }, { label: 'Delete' }] },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="ds-menu"]')).toBeNull()
  })

  it('renders items when the menu is opened', async () => {
    const items: DsDropdownMenuItem[] = [
      { label: 'Edit' },
      { separator: true },
      { label: 'Delete', tone: 'danger' },
    ]
    mount(Host, { props: { items }, attachTo: document.body })
    await flush()
    await openMenu()
    const menu = document.body.querySelector('[data-test="ds-menu"]')
    expect(menu).not.toBeNull()
    const itemEls = document.body.querySelectorAll('[data-test="ds-menu-item"]')
    expect(itemEls.length).toBe(2)
    expect(itemEls[1].getAttribute('data-tone')).toBe('danger')
    expect(document.body.querySelector('.ds-menu__separator')).not.toBeNull()
  })

  it('invokes onSelect with the item that was activated', async () => {
    const onSelect = vi.fn()
    const items: DsDropdownMenuItem[] = [
      { label: 'Edit', onSelect },
      { label: 'Delete' },
    ]
    mount(Host, { props: { items }, attachTo: document.body })
    await flush()
    await openMenu()
    const itemEls = document.body.querySelectorAll('[data-test="ds-menu-item"]')
    ;(itemEls[0] as HTMLElement).click()
    await flush()
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect.mock.calls[0][0].label).toBe('Edit')
  })

  it('disabled items do not trigger onSelect', async () => {
    const onSelect = vi.fn()
    const items: DsDropdownMenuItem[] = [
      { label: 'Edit', onSelect, disabled: true },
    ]
    mount(Host, { props: { items }, attachTo: document.body })
    await flush()
    await openMenu()
    const item = document.body.querySelector('[data-test="ds-menu-item"]') as HTMLElement
    item.click()
    await flush()
    expect(onSelect).not.toHaveBeenCalled()
  })
})
